import os
import json
import aiohttp
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

GITHUB_METRICS_FILE = "data/github_metrics.json"

def get_github_stats():
    """Fetches GitHub repository statistics and appends to metrics file."""
    repo = os.getenv("GITHUB_REPO")
    if not repo:
        return "❌ GITHUB_REPO not set in environment."

    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)

    if response.status_code != 200:
        return "❌ Error fetching GitHub stats."

    data = response.json()
    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)
    release_version = get_current_release_version(repo)

    # Build entry
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "stars": stars,
        "forks": forks,
        "release_version": release_version
    }

    save_github_metrics(entry)

    return (
        f"⭐️ Github Stars  >>  {stars:,}\n"
        f"🍴 Github Forks  >>  {forks:,}\n"
        f"🔖 Rig Version  >>  {release_version}"
    )

def get_current_release_version(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("tag_name", "N/A")
    return "N/A"

def save_github_metrics(new_entry):
    """Appends the new GitHub stats entry to the metrics file."""
    if os.path.exists(GITHUB_METRICS_FILE):
        with open(GITHUB_METRICS_FILE, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    if not existing_data:
        existing_data = {
            "dataset_name": "github_metrics",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": []
        }

    existing_data["entries"].append(new_entry)

    with open(GITHUB_METRICS_FILE, "w") as f:
        json.dump(existing_data, f, indent=2)