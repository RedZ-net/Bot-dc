import discord
from discord.ext import commands
import os
import asyncio
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

TOKEN = os.getenv("DISCORD_TOKEN")

# Create intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

# Create bot with intents
bot = commands.Bot(command_prefix="!", self_bot=True, intents=intents)

tasks = {}  # Dictionary to track running tasks by channel_id

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

# Adding simple HTTP server for Uptime Robot
def run_http_server():
    handler = SimpleHTTPRequestHandler
    with TCPServer(("", 8080), handler) as httpd:
        print("HTTP server running on port 8080...")
        httpd.serve_forever()

# Start the HTTP server in a separate thread
async def start_http_server():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_http_server)

# Start both bot and HTTP server
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    # Start the HTTP server after the bot is ready
    asyncio.create_task(start_http_server())

@bot.command()
async def message(ctx, *, args=None):
    await ctx.message.delete()

    if not args:
        usage = "Usage: !message <text>, <channel_id>, <interval_seconds>"
        example = "Example: !message Hello everyone!, 123456789, 60"
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

    # Define the repeating task
    async def send_repeating():
        await channel.send(msg_text)
        while True:
            await asyncio.sleep(interval)
            await channel.send(msg_text)

    # Create and store the task
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

bot.run(TOKEN)
