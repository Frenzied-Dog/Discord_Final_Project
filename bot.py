import os
import asyncio
from dotenv import load_dotenv

import discord
from discord.ext import commands

import sqlite3

load_dotenv()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "%", intents = intents, application_id=os.getenv("APP_ID"), \
				   activity = discord.Activity(name="森森鈴蘭", type=discord.ActivityType.watching), state="https://www.youtube.com/@lilylinglan")


# 當機器人完成啟動時
@bot.event
async def on_ready():
	print(f"目前登入身份 --> {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx: commands.context, extension: str):
	"""載入指令程式檔案 (管理員專用)"""
	await bot.load_extension(f"cogs.{extension}")
	await ctx.reply(f"Loaded {extension} done.")


@bot.command()
@commands.has_permissions(administrator=True)
async def unload(ctx: commands.Context, extension: str):
	"""卸載指令檔案 (管理員專用)"""
	await bot.unload_extension(f"cogs.{extension}")
	await ctx.reply(f"UnLoaded {extension} done.")


@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx: commands.Context, extension: str):
	"""重新載入程式檔案 (管理員專用)"""
	await bot.reload_extension(f"cogs.{extension}")
	await ctx.reply(f"ReLoaded {extension} done.")


@unload.error
@load.error
@reload.error
async def loading_error(ctx: commands.Context, error: commands.CommandError):
	print(error)
	if isinstance(error,commands.MissingPermissions):
		await ctx.reply('你沒有權限使用此指令!')
	else:
		await ctx.reply(error)

# 一開始bot開機需載入全部程式檔案
async def load_extensions():
	for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
	async with bot:
		await load_extensions()
		await bot.start(os.getenv("TOKEN"))

asyncio.run(main())