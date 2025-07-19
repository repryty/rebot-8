import discord
import dotenv
import os

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")

DISCORD_INTENTS = discord.Intents.default()
DISCORD_INTENTS.message_content = True

BOT_PREFIX = "ㄹ "

with open("data/system_instruction.txt", "r", encoding="utf-8") as file:
    SYSTEM_INSTRUCTION = file.read()

AVAILABLE_MIME_TYPES = set([
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/pdf",
    "video/mp4",
    "video/mpeg",
    "video/mov",
    "video/avi",
    "video/x-flv",
    "video/mpg",
    "video/webm",
    "video/wmv",
    "video/3gpp",
    "audio/wav",
    "audio/mp3",
    "audio/aiff",
    "audio/aac",
    "audio/ogg",
    "audio/flac"
])

EMOJIES = {
    "🚪": "<:me:1144858072624406588>",
    "⭐": "<:star:1144858244909633619>",
    "❓": "<a:what:1144859308299923536>",
    "🚫": "<:no:1144857465566003253>",
    "🌸": "<:hwal:1144858220263907358>",
    "😊": "<:happy:1144857824866861056>",
    "✍🏼": "<:grab:1144857312377446410>",
    "😔": "<:hing:1144858197551759410>",
    "🫠": "<:liquid:1144857660836036609>",
    "😢": "<:sad:1144857284112040026>",
}

MAIN_COLOR = discord.Colour.from_rgb(34, 75, 176) #224bb0
WARN_COLOR = discord.Colour.from_rgb(181, 0, 0) #b50000