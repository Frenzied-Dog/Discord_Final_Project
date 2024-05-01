import discord
from discord import app_commands
from discord.ext import commands
import os
import requests,json
import sqlite3

top10_url = f"https://api.giphy.com/v1/gifs/trending?api_key={os.getenv('GIPHY_KEY')}&limit=10"
random_url = f"https://api.giphy.com/v1/gifs/random?api_key={os.getenv('GIPHY_KEY')}"

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


async def setup(bot: commands.Bot):
	await bot.add_cog(Life(bot), guilds=[discord.Object(id=539951635288293397)])