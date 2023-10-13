import discord
from discord import PermissionOverwrite

async def create_private_channel(guild, channel_name, user1, user2):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user1: discord.PermissionOverwrite(read_messages=True),
        user2: discord.PermissionOverwrite(read_messages=True)
    }

    overwrites = {
        guild.default_role: PermissionOverwrite(read_messages=False),
        user1: PermissionOverwrite(read_messages=True),
        user2: PermissionOverwrite(read_messages=True),
        guild.me: PermissionOverwrite(read_messages=True, send_messages=True)  # This line gives the bot permission to read and send messages
    }
    #change category
    category = discord.utils.get(guild.categories, name="╭━━━🖥 Connections 🖥━━━╮")

    # If the category does not exist, create it
    if category is None:
        category = await guild.create_category("╭━━━🖥 Connections 🖥━━━╮")

    channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category
    )
    
    # channel = await guild.create_text_channel('channel_name', overwrites=overwrites)

    return channel

async def delete_private_channel(channel):
    await channel.delete()

async def find_channel_by_name(guild, channel_name):
    for channel in guild.channels:
        if channel.name == channel_name:
            return channel
    return None

