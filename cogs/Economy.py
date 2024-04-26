import discord
from discord import app_commands
from discord.ext import commands
import os
from random import random

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "經濟系統"
  
	@commands.Cog.listener()
	async def on_ready(self):
		print("Economy Cog loaded")
  
	@commands.hybrid_command(name="daily", description="每日簽到")
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def daily(self, ctx: commands.Context) -> None:
		"""每日簽到"""
  
		# To do: check if user has already signed in today
		# To do: sql database
		await ctx.reply("簽到成功")


	@commands.hybrid_command(name="bet", description="賭博")
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def bet(self, ctx: commands.Context, amount: int) -> None:
		"""小遊戲~

		Parameters
		-----------
		amount: int
			要下注的金額
		"""
		# To do: check if user has enough money & amount is valid
		# To do: sql database
		if (random()) > 0.7:
			await ctx.reply(f"贏得{amount}")
		else:
			await ctx.reply(f"輸掉{amount}")


	@commands.hybrid_command(name="pay", description="支付金錢")
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def pay(self, ctx: commands.Context, user: discord.Member, amount: int) -> None:
		"""支付金錢給某人

		Parameters
		-----------
		user: discord.Member
			要支付的對象
		amount: int
			要支付的金額
		"""
  
		# To do: check if user has enough money
		# To do: sql database
		await ctx.reply(f"{ctx.author.mention} 支付了 {amount}元 給{user.mention}")

async def setup(bot: commands.Bot):
	await bot.add_cog(Economy(bot), guilds=[discord.Object(id=539951635288293397)])