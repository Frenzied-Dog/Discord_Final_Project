import os
import discord
from discord import app_commands
from discord.ext import commands

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "經濟系統"
  
	@commands.Cog.listener()
	async def on_ready(self):
		print("Economy Cog loaded")
  
	@commands.hybrid_command(name="daily", description="每日簽到")
	@commands.has_permissions(administrator=True)
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def daily(self, ctx: commands.Context) -> None:
		"""每日簽到"""
		await ctx.reply("簽到成功")
  

async def setup(bot: commands.Bot):
	await bot.add_cog(Economy(bot), guilds=[discord.Object(id=539951635288293397)])