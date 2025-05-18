import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEEKLY_DIR = PROJECT_ROOT / "data" / "metrics" / "weekly"
FILTERS_DIR = PROJECT_ROOT / "filters"
FILTERS_DIR.mkdir(parents=True, exist_ok=True)

EMOJI_MAP = {
    "github_metrics_weekly_metrics": "⭐️ Github Stars",
    "github_forks": "🍴 Github Forks",
    "telegram_metrics_weekly_metrics": "👥 Telegram Members",
    "token_holders_weekly_metrics": "💊 $ARC Holders",
    "x_metrics_weekly_metrics": "🐦 X Followers",
}

def load_weekly_metrics_files():
    # Load all weekly metrics JSON files from WEEKLY_DIR
    results = {}
    for file_path in WEEKLY_DIR.glob("*_weekly_metrics.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                results[file_path.stem] = data
        except Exception as e:
            print(f"[!] Failed to load {file_path.name}: {e}")
    return results

def format_metrics_message(metrics_data):
    lines = []

    dataset_keys = {
        "github_metrics_weekly_metrics": ["stars", "forks"],
        "telegram_metrics_weekly_metrics": ["members"],
        "token_holders_weekly_metrics": ["holders"],
        "x_metrics_weekly_metrics": ["followers"],
    }

    for dataset_name, data in metrics_data.items():
        current = data.get("current", {})
        change = data.get("change", {})
        if not current:
            continue

        label = EMOJI_MAP.get(
            dataset_name,
            dataset_name.replace("_weekly_metrics", "").replace("_", " ").title()
        )

        keys_to_show = dataset_keys.get(dataset_name, list(current.keys()))
        for key in keys_to_show:
            if key not in current:
                continue
            value = current[key]
            pct_change = change.get(key)
            if not isinstance(value, (int, float)):
                continue
            if not isinstance(pct_change, (int, float)):
                pct_change = None

            value_str = f"{value:,}"

            change_str = f" ({pct_change:+.2f}%)" if pct_change is not None else ""
            line = f"{label} {key.title()} >> {value_str}{change_str}"
            lines.append(line)

    return "\n".join(lines) + "\n" 

def save_last_weekly_metrics_message(message):
    data = {"last_weekly_metrics_message": message}
    metrics_path = FILTERS_DIR / "last_weekly_metrics_message.json"
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
