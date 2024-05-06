import discord
from discord import app_commands
from discord.ext import commands
import os
import time
import sqlite3
from random import random

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "經濟系統"
  
	@commands.Cog.listener()
	async def on_ready(self):
		print("Economy Cog loaded")
  
	@commands.hybrid_command(name="daily", description="每日簽到")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def daily(self, ctx: commands.Context) -> None:
		"""每日簽到"""
  
		# To do: check if user has already signed in today
		# To do: sql database
		con = sqlite3.connect('cogs/data.db')
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		if user == None:
			con.execute("INSERT INTO USERS Values (?, 10, ?);", (ctx.author.id, time.strftime("%Y-%m-%d")))
			con.commit()
			await ctx.reply("初次簽到成功! (+10)")
		elif user[2] == time.strftime("%Y-%m-%d"):
			await ctx.reply("今天已經簽到過了!")
		else:
			con.execute("UPDATE USERS SET Coins = ?, LastSigned = ? WHERE ID = ?;",
               					(user[1]+10, time.strftime("%Y-%m-%d"), ctx.author.id))
			con.commit()
			await ctx.reply(f"簽到成功 (+10), 現在為 {user[1]+10}")
		con.close()


	@commands.hybrid_command(name="bet", description="賭博")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def bet(self, ctx: commands.Context, amount: int, big : bool = True) -> None:
		"""小遊戲~

		Parameters
		-----------
		amount: int
			要下注的金額
		big: bool
			猜大小(預設猜大)
		"""

		if amount < 1:
			await ctx.reply("請下注至少1元")
			return

		con = sqlite3.connect('cogs/data.db')
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		rand = random()
  
		if user == None or user[1] < amount:
			await ctx.reply("你錢不夠QQ")
		elif (big and rand > 0.5) or (not big and rand <= 0.5):
			con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user[1]+amount, ctx.author.id))
			con.commit()
			await ctx.reply(f"數字是%.2f 你贏得了{amount}元!" % rand)
		else:
			con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user[1]-amount, ctx.author.id))
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

		con = sqlite3.connect('cogs/data.db')
		sender = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		receiver = con.execute("SELECT * FROM USERS WHERE ID = ?;", (user.id,)).fetchone()
		if sender == None or sender[1] < amount:
			await ctx.reply("你錢不夠QQ")
		else:
			con.execute("UpDATE USERS SET Coins = ? WHERE ID = ?;",(sender[1]-amount, ctx.author.id))
			if receiver == None:
				con.execute("INSERT INTO USERS Values (?, ?, ?);", (user.id, amount, ""))
			else:
				con.execute("UpDATE USERS SET Coins = ? WHERE ID = ?;",(receiver[1]+amount, user.id))
			con.commit()

		await ctx.reply(f"{ctx.author.mention} 支付了 {amount}元 給{user.mention}")


	@commands.hybrid_command(name="list", description="查詢")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def list(self, ctx: commands.Context) -> None:
		"""查詢自己的金錢"""
  
		con = sqlite3.connect('cogs/data.db')
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		if user == None:
			await ctx.reply("目前還沒有你的資料喔")
		else:
			await ctx.reply(f"{ctx.author.mention} 目前有 {user[1]}元\n上次簽到時間: {user[2]}")


	@commands.hybrid_command(name="rank", description="排行榜")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def rank(self, ctx: commands.Context) -> None:
		"""金錢排行榜"""
  
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