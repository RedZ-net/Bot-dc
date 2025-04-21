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

        msg_text = msg_parts[0].strip()  # Text that will be sent
        channel_id = int(msg_parts[1].strip())  # Target channel ID
        interval = int(msg_parts[2].strip())  # Interval between sending the message

    except ValueError as e:
        await ctx.send(f"Error: {e}")
        return
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")
        return

    # Get the channel
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send("Invalid channel ID.")
        return

    if channel_id in tasks:
        await ctx.send("A message loop is already running in that channel.")
        return

    # Send the first message immediately
    await channel.send(msg_text)

    # Define the repeating task
    async def send_repeating():
        while True:
            await asyncio.sleep(interval)
            await channel.send(msg_text)

    # Create and store the task
    task = asyncio.create_task(send_repeating())
    tasks[channel_id] = task
    await ctx.send(f"Started sending messages to <#{channel_id}> every {interval} seconds.")
