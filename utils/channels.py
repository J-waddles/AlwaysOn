import discord
from discord import PermissionOverwrite
from main import connection_category_name

async def create_private_channel(guild, channel_name, user1, user2):

    overwrites = {
        guild.default_role: PermissionOverwrite(read_messages=False),
        user1: PermissionOverwrite(read_messages=True, send_messages=True),
        user2: PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)  # This line gives the bot permission to read and send messages
    }
    #change category
    # Use the connection_category_name variable when creating the channel
    category = discord.utils.get(guild.categories, name=connection_category_name)
    if category is None:
        # Create the category if it doesn't exist
        category = await guild.create_category(connection_category_name)

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

