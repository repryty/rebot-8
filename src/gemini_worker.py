import asyncio
from google import genai
from google.genai import types
import sqlite3
import discord
import logging
import json
import mimetypes
import re
import time

import config

genai_client = genai.Client(api_key=config.GEMINI_TOKEN)

grounding_tool = types.Tool(google_search=types.GoogleSearch())
url_context_tool = types.Tool(url_context=types.UrlContext)

"""
gemini_queue.put({
    "message_id": message.id,
    "sent_bot_message": gemini_message,
    "guild_id": message.guild.id,
    "content": message.content,
    "attachments": message.attachments
})
"""


def get_attachment_part(filename: str):
    with open(filename, "rb") as file:
        image_bytes = file.read()
    result = types.Part.from_bytes(data=image_bytes, mime_type=mimetypes.guess_type(filename)[0])
    return result


def apply_custom_emoji(inp: str) -> str:
    for target, emoji in config.EMOJIES.items():
        inp = re.sub(target, emoji, inp)
    return inp


class GeminiWorker:
    def __init__(self, task_queue: asyncio.Queue):
        self.task_queue = task_queue
        self.running = True

    def stop(self):
        self.running = False

    async def worker_loop(self):
        while self.running:
            # asyncio.Queue 사용
            task = await self.task_queue.get()

            # DB 통신
            with sqlite3.connect("data/database.db", timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT temperature, thinking, grounding, model \
                                FROM chat_sessions \
                                WHERE session_id = ?",
                    (int(task["guild_id"]),),
                )
                result = cursor.fetchone()
                if result:
                    temperature, thinking, grounding, model = result
                    # print(type(thinking))
                else:
                    cursor.execute(
                        "INSERT INTO chat_sessions VALUES (?, ?, ?, ?, ?)",
                        (task["guild_id"], 0.5, 1, 0, "gemini-2.0-flash"),
                    )
                    temperature, thinking, grounding, model = (
                        0.5,
                        1,
                        0,
                        "gemini-2.0-flash",
                    )
                conn.commit()

            # 이미지 전처리
            attachments = []
            attachments_filename_list = []
            ignored_attachments = []
            for i, image in enumerate(task["attachments"]):
                image: discord.Attachment
                if image.content_type in config.AVAILABLE_MIME_TYPES:
                    filename = f"images/{task['message_id']}-{i}.{image.filename.split('.')[-1]}"
                    await image.save(filename)
                    attachments.append(get_attachment_part(filename))
                    attachments_filename_list.append(filename)
                else:
                    ignored_attachments.append(image.filename)

            # DB로 대화 기록 복원
            with sqlite3.connect("data/database.db", timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT message_content, attachments_list, role FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
                    (task["guild_id"],),
                )
                messages = cursor.fetchall()
            chat_history = []
            for message in messages:
                attachment_list = json.loads(message["attachments_list"])
                chat_history.append(
                    types.Content(
                        role=message["role"],
                        parts=[types.Part(text=message["message_content"])]
                        + [get_attachment_part(i) for i in attachment_list],
                    )
                )

            # API 호출
            response = genai_client.models.generate_content_stream(
                model=model,
                config=types.GenerateContentConfig(
                    max_output_tokens=2048,
                    temperature=temperature,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=(900 * thinking), include_thoughts=True
                    )
                    if "2.5" in model
                    else None,
                    tools=[grounding_tool, url_context_tool] if grounding else None,
                    system_instruction=config.SYSTEM_INSTRUCTION,
                ),
                contents=chat_history
                + [
                    types.Content(
                        role="user",
                        parts=[types.Part(text=task["content"])] + attachments,
                    )
                ]
                + [
                    types.Content(
                        role="model",
                        parts=[types.Part(text="Sure! Here is response:\n")],
                    )
                ],
            )

            # 수신
            msg = task["sent_bot_message"]
            msg: discord.Message
            all_output = ""
            output = ""
            grounding_data = []
            last_update_time = time.time()
            update_interval = 1.5  # 1.5초마다 메시지 수정

            for chunk in response:
                try:
                    part = chunk.candidates[0].content.parts[0]
                except (IndexError, AttributeError):
                    continue

                if part.thought:
                    # "생각 중" 상태는 즉시 업데이트하여 사용자에게 피드백을 줍니다.
                    if (
                        time.time() - last_update_time > 0.5
                    ):  # 이 또한 너무 잦은 업데이트를 방지합니다.
                        await msg.edit(
                            content=output
                            if output
                            else "<a:loading:1264015095223287878> " + part.text.split("\n")[0]
                        )
                        last_update_time = time.time()
                else:
                    if len(output) > 1600:  # 디스코드 최대 컨텍스트 2000
                        all_output += output
                        output = ""
                        msg = await msg.channel.send("-# <:BLANK_ICON:1395775593391325184>")
                    output += chunk.text

                    # 일정 간격으로만 메시지를 수정하여 API 호출을 줄입니다.
                    if time.time() - last_update_time > update_interval:
                        await msg.edit(
                            content=apply_custom_emoji(
                                output if output else "<a:loading:1264015095223287878>"
                            )
                        )
                        last_update_time = time.time()

                if chunk.candidates[0].grounding_metadata:
                    grounding_chunks = chunk.candidates[0].grounding_metadata.grounding_chunks
                    if grounding_chunks:
                        title = grounding_chunks[0].web.title
                        if title not in grounding_data:
                            grounding_data.append(title)

            # 루프가 끝난 후, 최종적으로 완성된 메시지를 한 번만 전송합니다.
            final_content = apply_custom_emoji(
                output
                + (
                    ("\n-# 다음 웹 사이트에서 참조됨: " + ", ".join(list(set(grounding_data))))
                    if grounding_data
                    else ""
                )
            )
            await msg.edit(
                content=final_content if final_content.strip() else "생성된 콘텐츠가 없습니다."
            )
            all_output += output
            logging.info(all_output)

            # DB 통신
            with sqlite3.connect("data/database.db", timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_messages (message_id, session_id, message_content, attachments_list, role) VALUES (?, ?, ?, ?, ?)",
                    (
                        task["message_id"],
                        task["guild_id"],
                        task["content"],
                        json.dumps(attachments_filename_list),
                        "user",
                    ),
                )
                cursor.execute(
                    "INSERT INTO chat_messages (message_id, session_id, message_content, attachments_list, role) VALUES (?, ?, ?, ?, ?)",
                    (msg.id, task["guild_id"], all_output, "[]", "model"),
                )
                conn.commit()

            # 작업 완료 표시
            self.task_queue.task_done()

            await msg.add_reaction("✅")
