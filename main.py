import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import os
import threading
import time
from flask import Flask

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
STORE_URL = "https://store.hylexmc.net"   # Website to scrape

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ====== SELF PINGER ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_ping_server():
    app.run(host="0.0.0.0", port=10000)

def self_pinger():
    while True:
        try:
            print("Self-pinging...")
            requests.get("https://tracker-ii23.onrender.com")
        except:
            pass
        time.sleep(240)  # every 4 minutes


# ====== PURCHASE TRACKING ======

last_seen = set()

def scrape_purchases():
    """
    Scrapes the recent purchase items from the store.
    Returns a list of purchase strings like:
    ["Tharun bought VIP", "Alex bought 13000 Tokens"]
    """

    try:
        html = requests.get(STORE_URL, timeout=10).text
    except Exception as e:
        print("Scrape error:", e)
        return []

    soup = BeautifulSoup(html, "html.parser")

    # FIND ITEMS — This selector works on Tebex stores
    purchase_elements = soup.select(".recentpurchase, .ui-item, .purchase, .col-md-12")

    results = []

    for p in purchase_elements:
        text = p.get_text(strip=True)
        if text and len(text) > 2:
            results.append(text)

    return results


def log_to_file(text):
    with open("purchases.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")


@tasks.loop(seconds=20)
async def check_purchases():
    global last_seen
    new_purchases = scrape_purchases()

    if not new_purchases:
        return

    for item in new_purchases:
        if item not in last_seen:
            last_seen.add(item)

            channel = client.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(f"🛒 **New Store Purchase**\n{item}")

            log_to_file(item)
            print("Logged:", item)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    check_purchases.start()


# ====== START EVERYTHING ======

if __name__ == "__main__":
    # run webserver (for Render keep-alive)
    threading.Thread(target=run_ping_server).start()

    # run pinger thread
    threading.Thread(target=self_pinger).start()

    # start discord bot
    client.run(TOKEN)
