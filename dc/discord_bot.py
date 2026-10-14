import os
from pathlib import Path
import time
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

    @bot.tree.command(name="show_project", description="顯示目前系統有哪些已偵測到的project(project想被偵測須將config放置在該系統資料夾的project_config中)")
    async def show_project(interaction: discord.Interaction) -> None:
        await time.sleep(10) #之後一併補上

    @bot.tree.command(name="depoly", description="部屬/開啟指定網站")
    @app_commands.describe(path="指定config路徑")
    async def deploy(interaction: discord.Interaction, path:Path) -> None:
        await time.sleep(10) #之後一併補上

    @bot.tree.command(name="test", description="測試指定網站")
    @app_commands.describe(path="指定config路徑")
    async def test(interaction: discord.Interaction, path) -> None:
        await time.sleep(10) #之後一併補上

    @bot.tree.command(name="logs", description="顯示指定網站運行的log")
    @app_commands.describe(path="指定config路徑")
    async def logs(interaction: discord.Interaction, path) -> None:
        await time.sleep(10) #之後一併補上

    @bot.tree.command(name="start", description="開啟運行指定專案的容器")
    @app_commands.describe(path="指定config路徑")
    async def start(interaction: discord.Interaction, path) -> None:
        await time.sleep(10) #之後一併補上

    @bot.tree.command(name="status", description="顯示指定專案的容器的狀態")
    @app_commands.describe(path="指定config路徑")
    async def status(interaction: discord.Interaction, path) -> None:
        await time.sleep(10) #之後一併補上

    @bot.tree.command(name="stop", description="停止運行指定專案的容器")
    @app_commands.describe(path="指定config路徑")
    async def stop(interaction: discord.Interaction, path) -> None:
        await time.sleep(10) #之後一併補上

    @bot.tree.command(name="remove", description="移除運行指定專案的容器")
    @app_commands.describe(path="指定config路徑")
    async def remove(interaction: discord.Interaction, path) -> None:
        await time.sleep(10) #之後一併補上


if __name__ == "__main__":
    main()