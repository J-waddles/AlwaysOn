import discord
from discord.ext import commands, tasks
from discord.ui import Button, view
import json
import os
from discord import Embed

from utils.roles import add_role_to_user, remove_role_from_user
from utils.channels import create_private_channel, delete_private_channel, find_channel_by_name
from utils.queue import enqueue_user, dequeue_user, is_pair_available, get_next_pair, remove_user_from_queue

admin_channel_id = None
connection_channel_id = None 

# Define Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

if os.getenv("token"):
    # Load configuration from environment variables
    TOKEN = os.environ.get("token")
    PREFIX = os.environ.get("PREFIX", "!")  # The "!" is a default value in case PREFIX is not set
    
    # Initialize the bot
    bot = commands.Bot(command_prefix=PREFIX, intents=intents)

else:
    # Load the config file for Test Bot
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Initialize the Test Bot
    bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

@bot.command()
@commands.has_permissions(administrator=True)
async def startnetworking(ctx):
    global admin_channel_id
    admin_channel_id = ctx.channel.id
    await ctx.send(f"Networking bot initiated in this channel: {ctx.channel.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def viewconnections(ctx):
    global connection_channel_id
    connection_channel_id = ctx.channel.id
    await ctx.send(f"Set the connection view channel to {ctx.channel.mention}.")

##Close all ON channels at once

## Close channel of connect

