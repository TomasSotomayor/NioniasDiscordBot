import nextcord
from nextcord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='%', intents=intents)

# Cargar extensiones (otros archivos para que funcionen con el bot)
extensions = [
    "ratings",
    "roulette",
    "diceroller",
    "battleroyale"
]
if __name__ == "__main__": # Carga las extensiones
    for extension in extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    os.system("cls" if os.name == "nt" else "clear")
    try:
        await bot.sync_application_commands()
    except Exception as e:
        print("Sync error:", e)
    print(f"{bot.user} ready!")

bot.run(token)