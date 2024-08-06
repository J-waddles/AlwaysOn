import discord
from discord import PermissionOverwrite

async def create_private_channel(guild, channel_name, user1, user2, category_name):
    overwrites = {
        guild.default_role: PermissionOverwrite(read_messages=False),
        user1: PermissionOverwrite(read_messages=True, send_messages=True),
        user2: PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }
    
    # Use the dynamic category name
    category = discord.utils.get(guild.categories, name=category_name)
    
    if category is None:
        category = await guild.create_category(category_name)
    
    channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category
    )
    
    return channel

async def delete_private_channel(channel):
    await channel.delete()

async def find_channel_by_name(guild, channel_name):
    for channel in guild.channels:
        if channel.name == channel_name:
            return channel
    return None
