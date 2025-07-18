import discord
import os
import sqlite3
import logging
import asyncio
# import threading
# import queue
# from dataclasses import dataclass

import config
import commands
import gemini_worker


logging.basicConfig(level=logging.INFO)

client = discord.Client(intents=config.DISCORD_INTENTS)

gemini_queue = asyncio.Queue()
gemini_worker_class= gemini_worker.GeminiWorker(gemini_queue)

@client.event
async def on_ready():
    logging.info("Initializing...")

    # 디렉토리 생성
    os.makedirs("data", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    
    
    try:
        with sqlite3.connect("data/database.db") as conn:
            cursor = conn.cursor()

            # 세션 테이블 생성
            cursor.execute("""CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id INTEGER PRIMARY KEY,
                temperature INTEGER,
                thinking INTEGER,
                grounding INTEGER,
                model TEXT
            )""")

            # 메세지 테이블 생성
            cursor.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
                message_id INTEGER PRIMARY KEY,
                session_id INTEGER,
                message_content TEXT,
                attachments_list TEXT,
                role TEXT,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
            )""")
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

    logging.info("Gemini Worker is Starting...")
    # 백그라운드 태스크로 워커 시작
    asyncio.create_task(gemini_worker_class.worker_loop())

    logging.info("REBOT client is activated.")

@client.event
async def on_message(message: discord.Message):
    if not message.content.startswith(config.BOT_PREFIX):
        return
    if message.author == client.user:
        return
    args = message.content.removeprefix(config.BOT_PREFIX).split() # !고양이 최고 => [고양이, 최고]
    command = args.pop(0)
    # print(commands.commands_list)
    if command in commands.commands_list:
        await commands.commands_list[command](commands.CommandContext(message, args, client))
    else:
        gemini_message = await message.channel.send("<a:loading:1264015095223287878>")
        # asyncio.Queue의 put은 async 메서드
        await gemini_queue.put({
            "message_id": message.id,
            "sent_bot_message": gemini_message,
            "guild_id": message.guild.id,
            "content": message.content,
            "attachments": message.attachments
        })

client.run(config.DISCORD_TOKEN)