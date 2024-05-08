import discord
from discord import app_commands
from discord.ext import commands
import os
import requests,json,bs4
import sqlite3
from random import randint
from typing import Literal

rate_url = "https://rate.bot.com.tw/xrt/quote/l6m/%s"

class Stock(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "歷史匯率查詢"
		self.currency_choice = []

	@commands.Cog.listener()
	async def on_ready(self):
		print("Stock Cog loaded")

  
	@commands.hybrid_command(name="check_exchange_rate", description="查詢半年內匯率")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def check_exchange_rate(self, ctx: commands.Context, currency: Literal["USD","EUR","CNY","JPY","HKD","KRW","GBP","AUD","CAD",
                                                                              "SGD","CHF","ZAR","SEK","NZD","THB","PHP","IDR","VND","MYR"]) -> None:
		""" 查詢半年內匯率
        
        Parameters
		-----------
		currency: Literal
			選擇的貨幣
        """
        
		await ctx.reply(f'Choosed {currency}. 敬請期待')
  
  
	@check_exchange_rate.error
	async def check_error(self, ctx: commands.Context, error: commands.CommandError):
		await ctx.reply(error)

async def setup(bot: commands.Bot):
	await bot.add_cog(Stock(bot), guilds=[discord.Object(id=539951635288293397)])