import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

TOKEN = os.getenv("DISCORD_TOKEN")  # Get token from environment variables

# Flask app to keep the bot alive (e.g., for Uptime Robot)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Selfbot client setup
bot = commands.Bot(command_prefix='!', self_bot=True)
tasks = {}       # Tracks running tasks by channel ID
task_meta = {}   # Stores type and interval info

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

@bot.command()
async def message(ctx, *, args=None):
    await ctx.message.delete()

    if not args:
        usage = "Usage: !message <text>, <channel_id>, <interval_seconds>"
        example = "Example: !message Hello!, 1234567890, 30"
        await ctx.send(f"{usage}\n{example}")
        return

    try:
        msg, chan_id, interval = [x.strip() for x in args.split(',', 2)]
        channel_id = int(chan_id)
        interval = int(interval)
    except Exception as e:
        await ctx.send(f"Error: {e}")
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send("Invalid channel ID.")
        return

    if channel_id in tasks:
        await ctx.send("A loop is already running in that channel.")
        return

    async def send_loop():
        await channel.send(msg)
        while True:
            await asyncio.sleep(interval)
            await channel.send(msg)

    task = asyncio.create_task(send_loop())
    tasks[channel_id] = task
    task_meta[channel_id] = {"type": "message", "interval": interval}
    await ctx.send(f"Started messaging <#{channel_id}> every {interval} seconds.")

@bot.command()
async def forward(ctx, *, args=None):
    await ctx.message.delete()

    if not args:
        usage = "Usage: !forward <message_id>, <channel_id>, <interval_seconds>"
        example = "Example: !forward 112233445566, 1234567890, 60"
        await ctx.send(f"{usage}\n{example}")
        return

    try:
        msg_id_str, chan_id_str, interval_str = [x.strip() for x in args.split(',', 2)]
        message_id = int(msg_id_str)
        channel_id = int(chan_id_str)
        interval = int(interval_str)

        # Get the destination channel where the message will be forwarded
        dest_channel = bot.get_channel(channel_id)
        if not dest_channel:
            await ctx.send("Invalid channel ID.")
            return

        # Fetch the original message to forward
        original_message = await ctx.channel.fetch_message(message_id)

        # Check if the task is already running in the destination channel
        if channel_id in tasks:
            await ctx.send("A forward loop is already running in that channel.")
            return

    except Exception as e:
        await ctx.send(f"Error: {e}")
        return

    async def forward_loop():
        # Create the message content, including the author's name
        content = f"**{original_message.author}** said:\n{original_message.content}"

        # Send the original message's content
        await dest_channel.send(content)

        # If the original message had any attachments, forward them
        for attachment in original_message.attachments:
            await dest_channel.send(attachment.url)

        # If the original message had embeds, forward them as well
        for embed in original_message.embeds:
            await dest_channel.send(embed=embed)

        # Loop to forward the message at the specified interval
        while True:
            await asyncio.sleep(interval)
            await dest_channel.send(content)
            for attachment in original_message.attachments:
                await dest_channel.send(attachment.url)
            for embed in original_message.embeds:
                await dest_channel.send(embed=embed)

    # Create and store the task
    task = asyncio.create_task(forward_loop())
    tasks[channel_id] = task
    task_meta[channel_id] = {"type": "forward", "interval": interval}
    await ctx.send(f"Started forwarding message to <#{channel_id}> every {interval} seconds.")

@bot.command()
async def stop(ctx, channel_id: int):
    await ctx.message.delete()

    task = tasks.get(channel_id)
    if task:
        task.cancel()
        del tasks[channel_id]
        task_meta.pop(channel_id, None)
        await ctx.send(f"Stopped activity in <#{channel_id}>.")
    else:
        await ctx.send("No active task in that channel.")

@bot.command()
async def list(ctx):
    await ctx.message.delete()

    if not tasks:
        await ctx.send("No active tasks.")
        return

    lines = []
    for channel_id in tasks:
        channel = bot.get_channel(channel_id)
        name = channel.name if channel else "Unknown"
        info = task_meta.get(channel_id, {})
        task_type = info.get("type", "unknown")
        interval = info.get("interval", "?")
        lines.append(f"- Channel: <#{channel_id}> ({name}) | Type: `{task_type}` | Every {interval}s")

    await ctx.send("**Active Tasks:**\n" + "\n".join(lines))

# Start Flask thread
Thread(target=run_flask).start()

# Run bot
bot.run(TOKEN)
