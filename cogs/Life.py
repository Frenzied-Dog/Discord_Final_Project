import discord
from discord import app_commands
from discord.ext import commands
import os
import requests,json,bs4
import aiohttp,io
import sqlite3
from typing import Literal
from random import randint

top10_url = f"https://api.giphy.com/v1/gifs/trending?api_key={os.getenv('GIPHY_KEY')}&limit=10"
random_url = f"https://api.giphy.com/v1/gifs/random?api_key={os.getenv('GIPHY_KEY')}"
giphy_search_url = f"https://api.giphy.com/v1/gifs/search?api_key={os.getenv('GIPHY_KEY')}&q=%s&limit=25&offset=0&rating=g&lang=en&bundle=messaging_non_clips"
tenor_search_url = f"https://tenor.googleapis.com/v2/search?key={os.getenv('TENOR_KEY')}&q=%s&client_key=fddcbot&limit=5&media_filter=gif&random=true"
StarSigns = Literal["牡羊","金牛","雙子","巨蟹","獅子","處女","天秤","天蠍","射手","摩羯","水瓶","雙魚"]
sign_dict: dict[str,int] = {"牡羊": 0, "金牛": 1, "雙子": 2, "巨蟹": 3, "獅子": 4, "處女": 5, "天秤": 6, "天蠍": 7, "射手": 8, "摩羯": 9, "水瓶": 10, "雙魚": 11}


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
		con.row_factory = sqlite3.Row
  
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
  
		if user == None or user["Coins"] < 5:
			await ctx.reply("你錢不夠QQ")
			con.close()
			return

		con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user["Coins"]-5, ctx.author.id))
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
		con.row_factory = sqlite3.Row
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
  
		if user == None or user["Coins"] < 10:
			await ctx.reply("你錢不夠QQ")	
			con.close()
			return

		con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user["Coins"]-10, ctx.author.id))
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
		

	@commands.hybrid_command(name="star_sign_daily", description="關鍵字搜尋GIF")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def star_sign_daily(self, ctx: commands.Context, sign: StarSigns) -> None:
		"""星座運勢 (每次5積分)
  
		Parameters
		-----------
		sign: str
			星座
		"""
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
  
		if user == None or user["Coins"] < 5:
			await ctx.reply("你錢不夠QQ")	
			con.close()
			return

		con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user["Coins"]-5, ctx.author.id))
		con.commit()
		con.close()
		await ctx.defer()

		try:
			htmlfile = requests.get("https://astro.click108.com.tw/daily.php?iAstro=%d" % sign_dict[sign])
		except Exception as err:
			print(f"網頁下載失敗: {err}")

		soup = bs4.BeautifulSoup(htmlfile.text,'lxml')

		file: discord.File = None
		img_url = soup.find("div", class_="STARBABY").find("img")["src"]
		async with aiohttp.ClientSession() as session: # creates session
			try:
				async with session.get(img_url) as resp: # gets image from url
					img = await resp.read() # reads image from response
					with io.BytesIO(img) as f: # converts to file-like object
						file = discord.File(f, "star_baby.png")
			except Exception as err:
				print(f"圖片取得失敗: {err}")
    
		ret: str = ""
		# content = (soup.find("div", class_="TODAY_CONTENT").text.strip('\n').replace("今日", "**今日").replace("解析", "解析**\n")
        #      												.replace("愛情運勢","\n愛情運勢").replace("事業運勢","\n事業運勢").replace("財運運勢","\n財運運勢"))
		content = soup.find("div", class_="TODAY_CONTENT").text.strip('\n').replace("\n","\n\n").replace("今日", "**今日",1).replace("解析", "解析**",1)
		ret += "%s\n\n" % content
  
		words = soup.find("div", class_="TODAY_WORD").text.strip('\n')
		ret += "今日短評: %s\n\n" % words

		tmp = soup.find_all("div", class_="LUCKY")
		num = tmp[0].text.strip('\n')
		color = tmp[1].text.strip('\n')
		lucky_sign = tmp[4].text.strip('\n')

		ret += "幸運數字: %s\n幸運顏色: %s\n幸運星座: %s\n\n" % (num, color, lucky_sign)

		await ctx.reply(ret, file=file)


async def setup(bot: commands.Bot):
	await bot.add_cog(Life(bot), guilds=[discord.Object(id=539951635288293397)])