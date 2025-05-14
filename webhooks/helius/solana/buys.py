import os
import json
import requests
from dotenv import load_dotenv
from telegram import Bot
from flask import Flask, request
from telegram.ext import Updater

load_dotenv()

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

helius_url = "https://api.helius.xyz/v0/transactions"
headers = {
    "Authorization": f"Bearer {HELIUS_API_KEY}",
    "Content-Type": "application/json"
}

middleware_bot = Bot(token=MIDDLEWARE_BOT_TOKEN)

# Flask app for the webhook server
app = Flask(__name__)

def parse_transaction_data(data):
    try:
        if 'token' in data and data['token'] == 'SOL' and data['amount'] >= 500:
            return {
                'amount': data['amount'],
                'solana_account': data['account'],
                'transaction_link': data['transaction_link'],
            }
        return None
    except KeyError as e:
        print(f"Error parsing transaction data: {e}")
        return None

def pass_message_to_bot(transaction_data):
    message = f"New Solana purchase detected!\n" \
              f"Amount: {transaction_data['amount']} SOL\n" \
              f"Account: {transaction_data['solana_account']}\n" \
              f"Transaction: {transaction_data['transaction_link']}"

    try:
        middleware_bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message
        )
        print(f"Message sent to Telegram group: {message}")
    except Exception as e:
        print(f"Failed to send message to Telegram group: {e}")

# Webhook route to receive Helius transaction data
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json  # Assuming the Helius API sends a JSON payload
    print(f"Received webhook data: {data}")
    
    # Parse and process the transaction data
    transaction_data = parse_transaction_data(data)
    
    if transaction_data:
        pass_message_to_bot(transaction_data)
        return "OK", 200
    else:
        return "No valid transaction data", 400

if __name__ == '__main__':
    # Start Flask server
    app.run(debug=True, host='0.0.0.0', port=5000)