import discord
from discord import PermissionOverwrite

user_channel_count = {}  # Global dictionary to track user channel counts

async def create_personal_channel(guild, channel_name, user):
    # Existing logic for channel creation
    overwrites = {
        guild.default_role: PermissionOverwrite(read_messages=False),
        user: PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True ),
        guild.me: PermissionOverwrite(read_messages=True)
    }

    category = discord.utils.get(guild.categories, name="╭━━━🖥 Connections 🖥━━━╮")

    if category is None:
        category = await guild.create_category("╭━━━🖥 Connections 🖥━━━╮")

    channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

    # Update channel count
    user_channel_count[user.id] = user_channel_count.get(user.id, 0) + 1

    channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category
    )
    
    # channel = await guild.create_text_channel('channel_name', overwrites=overwrites)

    return channel

async def close_personal_channel(user, channel):
    # Logic to close the channel
    await channel.delete()

    # Update channel count
    if user.id in user_channel_count:
        user_channel_count[user.id] = max(0, user_channel_count[user.id] - 1)

async def create_private_channel(guild, channel_name, user1, user2):

    overwrites = {
        guild.default_role: PermissionOverwrite(read_messages=False),
        user1: PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        user2: PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        guild.me: PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)  # This line gives the bot permission to read and send messages
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


