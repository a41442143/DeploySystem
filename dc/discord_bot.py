import os
from pathlib import Path

import discord
from discord import app_commands

class DiscordBot(discord.Client):
    def __init__(self, *, intents, **options):
        super().__init__(intents=intents, **options)
        self.tree = app_commands.CommandTree(self)
    async def on_ready(self) -> None:
        print(f"已連線：{self.user}（ID：{self.user.id}）")

def main():
    env_path = Path(__file__).resolve().parent / ".env"
    token = None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator  and key.strip() == "DISCORD_BOT_TOKEN":
            token = value.strip().strip('"').strip("'")
            break
    print(token)
    intents = discord.Intents.default()
    bot = DiscordBot(intents=intents)
    bot.run(token)

if __name__ == "__main__":
    main()