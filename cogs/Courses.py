import os
import discord
from discord import app_commands
from discord.ext import commands
import selenium

class Courses(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "課程系統"
  
	@commands.Cog.listener()
	async def on_ready(self):
		print("Courses Cog loaded")
  
  
	@commands.hybrid_command(name="search", description="課程查詢")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def daily(self, ctx: commands.Context) -> None:
		"""查詢課程"""
		await ctx.reply("敬請期待")


async def setup(bot: commands.Bot):
	await bot.add_cog(Courses(bot), guilds=[discord.Object(id=539951635288293397)])