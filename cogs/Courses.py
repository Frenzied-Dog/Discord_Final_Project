import re,os,io,asyncio

import discord
from discord import app_commands
from discord.ext import commands

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

class Courses(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "課程系統"

	@commands.Cog.listener()
	async def on_ready(self):
		print("Courses Cog loaded")


	async def build_message(self, web: WebDriver, the_class: list[WebElement]):
		ret: str = ""
		class_name: str = the_class[4].find_element(By.CLASS_NAME,"course_name").text
		teacher: str = the_class[6].text
		time_place: str = the_class[-2].text
		pic = None
		if time_place.endswith("上課時間"):
			time_place = time_place.removesuffix("上課時間").removesuffix("\n")
			the_class[-2].find_element(By.CLASS_NAME,"flex_time").click()
			await asyncio.sleep(1)
			table = web.find_element(By.ID,"show_note_msg").find_element(By.CLASS_NAME,"modal-content").screenshot_as_png
			pic = io.BytesIO(table); pic.seek(0)
			web.find_element(By.ID,"show_note_msg").find_element(By.TAG_NAME,"button").click()

		link: str = the_class[-1].find_element(By.TAG_NAME,"a").get_attribute("href")
		link = "[連結點我]("  + link + ")"
		ret += f"**{class_name}**\n教師: {teacher}\n"

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

		if course_id is not None and not re.match('[A-Z]([0-9]|[A-Z])-[0-9]{3}',course_id):
			await ctx.reply("課程代碼格式錯誤")
			return

		await ctx.defer()
		web = webdriver.Chrome(options=options)
		web.set_window_size(1920, 1030)
		web.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
		web.get('https://course.ncku.edu.tw/index.php?c=qry11215&m=en_query')

		try: WebWait(web, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="cosname"]')))
		except OOT: await ctx.reply("網站逾時"); web.quit(); return

		web.find_element(By.XPATH,'//input[@id="cosname"]').send_keys(name)
		web.find_element(By.XPATH,'//div[@id="main_content"]/div[3]/button').click()

		try: WebWait(web, 10).until(EC.invisibility_of_element_located((By.XPATH, '/html/body/div[1]/div')))
		except OOT: await ctx.reply("網站逾時"); web.quit(); return

		class_lists = web.find_element(By.XPATH,'//div[@id="result"]/table/tbody').find_elements(By.TAG_NAME,"tr")
		if len(class_lists) == 0:
			await ctx.reply("查無資料")
			web.quit()
			return

		count: int = 0
		pics: list[discord.File] = []
		ret: str = ""
		for i in class_lists:
			each_class = i.find_elements(By.TAG_NAME,"td")
			id = each_class[1].find_element(By.CLASS_NAME,"dept_seq").text
			if course_id is not None:
				if course_id == id:
					value = await self.build_message(web, each_class)
					ret += value[0]
					if value[1] is not None: pics.append(value[1])
				else: continue
			else:
				value = await self.build_message(web, each_class)
				ret += value[0]
				if value[1] is not None: pics.append(value[1])
    
				count += 1
				if count >= 5: break
		else:
			if count == 0: ret = "找不到指定的課程代碼!"
		await ctx.reply(ret,files=pics)
		web.quit()



async def setup(bot: commands.Bot):
	await bot.add_cog(Courses(bot), guilds=[discord.Object(id=539951635288293397)])