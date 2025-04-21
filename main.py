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
        usage = "Usage: !message <text>, <channel_id>, <interval_seconds>"
        example = "Example: !message Hello!, 1234567890, 60"
        await ctx.send(f"{usage}\n{example}")
        return

    try:
        msg_parts = args.split(',')
        if len(msg_parts) != 3:
            raise ValueError("Incorrect format")

        msg_text = msg_parts[0].strip()
        channel_id = int(msg_parts[1].strip())
        interval = int(msg_parts[2].strip())

    except ValueError as e:
        await ctx.send(f"Error: {e}")
        return
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send("Invalid channel ID.")
        return

    if channel_id in tasks:
        await ctx.send("A message loop is already running in that channel.")
        return

    # Wrap message in triple backticks to prevent Markdown issues
    safe_msg = f"```{msg_text}```"

    async def send_repeating():
        await channel.send(safe_msg)
        while True:
            await asyncio.sleep(interval)
            await channel.send(safe_msg)

    task = asyncio.create_task(send_repeating())
    tasks[channel_id] = task
    await ctx.send(f"Started sending messages to <#{channel_id}> every {interval} seconds.")

@bot.command()
async def stop(ctx, channel_id: int):
    await ctx.message.delete()

    task = tasks.get(channel_id)
    if task:
        task.cancel()
        del tasks[channel_id]
        await ctx.send(f"Stopped messages in <#{channel_id}>.")
    else:
        await ctx.send("No active message loop found for that channel.")

flask_thread = Thread(target=run_flask)
flask_thread.start()

bot.run(TOKEN)
