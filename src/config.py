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