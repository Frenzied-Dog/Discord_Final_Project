import discord
from discord import app_commands
from discord.ext import commands
import os
import time
import sqlite3
from typing import Literal
from random import random

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "經濟系統"
  
	@commands.Cog.listener()
	async def on_ready(self):
		print("Economy Cog loaded")
  
	@commands.hybrid_command(name="daily", description="每日簽到 (+100)")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def daily(self, ctx: commands.Context) -> None:
		"""每日簽到 (+100積分)"""
  
		await ctx.defer()
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
  
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		# check if user exists
		if user == None:
			con.execute("INSERT INTO USERS Values (?, 100, ?);", (ctx.author.id, time.strftime("%Y-%m-%d")))
			con.commit()
			await ctx.reply("初次簽到成功! (+100)")
		elif user[2] == time.strftime("%Y-%m-%d"):
			# check if user has signed in today
			await ctx.reply("今天已經簽到過了!")
		else:
			con.execute("UPDATE USERS SET Coins = ?, LastSigned = ? WHERE ID = ?;",
               					(user["Coins"]+100, time.strftime("%Y-%m-%d"), ctx.author.id))
			con.commit()
			await ctx.reply(f"簽到成功 (+100), 現在為 {user['Coins']+100}")
		con.close()


	@commands.hybrid_command(name="bet", description="賭博")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def bet(self, ctx: commands.Context, amount: int, guess : Literal["Big", "Small"]) -> None:
		"""小遊戲~

		Parameters
		-----------
		amount: int
			要下注的金額
		guess: Literal["Big", "Small"]
			猜大小
		"""

		if amount < 1:
			await ctx.reply("請下注至少1元")
			return

		await ctx.defer()
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		rand = random()
  
		if user == None or user["Coins"] < amount:
			await ctx.reply("你錢不夠QQ")
		elif (guess == "Big" and rand > 0.5) or (guess == "Small" and rand <= 0.5):
			con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user["Coins"]+amount, ctx.author.id))
			con.commit()
			await ctx.reply(f"數字是%.2f 你贏得了{amount}元!" % rand)
		else:
			con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user["Coins"]-amount, ctx.author.id))
			con.commit()		
			await ctx.reply(f"數字是%.2f 你輸掉了{amount}元QQ" % rand)


	@commands.hybrid_command(name="pay", description="支付金錢")
	@commands.guild_only()
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
  
		if amount < 1:
			await ctx.reply("數量必須大於0")
			return

		await ctx.defer()
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
  
		# check if sender/receiver exists in database
		sender = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		receiver = con.execute("SELECT * FROM USERS WHERE ID = ?;", (user.id,)).fetchone()
		if sender == None or sender["Coins"] < amount:
			await ctx.reply("你錢不夠QQ")
		else:
			con.execute("UpDATE USERS SET Coins = ? WHERE ID = ?;",(sender["Coins"]-amount, ctx.author.id))
			if receiver == None:
				con.execute("INSERT INTO USERS Values (?, ?, ?);", (user.id, amount, ""))
			else:
				con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(receiver["Coins"]+amount, user.id))
			con.commit()

		await ctx.reply(f"{ctx.author.mention} 支付了 {amount}元 給{user.mention}")


	@commands.hybrid_command(name="list", description="查詢")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def list(self, ctx: commands.Context) -> None:
		"""查詢自己的金錢"""
  
		await ctx.defer()
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
		
		# check if user exists in database
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		if user == None:
			await ctx.reply("目前還沒有你的資料喔")
		else:
			await ctx.reply(f"{ctx.author.mention} 目前有 {user['Coins']}元\n上次簽到時間: {user['LastSigned']}")


	@commands.hybrid_command(name="rank", description="排行榜")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def rank(self, ctx: commands.Context) -> None:
		"""金錢排行榜"""

		await ctx.defer()
		con = sqlite3.connect('cogs/data.db')
		ranks = con.execute("SELECT ID,Coins FROM USERS ORDER BY Coins DESC LIMIT 5;").fetchall()

		ret = "```\n排行榜:\n"
		for i, (id, coins) in enumerate(ranks):
			name = ctx.guild.get_member(int(id)).display_name
			ret += f"{i+1}. {name} {coins}元\n"
		ret += "```"
  
		await ctx.reply(ret)
		
  
async def setup(bot: commands.Bot):
	await bot.add_cog(Economy(bot), guilds=[discord.Object(id=539951635288293397)])