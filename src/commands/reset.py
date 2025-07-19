from . import register_command, CommandContext
import sqlite3
import os
import json

@register_command("초기화")
async def execute(ctx: CommandContext):
    with sqlite3.connect("data/database.db", timeout=10.0) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT attachments_list FROM chat_messages WHERE session_id = ? AND attachments_list != '[]'", (ctx.guild.id, ))
        attachments_list = cursor.fetchall()

        for (attachment,) in attachments_list:
            filename,  = json.loads(attachment)
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass

        cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (ctx.guild.id, ))

        conn.commit()
    await ctx.channel.send("이 서버의 채팅 기록이 삭제되었습니다.")