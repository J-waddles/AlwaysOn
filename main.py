import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
from discord import Embed

from utils.roles import add_role_to_user, remove_role_from_user
from utils.channels import create_private_channel, delete_private_channel, find_channel_by_name
from utils.queue import enqueue_user, dequeue_user, is_pair_available, get_next_pair, remove_user_from_queue

# Define Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

admin_channel_id = None
connection_channel_id = None
connection_category_name = None  # Add a global variable to store the category name

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

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.green, custom_id="connect_button")
    async def connect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        
        user = interaction.user
        enqueue_user(user.id)
        
        if is_pair_available():
            user1_id, user2_id = get_next_pair()
            user1 = await guild.fetch_member(user1_id)
            user2 = await guild.fetch_member(user2_id)
            
            # Use the stored category name
            global connection_category_name
            if connection_category_name:
                channel = await create_private_channel(guild, f'on-{user1.name}-{user2.name}', user1, user2, connection_category_name)
                await add_role_to_user(user1, "Connected", guild)
                await add_role_to_user(user2, "Connected", guild)
                embed = Embed(
                    title="Connected",
                    description=f"Congratulations, You are now connected! \n\nTime to network!",
                    color=0xdeffee  
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                embed = Embed(
                    title="Connected",
                    description=f"Congratulations {user1.mention} and {user2.mention}!\n\nYou are now connected for networking!\n\n When finished please type !disconnect to delete this channel.",
                    color=0xdeffee  
                )
                await channel.send(embed=embed)
            else:
                await interaction.response.send_message("Connection category is not set. Please set it using !viewconnections command.", ephemeral=True)
        else:
            embed = Embed(
                title="Queued",
                description="You're in the queue. \nPlease wait for another user to connect with.",
                color=0xdeffee  
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        if connection_channel_id:
            channel = bot.get_channel(connection_channel_id)
            if channel:
                await channel.send(f"{user1.mention} and {user2.mention} recently connected!")
class ChannelView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
            # @discord.ui.button(label='Disconnect', style=discord.ButtonStyle.danger, custom_id="disconnect_channel_button")
            # async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            #     print(type(interaction), interaction)
            #     user = interaction.user
            #     guild = interaction.guild
            #     channel = interaction.channel
            #     # Remove roles (if any)
            #     await remove_role_from_user(user, "Connected", guild)
            #     # Delete the private channel
            #     if "on-" in channel.name:
            #         await delete_private_channel(channel)
                    
                
            #     embed = Embed(
            #         title="Disconnected",
            #         description="Thank you for connecting!",
            #         color=0xdeffee  
            #     )
                
            #     await interaction.response.send_message(embed=embed, ephemeral=True)

            embed = Embed(
                title="Connected",
                description=f"Congratulations {user1.mention} and {user2.mention}!\n\nYou are now connected for networking!\n\n When finished please type !disconnect to delete this channel.",
                color=0xdeffee  
            )

            # await channel.send(embed=embed, view=ChannelView())
            await channel.send(embed=embed)
            # await channel.send(f"{user1.mention} and {user2.mention}, you are now connected for networking!", view=ChannelView())
        else:
            embed = Embed(
                title="Queued",
                description="You're in the queue. \nPlease wait for another user to connect with.",
                color=0xdeffee  
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        if connection_channel_id:
                channel = bot.get_channel(connection_channel_id)
                if channel:
                    await channel.send(f"{user1.mention} and {user2.mention} recently connected!")

    @discord.ui.button(label='Disconnect', style=discord.ButtonStyle.danger, custom_id="disconnect_button")
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        remove_user_from_queue(user.id)
        embed = Embed(
            title="Leaving line",
            description="You've now been removed from the queue. \n\nHope to see you back shortly :)",
            color=0xdeffee  
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="disconnect")
async def disconnect(ctx):
    channel = ctx.channel
    await delete_private_channel(channel)

@bot.event
async def on_message(message):
    global admin_channel_id
    global connection_channel_id
    global connection_category_name
    
    if message.author == bot.user:
        return
    
    if message.content == "!starton":
        if message.author.guild_permissions.administrator:
            admin_channel_id = message.channel.id
            await message.channel.send("This channel is now set as the admin channel for networking.")
            
            if admin_channel_id:
                channel = bot.get_channel(admin_channel_id)
                if channel:
                    async for message in channel.history(limit=100):
                        try:
                            await message.delete()
                        except:
                            pass
                    
                    embed = Embed(
                        title="1 on 1 Networking",
                        description="Your opportunity to connect with members is about to begin!\n\nClick Start. Then please wait for a connection with a random user also looking to Network! \n\nRules:\n1. Provide a positive connection expereience.\n2. Don't share personal or financial information. \n3. Beware of bad actors. (admin is always here to ping)\n\n Let's Connect! ",
                        color=0xdeffee
                    )
                    await channel.send(embed=embed, view=MyView())
        else:
            await message.channel.send("You do not have the permissions to run this command.")
    
    if message.content.startswith('!viewconnections'):
        admin_role = discord.utils.get(message.guild.roles, name="Admin")
        if admin_role in message.author.roles:
            connection_channel_id = message.channel.id
            connection_category_name = message.channel.category.name if message.channel.category else None
            await message.channel.send(f"The connection channel has been set to {connection_category_name}.")
        else:
            await message.channel.send("You don't have the permissions to set the connection channel.")
    
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    bot.add_view(MyView())

if os.getenv("token"):
    bot.run(TOKEN)
else:
    bot.run(config['testToken'])
