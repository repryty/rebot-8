from . import register_command, CommandContext
import discord
import sqlite3
from google import genai

import config
from gemini_worker import genai_client

@register_command("모델")
async def execute(ctx: CommandContext):
    if ctx.args:
        await ctx.channel.send(embed=discord.Embed(
            color=config.MAIN_COLOR,
            title="REBOT LLM",
            description=f"모델이 `{genai_client.models.get(model=ctx.args[0]).display_name}`으로 설정되었습니다!"
            
        ))
        with sqlite3.connect("data/database.db", timeout=10.0) as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE chat_sessions SET model=? WHERE session_id=?", (ctx.args[0], ctx.guild.id))
            conn.commit()
        return

    with sqlite3.connect("data/database.db", timeout=10.0) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT model FROM chat_sessions WHERE session_id = ?", (ctx.guild.id, ))
        current_model = cursor.fetchone()[0].removeprefix("models/")

    models_list = []
    models_name_list = []
    major_models=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
    for model in genai_client.models.list():
        if "generateContent" in model.supported_actions:
            if any(major_model in model.name for major_model in major_models):
                models_list.append(discord.SelectOption(
                    label=model.display_name, 
                    value=model.name, 
                    description=model.name
                    ))
            models_name_list.append(model.name)
            # print(model.name)
    # print(models_list)

    async def select_callback(interaction: discord.Interaction):
        await interaction.response.send_message(f"모델이 `{genai_client.models.get(model=select.values[0]).display_name}`으로 변경되었습니다!")
        with sqlite3.connect("data/database.db", timeout=10.0) as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE chat_sessions SET model=? WHERE session_id=?", (select.values[0], ctx.guild.id))
            conn.commit()

    async def all_model_button_callback(interaction: discord.Interaction):
        dm_channel = await ctx.author.create_dm()
        await dm_channel.send("\n".join(models_name_list))

    select = discord.ui.Select(options=models_list[:20], placeholder="주요 모델 선택")
    select.callback = select_callback

    all_model_button = discord.ui.Button(label="모든 모델")
    all_model_button.callback = all_model_button_callback

    view = discord.ui.View()
    view.add_item(select)
    view.add_item(all_model_button)

    await ctx.channel.send(embed=discord.Embed(
        color=config.MAIN_COLOR,
        title="REBOT LLM",
        description=f"사용할 모델을 선택해주세요.\n현재 모델: {current_model}"
    ), view=view)
