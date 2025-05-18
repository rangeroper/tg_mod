import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEEKLY_DIR = PROJECT_ROOT / "data" / "metrics" / "weekly"
FILTERS_DIR = PROJECT_ROOT / "filters"
FILTERS_DIR.mkdir(parents=True, exist_ok=True)

EMOJI_MAP = {
    "github_weekly_metrics_stars": "⭐️ GitHub Stars",
    "github_weekly_metrics_forks": "🍴 GitHub Forks",
    "telegram_weekly_metrics_member_count": "👥 Telegram Members",
    "token_holder_weekly_metrics_holder_count": "💊 $ARC Holders",
    "x_follower_weekly_metrics_followers": "🐦 X Followers",
}

def load_weekly_metrics_files():
    results = {}
    for file_path in WEEKLY_DIR.glob("*_weekly_metrics.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Use filename stem as dataset name, matches your naming scheme
                results[file_path.stem] = data
        except Exception as e:
            print(f"[!] Failed to load {file_path.name}: {e}")
    return results

def format_metrics_message(metrics_data):
    lines = []

    dataset_keys = {
        "github_weekly_metrics": ["stars", "forks"],
        "telegram_weekly_metrics": ["member_count"],
        "token_holder_weekly_metrics": ["holder_count"],
        "x_follower_weekly_metrics": ["followers"],
    }

    for dataset_name, keys_to_show in dataset_keys.items():
        data = metrics_data.get(dataset_name)
        if not data:
            continue

        current = data.get("current", {})
        change = data.get("change", {})
        if not current:
            continue

        for key in keys_to_show:
            if key not in current:
                continue
            value = current[key]
            pct_change = change.get(key)
            if not isinstance(value, (int, float)):
                continue
            if not isinstance(pct_change, (int, float)):
                pct_change = None

            label_key = f"{dataset_name}_{key}"
            label = EMOJI_MAP.get(label_key, f"{dataset_name.replace('_', ' ').title()} {key.title()}")

            value_str = f"{value:,}"
            change_str = f" ({pct_change:+.2f}%)" if pct_change is not None else ""
            lines.append(f"{label} >> {value_str}{change_str}")

        lines.append("")  # Line break between groups

    return "\n".join(lines).strip() + "\n"

def save_last_weekly_metrics_message(message):
    data = {"last_weekly_metrics_message": message}
    metrics_path = FILTERS_DIR / "growth.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[✓] Saved last weekly metrics message to {metrics_path}")

def main():
    metrics_data = load_weekly_metrics_files()
    if not metrics_data:
        print("[!] No weekly metrics data found.")
        return

    message = format_metrics_message(metrics_data)
    save_last_weekly_metrics_message(message)

if __name__ == "__main__":
    main()
