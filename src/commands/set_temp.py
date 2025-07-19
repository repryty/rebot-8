from . import register_command, CommandContext
import discord
import sqlite3

import config

@register_command("temp")
async def execute(ctx: CommandContext):
    with sqlite3.connect("data/database.db", timeout=10.0) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT temperature FROM chat_sessions WHERE session_id = ?", (ctx.guild.id, ))
        current_temp = cursor.fetchone()
    if current_temp:
        current_temp = current_temp[0]
        # print(type(thinking))
    else:
        cursor.execute(
            "INSERT INTO chat_sessions VALUES (?, ?, ?, ?, ?)", 
            (ctx.guild.id, 0.5, 1, 0, "gemini-2.0-flash")
        )
        current_temp=0

    if ctx.args:
        with sqlite3.connect("data/database.db", timeout=10.0) as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE chat_sessions SET temperature=? WHERE session_id=?", (int(ctx.args[0]), ctx.guild.id))
            conn.commit()
        await ctx.channel.send(embed=discord.Embed(
            color=config.MAIN_COLOR,
            title="REBOT LLM",
            description=f"Temp가 {int(ctx.args[0])}로 설정되었습니다!"
        ))
    else:
        await ctx.channel.send(embed=discord.Embed(
            color=config.MAIN_COLOR,
            title="REBOT LLM",
            description=f"설정할 Temp를 입력해주세요.\n현재 Temp: {current_temp}"
        ))
