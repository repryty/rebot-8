from . import register_command, CommandContext
import discord
import sqlite3

import config

@register_command("검색")
async def execute(ctx: CommandContext):
    with sqlite3.connect("data/database.db", timeout=10.0) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT grounding FROM chat_sessions WHERE session_id = ?", (ctx.guild.id, ))
        current_grounding = cursor.fetchone()
    if current_grounding:
        current_grounding = current_grounding[0]
        # print(type(thinking))
    else:
        cursor.execute(
            "INSERT INTO chat_sessions VALUES (?, ?, ?, ?, ?)", 
            (ctx.guild.id, 0.5, 1, 0, "gemini-2.0-flash")
        )
        current_grounding=0
        

    if ctx.args:
        if ctx.args[0].lower()=="on":
            ctx.args[0]=1
        elif ctx.args[0].lower()=="off":
            ctx.args[0]=0
        else:
            await ctx.channel.send("상태를 변경할 수 없습니다.")
            return
        with sqlite3.connect("data/database.db", timeout=10.0) as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE chat_sessions SET grounding=? WHERE session_id=?", (ctx.args[0], ctx.guild.id))
            conn.commit()
        await ctx.channel.send(embed=discord.Embed(
            color=config.MAIN_COLOR,
            title="REBOT LLM",
            description=f"검색 모드가 {'활성' if ctx.args[0] else '비활성'}화되었습니다!"
        ))
    else:
        await ctx.channel.send(embed=discord.Embed(
            color=config.MAIN_COLOR,
            title="REBOT LLM",
            description=f"현재 검색 기능이 `{'활성' if current_grounding else '비활성'}` 상태입니다. ON/OFF로 변경합니다."
        ))
