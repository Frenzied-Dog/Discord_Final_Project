import discord
from discord import app_commands
from discord.ext import commands
import os
import requests,json
import sqlite3
from random import randint

top10_url = f"https://api.giphy.com/v1/gifs/trending?api_key={os.getenv('GIPHY_KEY')}&limit=10"
random_url = f"https://api.giphy.com/v1/gifs/random?api_key={os.getenv('GIPHY_KEY')}"
giphy_search_url = f"https://api.giphy.com/v1/gifs/search?api_key={os.getenv('GIPHY_KEY')}&q=%s&limit=25&offset=0&rating=g&lang=en&bundle=messaging_non_clips"
tenor_search_url = f"https://tenor.googleapis.com/v2/search?q=%s&key={os.getenv('TENOR_KEY')}&client_key=fddcbot&limit=5&media_filter=gif&random=true"

class Life(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "生活系統"
  
	@commands.Cog.listener()
	async def on_ready(self):
		print("Life Cog loaded")


	@commands.hybrid_command(name="random_gif", description="隨機GIF")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def random_gif(self, ctx: commands.Context) -> None:
		"""隨機GIF (每次5積分)"""
		con = sqlite3.connect('cogs/data.db')
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
  
		if user == None or user[1] < 5:
			await ctx.reply("你錢不夠QQ")	
		else:
			con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user[1]-5, ctx.author.id))
			con.commit()
   
			response = requests.get(random_url)
			if response.status_code == 200:
				data = json.loads(response.content.decode("utf-8"))
				gif = data["data"]
				await ctx.reply(gif["url"])
			else:
				print("Something went wrong")
			con.close()


	@commands.hybrid_command(name="search_gif", description="關鍵字搜尋GIF")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def search_gif(self, ctx: commands.Context, keyword: str) -> None:
		"""關鍵字搜尋GIF (每次10積分)
  
		Parameters
		-----------
		keyword: str
			關鍵字
		"""
		con = sqlite3.connect('cogs/data.db')
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
  
		if user == None or user[1] < 10:
			await ctx.reply("你錢不夠QQ")	
		else:
			con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user[1]-0, ctx.author.id)) # for testing
			con.commit()
			con.close()

			await ctx.defer()
   
			# try tenor first
			response = requests.get(tenor_search_url % keyword)
			if response.status_code == 200:
				data = json.loads(response.content.decode("utf-8"))
				if len(data["results"]) == 0:
					# try giphy if tenor has no results
					response = requests.get(giphy_search_url % keyword)
					if response.status_code == 200:
						data = json.loads(response.content.decode("utf-8"))
						if len(data["data"]) == 0:
							await ctx.reply("找不到相關GIF")
						else:
							gif = data["data"][randint(0,len(data["data"])-1)]
							await ctx.reply(gif["url"])							
				else:
					gif = data["results"][randint(0,len(data["results"])-1)]
					await ctx.reply(gif["url"])
			else:
				print("Something went wrong")

async def setup(bot: commands.Bot):
	await bot.add_cog(Life(bot), guilds=[discord.Object(id=539951635288293397)])