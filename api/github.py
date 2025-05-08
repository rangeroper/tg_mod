import os
import json
import aiohttp

async def get_github_stats():
    """Fetches GitHub repository statistics (stars, forks, and current release version)."""
    previous_stats = load_previous_github_stats()  # Get previous stats

    # GitHub API call to fetch the current stats
    repo = os.getenv("GITHUB_REPO")
    url = f"https://api.github.com/repos/{repo}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                # Get the required stats: stars, forks, and latest release version
                stars = data.get("stargazers_count", 0)
                forks = data.get("forks_count", 0)

                # Get the latest release version (now async)
                release_version = await get_current_release_version(session, repo)

                # Format stats into a dictionary
                current_stats = {
                    "stars": stars,
                    "forks": forks,
                    "release_version": release_version
                }

                # Calculate increases and percentage changes for stars and forks (release version is not numeric)
                stats = {}
                for key in current_stats:
                    current_value = current_stats[key]
                    previous_value = previous_stats.get(key, 0)

                    # Only calculate percentage changes for numeric values
                    if key != "release_version":
                        # Ensure current_value is an integer for stars and forks
                        current_value = int(current_value) if isinstance(current_value, str) else current_value
                        previous_value = int(previous_value) if isinstance(previous_value, str) else previous_value

                        # Calculate increases and percentage changes
                        if previous_value == 0:
                            increase = current_value
                            percent_change = 100 if current_value > 0 else 0
                        else:
                            increase = current_value - previous_value
                            percent_change = (increase / previous_value * 100) if previous_value else 0
                    else:
                        increase = "N/A"
                        percent_change = "N/A"

                    stats[key] = {
                        'current': current_value if key != "release_version" else release_version,
                        'increase': increase,
                        'percent_change': percent_change
                    }

                # Save current stats to file for future comparisons
                save_current_github_stats(current_stats)

                # Format the stats into a message with commas for stars and forks
                formatted_stars = "{:,}".format(stats['stars']['current'])
                formatted_forks = "{:,}".format(stats['forks']['current'])

                # Correct the message formatting
                message = f"⭐️ Github Stars  >>  {formatted_stars} ({stats['stars']['percent_change']:.2f}%)\n"
                message += f"🍴 Github Forks  >>  {formatted_forks} ({stats['forks']['percent_change']:.2f}%)\n"
                message += f"🔖 Rig Version  >>  {stats['release_version']['current']}"

                return message
            else:
                return "❌ Error fetching GitHub stats."

async def get_current_release_version(session, repo):
    """Fetches the latest release version from the repository asynchronously."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("tag_name", "N/A")  # Default to 'N/A' if no release exists
    return "N/A"  

def load_previous_github_stats():
    """Loads previous GitHub stats from file or fetches current stats if the file is missing."""
    if os.path.exists("data/github_metrics.json"):
        with open("data/github_metrics.json", "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}  # Return empty dict if the file is invalid
    else:
        return {}  # If the file does not exist, return empty dict

def save_current_github_stats(stats):
    """Saves the current GitHub stats to file."""
    with open("data/github_metrics.json", "w") as f:
        json.dump(stats, f)