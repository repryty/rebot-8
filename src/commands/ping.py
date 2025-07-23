from . import register_command, CommandContext
import discord


@register_command("핑")
async def execute(ctx: CommandContext):
    await ctx.channel.send(f"{ctx.client.latency * 1000:.3f}ms")
