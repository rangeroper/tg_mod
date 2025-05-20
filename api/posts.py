import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urlparse

X_PROFILES = [
    "https://x.com/arcdotfun",
    "https://x.com/0thTachi",
    "https://x.com/Kezo_Futura"
]

def format_timestamp(iso_ts):
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return dt.strftime("%m/%d/%Y %I:%M %p")
    except Exception:
        return "Unknown time"

def extract_username(url):
    parsed = urlparse(url)
    return parsed.path.strip("/").split("/")[0]

async def get_latest_post_from_profile(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url)
            await page.wait_for_selector("[data-testid='cellInnerDiv']")

            posts = await page.query_selector_all("[data-testid='cellInnerDiv']")

            for post in posts:
                pinned_label = await post.query_selector("span:has-text('Pinned')")
                if pinned_label:
                    continue

                time_element = await post.query_selector("time")
                timestamp = await time_element.get_attribute("datetime") if time_element else "Unknown time"

                link_element = await post.query_selector("a[href*='/status/']")
                relative_link = await link_element.get_attribute("href") if link_element else None
                full_link = f"https://x.com{relative_link}" if relative_link else "Link not found"

                await browser.close()

                return {
                    "username": extract_username(url),
                    "url": full_link,
                    "timestamp": timestamp
                }

            await browser.close()
            return None

    except Exception as e:
        print(f"Error fetching post from {url}: {e}")
        return None

async def get_all_latest_posts():
    results = []
    for profile in X_PROFILES:
        post = await get_latest_post_from_profile(profile)
        if post:
            results.append(post)
    return results

async def build_latest_posts_message():
    posts = await get_all_latest_posts()
    if not posts:
        return "⚠️ No posts found."

    message_lines = ["🧵 **Latest Posts:**"]
    for post in posts:
        formatted_time = format_timestamp(post['timestamp'])
        username = post['username']
        preview = (
            f"**{username}**  \n"
            f"🕒 {formatted_time}  \n"
            f"[View Post]({post['url']})"
        )
        message_lines.append(preview)

    return "\n\n---\n\n".join(message_lines)

async def main():
    message = await build_latest_posts_message()
    data = {
        "latest_posts_message": message
    }
    try:
        path = Path("filters/posts.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Successfully updated filters/posts.json")
    except Exception as e:
        print(f"Error writing posts.json: {e}")

if __name__ == "__main__":
    asyncio.run(main())
