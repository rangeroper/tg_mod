import json
import os
import aiohttp

# Fetch system environment variables
TOKEN_MINT_ADDRESS = os.getenv("TOKEN_ADDRESS")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

async def get_token_holders():
    """Fetches the total token holder count using Helius getTokenAccounts API asynchronously."""
    
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    
    payload = {
        "jsonrpc": "2.0",
        "id": "get-holders",
        "method": "getTokenAccounts",
        "params": {
            "mint": TOKEN_MINT_ADDRESS,
            "limit": 1000,
            "options": {
                "showZeroBalance": False
            }
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    unique_holders = set()
    has_more = True
    cursor = None

    async with aiohttp.ClientSession() as session:
        while has_more:
            if cursor:
                payload["params"]["cursor"] = cursor
            
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "error" in data:
                        print(f"API Error: {data['error']['message']}")
                        return 0
                        
                    if "result" in data and "token_accounts" in data["result"]:
                        accounts = data["result"]["token_accounts"]
                        
                        for account in accounts:
                            if "owner" in account:
                                unique_holders.add(account["owner"])
                        
                        if "cursor" in data["result"] and data["result"]["cursor"]:
                            cursor = data["result"]["cursor"]
                        else:
                            has_more = False
                    else:
                        has_more = False
                else:
                    print(f"Error fetching data: {response.status}")
                    has_more = False
    
    holder_count = len(unique_holders)
    return holder_count

def load_previous_token_stats():
    """Loads previous token holder count from file or returns 0 if not available."""
    if os.path.exists("data/token_holders.json"):
        with open("data/token_holders.json", "r") as f:
            try:
                data = json.load(f)
                return data.get("holders", {}).get("current", 0)
            except json.JSONDecodeError:
                return 0
    else:
        return 0

def save_current_token_stats(current_count):
    """Saves the current token holder count to file."""
    os.makedirs("data", exist_ok=True)
    stats = {"holders": {"current": current_count}}
    with open("data/token_holders.json", "w") as f:
        json.dump(stats, f)

async def get_token_stats():
    """Fetches token stats asynchronously and returns a formatted message."""
    previous_count = load_previous_token_stats()
    current_count = await get_token_holders()  
    
    if previous_count == 0:
        increase = current_count
        percent_change = 100 if current_count > 0 else 0
    else:
        increase = current_count - previous_count
        percent_change = (increase / previous_count * 100) if previous_count else 0
    
    save_current_token_stats(current_count)
    
    formatted_count = "{:,}".format(current_count)
    
    message = f"💊 $ARC Holders  >>  {formatted_count} ({percent_change:.2f}%)"
    return message
