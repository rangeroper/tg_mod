import os
import json
import asyncio
from playwright.async_api import async_playwright

# File path to store follower data
X_METRICS_FILE = "data/x_metrics.json"

async def scrape_x_profile(url: str) -> dict:
    """Scrape an X.com profile to get user data."""
    xhr_calls = []

    def intercept_response(response):
        if response.request.resource_type == "xhr":
            xhr_calls.append(response)
        return response

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        page.on("response", intercept_response)
        await page.goto(url)
        await page.wait_for_selector("[data-testid='primaryColumn']")
        
        await page.wait_for_timeout(3000)

        # Extract user metrics
        tweet_calls = [f for f in xhr_calls if "UserBy" in f.url]
        for xhr in tweet_calls:
            data = await xhr.json()
            return data['data']['user']['result']
    
    return None

def load_previous_followers():
    """Loads the previous follower count from a file."""
    if os.path.exists(X_METRICS_FILE):
        with open(X_METRICS_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("followers", 0)
            except json.JSONDecodeError:
                return 0
    return 0

def save_followers_count(count):
    """Saves the current follower count to a file."""
    os.makedirs("data", exist_ok=True)
    stats = {"followers": {"current": count}}
    with open(X_METRICS_FILE, "w") as f:
        json.dump(stats, f)

async def get_x_followers_stats():
    """Fetches current followers, calculates the increase, and formats the message."""
    previous_count = load_previous_followers()
    profile = await scrape_x_profile("https://x.com/arcdotfun")
    
    if profile and 'legacy' in profile and 'followers_count' in profile['legacy']:
        current_count = profile['legacy']['followers_count']
    else:
        current_count = 0

    # Calculate increase and percentage change
    increase = current_count - previous_count
    percent_change = (increase / previous_count * 100) if previous_count else (100 if current_count > 0 else 0)

    # Save the new count
    save_followers_count(current_count)

    # Format count with commas
    formatted_count = "{:,}".format(current_count)

    # Generate formatted message
    message = f"🐦 X Followers  >>  {formatted_count} ({percent_change:.2f}%)"
    
    return message

def fetch_x_followers():
    """Runs the async function and returns the formatted message."""
    return asyncio.get_event_loop().run_until_complete(get_x_followers_stats())

if __name__ == "__main__":
    # Fetch and print X followers count
    print(fetch_x_followers())