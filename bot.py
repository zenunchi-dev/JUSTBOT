import discord
from discord.ext import tasks, commands
import requests
import os
from flask import Flask
from threading import Thread

# --- CONFIGURARE ---
TOKEN = os.getenv("DISCORD_TOKEN")
# Am pus ID-ul trimis de tine direct aici
CHANNEL_ID = 1479886164180729867 
PORT = int(os.getenv("PORT", 8080))

# Dicționar pentru emoji-uri și nume (Modelul cerut)
FRUITS_DATA = {
    "Kitsune": {"emoji": "🦊", "price": "8,000,000"},
    "Dragon": {"emoji": "🐉", "price": "3,500,000"},
    "Control": {"emoji": "🎮", "price": "3,200,000"},
    "Yeti": {"emoji": "❄️", "price": "2,000,000"},
    "T-Rex": {"emoji": "🦖", "price": "2,700,000"},
    "Dough": {"emoji": "🍩", "price": "2,800,000"},
    "Gas": {"emoji": "☁️", "price": "450,000"},
    "Leopard": {"emoji": "🐆", "price": "5,000,000"}
}

# --- SERVER WEB (KEEP ALIVE) ---
app = Flask('')
@app.route('/')
def home(): return "Stock Bot Online!"

def run(): app.run(host='0.0.0.0', port=PORT)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- BOT LOGIC ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix=".", intents=intents)

@tasks.loop(minutes=15) # Verifică la fiecare 15 minute
async def check_stock():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: 
        print(f"Eroare: Nu am găsit canalul cu ID {CHANNEL_ID}")
        return

    try:
        # URL-ul de unde luăm datele despre stock
        r = requests.get("https://api.bloxfruits.tools/stock")
        data = r.json()
        
        normal_items = data.get("normal", [])
        mirage_items = data.get("mirage", [])

        embed = discord.Embed(title="🍎 Blox Fruits Stock Finder", color=0x2b2d31)
        found_any = False

        # Verificare Normal Stock
        normal_found = []
        for item in normal_items:
            name = item['name']
            if name in FRUITS_DATA:
                normal_found.append(f"{FRUITS_DATA[name]['emoji']} **{name}** • 💲{item['price']:,}")
        
        if normal_found:
            embed.add_field(name="🛒 Current Normal Stock", value="\n".join(normal_found), inline=False)
            found_any = True

        # Verificare Mirage Stock
        mirage_found = []
        for item in mirage_items:
            name = item['name']
            if name in FRUITS_DATA:
                mirage_found.append(f"{FRUITS_DATA[name]['emoji']} **{name}** • 💲{item['price']:,}")

        if mirage_found:
            embed.add_field(name="🏝️ Current Mirage Stock", value="\n".join(mirage_found), inline=False)
            found_any = True

        if found_any:
            await channel.send(content="🚨 **ATENȚIE! Fructe rare în Stock!** @everyone", embed=embed)

    except Exception as e:
        print(f"Eroare la scanare: {e}")

@bot.event
async def on_ready():
    print(f"✅ Botul de Stock a pornit pe canalul {CHANNEL_ID}")
    if not check_stock.is_running():
        check_stock.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
