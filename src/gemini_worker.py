import asyncio
from google import genai
from google.genai import types
import sqlite3
import discord
import logging
import json

import config

genai_client = genai.Client(api_key=config.GEMINI_TOKEN)

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)
url_context_tool = types.Tool(
    url_context=types.UrlContext
)

"""
gemini_queue.put({
    "message_id": message.id,
    "sent_bot_message": gemini_message,
    "guild_id": message.guild.id,
    "content": message.content,
    "attachments": message.attachments
})
"""

class GeminiWorker:
    def __init__(self, task_queue):
        self.task_queue = task_queue
        self.running = True
    
    def stop(self):
        self.running=False
    
    async def worker_loop(self):
        while self.running:
            try:
                # asyncio.Queue 사용
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # DB 통신
                with sqlite3.connect("data/database.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT temperature, thinking, grounding, model \
                                   FROM chat_sessions \
                                   WHERE session_id = ?", (int(task["guild_id"]), ))
                    result = cursor.fetchone()
                    if result:
                        temperature, thinking, grounding, model = result
                    else:
                        cursor.execute(
                            "INSERT INTO chat_sessions VALUES (?, ?, ?, ?, ?)", 
                            (task["guild_id"], 0.5, 1, 0, "gemini-2.0-flash")
                        )
                        temperature, thinking, grounding, model = 0.5, 1, 0, "gemini-2.0-flash"

                # 이미지 전처리
                attachments = []
                attachments_filename_list = []
                ignored_attachments = []
                for i, image in enumerate(task["attachments"]):
                    image: discord.Attachment
                    if image.content_type in config.AVAILABLE_MIME_TYPES:
                        filename=f"images/{task['message_id']}-{i}.{image.filename.split('.')[-1]}"
                        await image.save(filename)
                        with open(filename, "rb") as file:
                            image_bytes=file.read()
                        attachments.append([
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=image.content_type
                            )
                        ])
                        attachments_filename_list.append(filename)
                    else:
                        ignored_attachments.append(image.filename)

                # API 호출
                response = genai_client.models.generate_content_stream(
                    model=model,
                    config=types.GenerateContentConfig(
                        max_output_tokens=2048,
                        temperature=temperature,
                        thinking_config=(types.ThinkingConfig(thinking_budget=(900 if thinking else 0)) if "2.5" in model else None),
                        tools=[grounding_tool, url_context_tool] if grounding else None,
                        system_instruction=config.SYSTEM_INSTRUCTION
                    ),
                    contents=[
                        task["content"]
                    ] + attachments
                )

                # 수신
                msg = task["sent_bot_message"]
                msg: discord.Message
                all_output=""
                output = ""
                for chunk in response:
                    if len(output)>1600: # 디스코드 최대 컨텍스트 2000
                        all_output+=output
                        output=""
                        msg = await msg.channel.send("-# <:BLANK_ICON:1395775593391325184>")
                    output+=chunk.text
                    # print(chunk.text, end="")
                    await msg.edit(content=output if output else "<a:loading:1264015095223287878>")
                all_output+=output

                logging.info(all_output)

                # DB 통신
                with sqlite3.connect("data/database.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO chat_messages VALUES (?, ?, ?, ?, ?)", 
                        (task["message_id"], task["guild_id"], task["content"], json.dumps(attachments_filename_list), "user")
                    )
                    cursor.execute(
                        "INSERT INTO chat_messages VALUES (?, ?, ?, ?, ?)", 
                        (task["message_id"], task["guild_id"], all_output, "", "model")
                    )
                
                # 작업 완료 표시
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
