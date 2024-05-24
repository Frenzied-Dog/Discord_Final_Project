import sys; sys.path.append("..")
from stonk_analyze import *
import discord
from discord import app_commands
from discord.ext import tasks,commands
from typing import Literal


# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# import requests, bs4, time

# rate_url = "https://rate.bot.com.tw/xrt/quote/l6m/%s"
cur_options = Literal["USD","EUR","CNY","JPY","HKD","GBP","AUD","CAD","SGD","CHF","ZAR","SEK","NZD","THB"]
# currency_choice = ["USD","EUR","CNY","JPY","HKD","GBP","AUD","CAD","SGD","CHF","ZAR","SEK","NZD","THB"]
# en2cn_dict = {"Cash_BID": "現金買入", "Cash_ASK": "現金賣出", "IMM_BID": "即期買入", "IMM_ASK": "即期賣出"}

class Stock(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "歷史匯率查詢"

  
	@commands.Cog.listener()
	async def on_ready(self):
		print("Stock Cog loaded")
		self.fetch_data.start()

	def cog_unload(self):
		self.fetch_data.cancel()

	@tasks.loop(hours=24)
	async def fetch_data(self):
		for i in currency_choice:
			self.bot.datas[i]["raw_data"] = get_info(i)
			self.bot.datas[i]["updown"] = find_updown(self.bot.datas, i)
			self.bot.datas[i]["analysis"] = analyze(self.bot.datas, i)
			self.bot.datas[i]["change"] = find_change(self.bot.datas, i)
			self.bot.datas[i]["BID_ASK_chart"] = discord.File(get_BID_ASK_chart(self.bot.datas, i),filename=f"{i}_BID_ASK.png")
			self.bot.datas[i]["predict"] = discord.File(get_predict(self.bot.datas, [4,7,8], i),filename=f"{i}_predict.png")
			self.bot.datas[i]["change_pie"] = discord.File(get_proportion_pie(self.bot.datas, i),filename=f"{i}_change_pie.png")
		print("Data updated")
   
	@fetch_data.before_loop
	async def before_fetch(self):
		print('Waiting...')
		await self.bot.wait_until_ready()
		print('Ready!')
  
  
	@commands.hybrid_command(name="exchange_rate", description="查詢半年內匯率")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def exchange_rate(self, ctx: commands.Context, currency: cur_options) -> None:
		""" 查詢半年內貨幣最高、最低、平均匯率
		
		Parameters
		-----------
		currency: Literal
			選擇的貨幣
		"""
		
		ret = ""
		for index, row in self.datas[currency]["analysis"].iterrows():
			ret += "%s%s最高匯率: %s 日期: %s\n" % (currency, en2cn_dict[index], row["Max"], row["Max_Date"])
			ret += "%s%s最低匯率: %s 日期: %s\n" % (currency, en2cn_dict[index], row["Min"], row["Min_Date"])
			ret += "%s%s平均匯率: %.3f\n\n" % (currency, en2cn_dict[index], row["Mean"])
		await ctx.reply(ret)


	@commands.hybrid_command(name="best_worst_point", description="查詢最賺及最賠的兌換點")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def best_worst_point(self, ctx: commands.Context, currency: cur_options) -> None:
		""" 查詢半年內最賺及最賠的兌換點
		
		Parameters
		-----------
		currency: Literal
			選擇的貨幣
		"""
		result_df = self.bot.datas[currency]["change"]["result"]
		ret = "%s現金最佳買賣點: %s 匯率差: %.3f\n" % (currency, result_df.at["Cash_Best","Date_Interval"], result_df.at["Cash_Best","Change"])
		ret += "%s現金最差買賣點: %s 匯率差: %.3f\n" % (currency, result_df.at["Cash_Worst","Date_Interval"], result_df.at["Cash_Worst","Change"])
		ret += "%s即期最佳買賣點: %s 匯率差: %.3f\n" % (currency, result_df.at["Spot_Best","Date_Interval"], result_df.at["Spot_Best","Change"])
		ret += "%s即期最差買賣點: %s 匯率差: %.3f" % (currency, result_df.at["Spot_Worst","Date_Interval"], result_df.at["Spot_Worst","Change"])
		await ctx.reply(ret)
  
  
	@commands.hybrid_command(name="buy_sell_chart", description="買入VS賣出散佈折線圖")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def buy_sell_chart(self, ctx: commands.Context, currency: cur_options) -> None:
		""" 查詢半年內的買入VS賣出散佈折線圖
		
		Parameters
		-----------
		currency: Literal
			選擇的貨幣
		"""
		await ctx.reply(file=self.bot.datas[currency]["BID_ASK_chart"])
  
  
	@commands.hybrid_command(name="predicition_chart", description="未來走向預測圖")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def predicition_chart(self, ctx: commands.Context, currency: cur_options) -> None:
		""" 未來走向預測圖
		
		Parameters
		-----------
		currency: Literal
			選擇的貨幣
		"""
		await ctx.reply(file=self.bot.datas[currency]["predict"])	


	@commands.hybrid_command(name="change_pie_chart", description="查詢半年內的漲跌圓餅圖")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def change_pie_chart(self, ctx: commands.Context, currency: cur_options) -> None:
		""" 查詢半年內的漲跌圓餅圖
		
		Parameters
		-----------
		currency: Literal
			選擇的貨幣
		"""
		await ctx.reply(file=self.bot.datas[currency]["change_pie"])
  
  
	@commands.hybrid_command(name="compare_bar_chart", description="查詢兩貨幣的漲跌關聯長條圖")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def compare_bar_chart(self, ctx: commands.Context, currency_a: cur_options, currency_b: cur_options) -> None:
		""" 查詢兩貨幣的漲跌關聯長條圖
		
		Parameters
		-----------
		currencyA: Literal
			選擇的貨幣1
		currencyB: Literal
			選擇的貨幣2
		"""
		ret = get_compare_bar_chart(self.bot.datas, currency_a, currency_b)
  
		await ctx.reply(file=discord.File(ret,filename=f"{currency_a}_{currency_b}_compare_bar.png"))  
  

	@compare_bar_chart.error
	@change_pie_chart.error
	@predicition_chart.error
	@buy_sell_chart.error
	@best_worst_point.error
	@exchange_rate.error
	async def check_error(self, ctx: commands.Context, error: commands.CommandError):
		await ctx.reply(error)

async def setup(bot: commands.Bot):
	await bot.add_cog(Stock(bot), guilds=[discord.Object(id=539951635288293397)])