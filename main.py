import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

TOKEN = os.getenv("DISCORD_TOKEN")  # Set your token in environment variables

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

bot = commands.Bot(command_prefix='!', self_bot=True)
tasks = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

@bot.command()
async def message(ctx, *, args=None):
    await ctx.message.delete()
    if not args:
        await ctx.send("Usage: `!message <text>, <channel_id>, <interval_seconds>`")
        return

    try:
        msg_text, channel_id, interval = map(str.strip, args.split(','))
        channel = bot.get_channel(int(channel_id))
        interval = int(interval)
    except Exception:
        await ctx.send("Error: invalid arguments. Format: `!message Hello, 1234567890, 60`")
        return

    if not channel:
        await ctx.send("Invalid channel ID.")
        return

    if channel.id in tasks:
        await ctx.send("A loop is already running in that channel.")
        return

    async def send_loop():
        await channel.send(msg_text)
        while True:
            await asyncio.sleep(interval)
            await channel.send(msg_text)

    task = asyncio.create_task(send_loop())
    tasks[channel.id] = task
    await ctx.send(f"Started sending messages to <#{channel.id}> every {interval}s.")

@bot.command()
async def stop(ctx, channel_id: int):
    await ctx.message.delete()
    task = tasks.get(channel_id)
    if task:
        task.cancel()
        del tasks[channel_id]
        await ctx.send(f"Stopped messages in <#{channel_id}>.")
    else:
        await ctx.send("No active loop found for that channel.")

@bot.command()
async def list(ctx):
    await ctx.message.delete()
    if not tasks:
        await ctx.send("No active loops.")
        return
    msg = "**Active message loops:**\n"
    for cid in tasks:
        ch = bot.get_channel(cid)
        msg += f"- Channel: <#{cid}> ({'Unknown' if not ch else ch.name})\n"
    await ctx.send(msg)

@bot.command()
async def forward(ctx, *, args=None):
    await ctx.message.delete()
    if not args:
        await ctx.send("Usage: `!forward <message_id>, <channel_id>, <interval_seconds>`")
        return

    try:
        msg_id_str, channel_id_str, interval_str = map(str.strip, args.split(','))
        msg_id = int(msg_id_str)
        channel_id = int(channel_id_str)
        interval = int(interval_str)

        source_channel = ctx.channel
        dest_channel = bot.get_channel(channel_id)
        if not dest_channel:
            await ctx.send("Invalid destination channel.")
            return

        if channel_id in tasks:
            await ctx.send("A forward loop is already running in that channel.")
            return

        message = await source_channel.fetch_message(msg_id)
        if not message:
            await ctx.send("Could not fetch message.")
            return

        author = message.author
        content = message.content
        attachments = message.attachments

    except Exception as e:
        await ctx.send(f"Error: {e}")
        return

    async def forward_loop():
        while True:
            try:
                embed = discord.Embed(description=content, color=0x2F3136)
                embed.set_author(name=f"Forwarded from {author}", icon_url=author.display_avatar.url)
                files = []
                for a in attachments:
                    f = await a.to_file()
                    files.append(f)
                await dest_channel.send(embed=embed, files=files)
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Error forwarding message: {e}")
                break

    task = asyncio.create_task(forward_loop())
    tasks[channel_id] = task
    await ctx.send(f"Started forwarding message from <#{ctx.channel.id}> to <#{channel_id}> every {interval}s.")

# Start Flask thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

# Run bot
bot.run(TOKEN)
