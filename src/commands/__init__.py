from dataclasses import dataclass
import discord
import importlib
import os

@dataclass
class CommandContext:
    message: discord.Message
    args: list[str]
    client: discord.Client
    
    @property
    def author(self):
        return self.message.author
    
    @property
    def channel(self):
        return self.message.channel
    
    @property
    def guild(self):
        return self.message.guild

commands_list = dict()

def register_command(command_name: str):
    def decorator(func):
        commands_list[command_name] = func
        return func
    return decorator

current_dir = os.path.dirname(os.path.abspath(__file__))
for file in os.listdir(current_dir):
    if file.endswith('.py') and file != '__init__.py':
        module_name = file[:-3]
        module = importlib.import_module(f"commands.{module_name}")