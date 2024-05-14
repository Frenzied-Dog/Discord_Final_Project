import re,os,io,asyncio
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException as NoElement
from selenium.common.exceptions import TimeoutException as OOT
from selenium.webdriver.support.ui import WebDriverWait as WebWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.add_argument("--disable-notifications")
options.add_argument("--headless")
options.add_argument('--disable-gpu')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

syllabus_url = "https://class-qry.acad.ncku.edu.tw/syllabus/syllabus.php?"
course_url = "https://course.ncku.edu.tw/index.php?c=qry11215&m=en_query"

class Courses(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "課程系統"

	@commands.Cog.listener()
	async def on_ready(self):
		print("Courses Cog loaded")


	async def build_message(self, web: WebDriver, the_class: list[WebElement], data: tuple[str,str,str]) -> tuple[str,Optional[discord.File]]:
		ret: str = ""
		teacher: str = the_class[6].text
		time_place: str = the_class[-2].text
		class_name, course_id, link = data
		pic = None
		if time_place.endswith("上課時間"):
			time_place = time_place.removesuffix("上課時間").removesuffix("\n")
			the_class[-2].find_element(By.CLASS_NAME,"flex_time").click()
			await asyncio.sleep(1)
			table = web.find_element(By.ID,"show_note_msg").find_element(By.CLASS_NAME,"modal-content").screenshot_as_png
			pic = io.BytesIO(table); pic.seek(0)
			web.find_element(By.ID,"show_note_msg").find_element(By.TAG_NAME,"button").click()

		# link: str = the_class[-1].find_element(By.TAG_NAME,"a").get_attribute("href")
		link = "[連結點我]("  + link + ")"
		ret += f"**{class_name}** {course_id}\n教師: {teacher}\n"

		time_place = time_place.replace("\n","\n\t")
		if pic is None: ret += f"上課時間,地點:\n\t{time_place}\n"
		else: 
			ret += f"上課地點(時間請看下圖):\n\t{('無' if time_place=='' else time_place)}\n"
			pic = discord.File(pic,filename='time_table.png')

		ret += f"課程大綱: {link} \n\n"
		return ret,pic

	@commands.hybrid_command(name="search", description="課程查詢")
	@commands.guild_only()
	@app_commands.rename(name='course_name')
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def search(self, ctx: commands.Context, name: str, course_id: str = None) -> None:
		"""查詢課程大綱

		Parameters
		-----------
		name: str
			課程名稱(全部或部分,請先確定系統中是否查得到)
		course_id: str
			課程代碼(可選 ex: E2-025,請依此格式輸入)
		"""
  
		# check if course_id has correct format
		if course_id is not None and not re.match('[A-Z]([0-9]|[A-Z])-[0-9]{3}',course_id):
			await ctx.reply("課程代碼格式錯誤")
			return

		await ctx.defer()

		# check if user has enough coins
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
		user = con.execute("SELECT * FROM USERS WHERE ID = ?;", (ctx.author.id,)).fetchone()
		if user == None or user["Coins"] < 20:
			await ctx.reply("你錢不夠QQ")

		# start searching
		web = webdriver.Chrome(options=options)
		web.set_window_size(1920, 1030)
		web.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
		web.get(course_url)

		try: WebWait(web, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="cosname"]')))
		except OOT: await ctx.reply("網站逾時(載入)"); web.quit(); return

		# type in the course name
		web.find_element(By.XPATH,'//input[@id="cosname"]').send_keys(name)
		web.find_element(By.XPATH,'//div[@id="main_content"]/div[3]/button').click()

		try: WebWait(web, 10).until(EC.invisibility_of_element_located((By.XPATH, '/html/body/div[1]/div')))
		except OOT: await ctx.reply("網站逾時(搜尋)"); web.quit(); return

		# get the search results
		class_lists = web.find_element(By.XPATH,'//div[@id="result"]/table/tbody').find_elements(By.TAG_NAME,"tr")
		if len(class_lists) == 0:
			await ctx.reply("查無資料")
			web.quit()
			con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user["Coins"]-20, ctx.author.id))
			con.commit()
			con.close()
			return

		count: int = 0
		pics: list[discord.File] = []
		ret: str = ""
		for i in class_lists:
			each_class = i.find_elements(By.TAG_NAME,"td")
			id: str = each_class[1].find_element(By.CLASS_NAME,"dept_seq").text
			class_name: str = each_class[4].find_element(By.CLASS_NAME,"course_name").text
			if class_name == '': continue
			link: str = each_class[-1].find_element(By.TAG_NAME,"a").get_attribute("href")
   
			# check if the course is in the database
			db_search = con.execute("SELECT Name FROM COURSES WHERE ID = ?;",(id,)).fetchone()
			if db_search is None:
				con.execute("INSERT INTO COURSES VALUES (?,?,?);",(id,class_name,link.removeprefix(syllabus_url)))

			if course_id is not None:
				if course_id == id:
					value = await self.build_message(web, each_class, (id, class_name, link))
					ret += value[0]
					if value[1] is not None: pics.append(value[1])
				else: continue
			else:
				value = await self.build_message(web, each_class, (id, class_name, link))
				ret += value[0]
				if value[1] is not None: pics.append(value[1])
    
				count += 1
				if count >= 5: break
		else:
			if count == 0: ret = "找不到指定的課程代碼!"
		await ctx.reply(ret,files=pics)
		web.quit()
		con.execute("UPDATE USERS SET Coins = ? WHERE ID = ?;",(user["Coins"]-20, ctx.author.id))
		con.commit()
		con.close()

	@commands.hybrid_command(name="add_favorite", description="新增最愛")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def add_favorite(self, ctx: commands.Context, course_id: str, name: str|None = None) -> None:
		"""新增課程至我的最愛

		Parameters
		-----------
		course_id: str
			課程代碼(ex: E2-025,請依此格式輸入)
		name: str
			課程名稱(全部或部分,請先確定系統中是否查得到)
		"""
  
		# check if course_id has correct format
		if course_id is not None and not re.match('[A-Z]([0-9]|[A-Z])-[0-9]{3}',course_id):
			await ctx.reply("課程代碼格式錯誤")
			return
     
		# check if the course is in the database
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
		db_search = con.execute("SELECT Name FROM COURSES WHERE ID = ?;",(course_id,)).fetchone()
		if db_search is None and name is None:
			await ctx.reply("資料庫中無此課程代碼! 請輸入課程名稱或先進行搜尋")
			return
		elif db_search is None and name is not None:
			# if not in the database, search for the course
			web = webdriver.Chrome(options=options)
			web.set_window_size(1920, 1030)
			web.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
			web.get(course_url)

			try: WebWait(web, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="cosname"]')))
			except OOT: await ctx.reply("網站逾時(載入)"); web.quit(); return

		 	# type in the course name
			web.find_element(By.XPATH,'//input[@id="cosname"]').send_keys(name)
			web.find_element(By.XPATH,'//div[@id="main_content"]/div[3]/button').click()

			try: WebWait(web, 10).until(EC.invisibility_of_element_located((By.XPATH, '/html/body/div[1]/div')))
			except OOT: await ctx.reply("網站逾時(搜尋)"); web.quit(); return
   
			class_lists = web.find_element(By.XPATH,'//div[@id="result"]/table/tbody').find_elements(By.TAG_NAME,"tr")
			if len(class_lists) == 0:
				await ctx.reply("查無資料")
				web.quit()
				return

			for i in class_lists:
				each_class = i.find_elements(By.TAG_NAME,"td")
				id: str = each_class[1].find_element(By.CLASS_NAME,"dept_seq").text
				class_name: str = each_class[4].find_element(By.CLASS_NAME,"course_name").text
				if class_name == '': continue
				link: str = each_class[-1].find_element(By.TAG_NAME,"a").get_attribute("href")
    
				# check if the course is in the database
				db_search = con.execute("SELECT Name FROM COURSES WHERE ID = ?;",(id,)).fetchone()
				if db_search is None:
					con.execute("INSERT INTO COURSES VALUES (?,?,?);",(id,class_name,link.removeprefix(syllabus_url)))

				if id == course_id:
					break
			else:
				await ctx.reply("找不到指定的課程代碼! 請確認課名是否有誤")
				web.quit()
				con.commit()
				con.close()
				return
			web.quit()

		con.execute("INSERT INTO FAVORITE VALUES (?,?);",(ctx.author.id,course_id))
		con.commit()
		await ctx.reply(f"已將`{course_id}: {db_search['Name'] if db_search is not None else class_name}`加入最愛")
		con.close()
			
  
	@commands.hybrid_command(name="list_favorite", description="列出最愛")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def list_favorite(self, ctx: commands.Context) -> None:
		"""列出我的最愛中的課程"""
		# get the list of favorite courses
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
		lists = con.execute("SELECT CourseID,Name,URL FROM FAVORITE JOIN COURSES ON COURSES.ID = FAVORITE.CourseID " +
                      												"WHERE UserID = ?;", (ctx.author.id,)).fetchall()
		if len(lists) == 0:
			await ctx.reply("無最愛課程")
		else:
			ret = f"**{ctx.author.display_name}** 的最愛課程:\n"
			for i,j in enumerate(lists):
				ret += f"{i+1}. **{j['Name']}** [{j['CourseID']}] [課程大綱]({syllabus_url+j['URL']})\n"
			await ctx.reply(ret)
		con.close()

   
	@commands.hybrid_command(name="remove_favorite", description="移除最愛")
	@commands.guild_only()
	@app_commands.guilds(discord.Object(id=539951635288293397))
	async def remove_favorite(self, ctx: commands.Context, course_id: str) -> None:
		"""從我的最愛中移除課程

		Parameters
		-----------
		course_id: str
			課程代碼(ex: E2-025,請依此格式輸入)
		"""
     
		# check if course_id has correct format
		if course_id is not None and not re.match('[A-Z]([0-9]|[A-Z])-[0-9]{3}',course_id):
			await ctx.reply("課程代碼格式錯誤")
			return

		# check if the course is in the favorite list
		con = sqlite3.connect('cogs/data.db')
		con.row_factory = sqlite3.Row
		db_search = con.execute("SELECT Name FROM COURSES WHERE ID = ?;",(course_id,)).fetchone()
		if db_search is None:
			await ctx.reply("你的最愛中無此課程!")
			return
		con.execute("DELETE FROM FAVORITE WHERE UserID = ? AND CourseID = ?;",(ctx.author.id,course_id))
		con.commit()
		await ctx.reply(f"已將`{course_id}: {db_search['Name']}`移出最愛")
     
async def setup(bot: commands.Bot):
	await bot.add_cog(Courses(bot), guilds=[discord.Object(id=539951635288293397)])