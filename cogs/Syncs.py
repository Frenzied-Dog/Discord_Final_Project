import os
import discord
from discord.ext import commands

class Syncs(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.description = "除錯用"
	
	@commands.Cog.listener()
	async def on_ready(self):
		print("Sync Cog loaded")

	@commands.command()
	@commands.has_permissions(administrator=True)
	async def sync(self, ctx: commands.Context) -> None:
		"""同步指令 (管理員專用)"""
		fmt = await ctx.bot.tree.sync(guild=ctx.guild)
		await ctx.send(f'synced {len(fmt)} commands')

	@sync.error
	async def sync_error(self, ctx: commands.Context, error: commands.CommandError):
		if isinstance(error,commands.NotOwner):
			await ctx.reply('此指令僅限機器人擁有者使用!')
		else:
			await ctx.reply(error)
   

async def setup(bot: commands.Bot):
	await bot.add_cog(Syncs(bot), guilds=[discord.Object(id=539951635288293397)])