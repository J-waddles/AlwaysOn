import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
import json
import os
from discord import Embed
import re  # Regular expressions module
from utils import channels

CHANNEL_LIMIT = 7  # Maximum number of private channels a user can create
# import asyncio

from utils.queue import (enqueue_user, dequeue_user, is_pair_available, get_next_pair, 
                         add_request, is_request_pending, get_requester, remove_request)
from utils.roles import add_role_to_user, remove_role_from_user
from utils.channels import create_private_channel, delete_private_channel, find_channel_by_name, user_channel_count, create_personal_channel, close_personal_channel




# Define Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

admin_channel_id = None
connection_channel_id = None 

# Load the env
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

    @discord.ui.button(label='Create Private Channel', style=discord.ButtonStyle.primary, custom_id='create_personal_channel')
    async def create_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user has reached the limit of created channels
        user= interaction.user
        if user_channel_count.get(user.id, 0) >= CHANNEL_LIMIT:
            await interaction.response.send_message("You have reached the maximum number of private channels allowed.", ephemeral=True)
            return

        # Prompt for channel name
        modal = ChannelNameModal(title="Enter Channel Name")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Connect', style=discord.ButtonStyle.secondary, custom_id="connect_button")
    async def connect_button(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        guild = interaction.guild  # Notice we are using interaction here


        
        user = interaction.user
        enqueue_user(user.id)
        
        if is_pair_available():
            user1_id, user2_id = get_next_pair()
            user1 = guild.get_member(user1_id)
            user2 = guild.get_member(user2_id)
 

            user1 = await guild.fetch_member(user1_id)
            user2 = await guild.fetch_member(user2_id)

            
            channel = await create_private_channel(guild, f'on-{user1.name}-{user2.name}', user1, user2)
            await add_role_to_user(user1, "Connected", guild)
            await add_role_to_user(user2, "Connected", guild)

            embed = Embed(
                title="Connected",
                description=f"Congratulations, You are now connected! \n\nTime to network!",
                color=0xdeffee  
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        
            class ChannelView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60*60*24)

                @discord.ui.button(label='Disconnect', style=discord.ButtonStyle.danger, custom_id="disconnect_channel_button")
                async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    print(type(interaction), interaction)
                    user = interaction.user
                    guild = interaction.guild
                    channel = interaction.channel

                    # Remove roles (if any)
                    await remove_role_from_user(user, "Connected", guild)

                    # Delete the private channel
                    if "on-" in channel.name:
                        await delete_private_channel(channel)
                        
                    
                    embed = Embed(
                        title="Disconnected",
                        description="Thank you for connecting!",
                        color=0xdeffee  
                    )
                    
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            embed = Embed(
                title="Connected",
                description=f"Congratulations {user1.mention} and {user2.mention}!\n\nYou are now connected for networking!\n\n When finished please hit 'Disconnect'",
                color=0xdeffee  
            )
            # embed.set_thumbnail(url="https://example.com/your-logo.png")  # Replace with the URL of your logo

            await channel.send(embed=embed, view=ChannelView())
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
        print(type(button), button)
        print(type(interaction), interaction)
        user = interaction.user
        dequeue_user()
        embed = Embed(
            title="Leaving line",
            description="You've now been removed from the queue. \n\nHope to see you back shortly :)",
            color=0xdeffee  
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class ChannelNameModal(Modal):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.add_item(TextInput(label='Channel Name', placeholder='Enter your channel name here'))

    async def on_submit(self, interaction: discord.Interaction):
        channel_name = self.children[0].value  # Get the entered channel name
        await create_personal_channel(interaction.guild, channel_name, interaction.user)

        # Update the user_channel_count
        user_channel_count[interaction.user.id] = user_channel_count.get(interaction.user.id, 0) + 1

        await interaction.response.send_message(f"Private channel '{channel_name}' created successfully.", ephemeral=True)

@bot.command(name='invite')
async def invite_user(ctx, member: discord.Member):
    try:
        connection_channel = bot.get_channel(connection_channel_id)
        if connection_channel is None:
            await ctx.send("Connection channel not found.")
            return

        if not ctx.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You don't have permissions to invite users in this channel.")
            return

        view = InviteView(connection_channel_id, ctx.author.id, member.id)
        await connection_channel.send(f"{member.mention}, you have been invited to join {ctx.channel.mention} by {ctx.author.mention}.", view=view)
        await ctx.send("Invitation sent.")
    except Exception as e:
        print(f"An error occurred: {e}")
        await ctx.send("An error occurred while sending the invitation.")




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
@bot.command(name="disconnect")
async def disconnect(ctx):
    user = ctx.author
    guild = ctx.guild
    channel = ctx.channel


    # Check if command is invoked in the bot's designated channel or a networking channel
    # Change bot channel
    if ctx.channel.name != "on-" not in ctx.channel.name:
        await ctx.send("This command can only be used in the designated bot channel or your current networking channel.")
        return
    

    # Remove roles (if any)
    await remove_role_from_user(user, "Connected", guild)

    # Delete the private channel
    if "on-" in channel.name:
        await ctx.send("You've been disconnected.")
        await delete_private_channel(channel)
    
    else:
        await ctx.send("You're not in a networking channel.")

class InviteView(discord.ui.View):
    def __init__(self, channel_id, inviter_id, invitee_id):
        super().__init__()
        self.channel_id = channel_id
        self.inviter_id = inviter_id
        self.invitee_id = invitee_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.invitee_id:
            await interaction.response.send_message("You're not the user invited to this channel.", ephemeral=True)
            return

        # Logic to add the user to the channel
        channel = bot.get_channel(self.channel_id)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        await interaction.response.send_message(f"You have joined {channel.mention}", ephemeral=True)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Similar checks and logic for declining the invitation
        if interaction.user.id != self.invitee_id:
            await interaction.response.send_message("You're not the user invited to this channel.", ephemeral=True)
            return

        # Send a message or notify the inviter that the invitation was declined
        await interaction.response.send_message("You have declined the invitation.", ephemeral=True)


@bot.event
async def on_message(message):
    global admin_channel_id  # Declare the variable as global so you can modify it
    global connection_channel_id

    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Necessary to allow commands to be processed
    await bot.process_commands(message)

    # Check if the message is the command you're looking for
    if message.content == "!starton":
        
        # Check if the author has admin privileges
        if message.author.guild_permissions.administrator:
            
            # Store the channel ID in the global variable
            admin_channel_id = message.channel.id
            
            # Send a confirmation message
            await message.channel.send("This channel is now set as the admin channel for networking.")
            
            if admin_channel_id:
                channel = bot.get_channel(admin_channel_id)
            
                if channel:
                    async for msg in channel.history(limit=100):  # Fetch last 100 messages
                        try:
                            await msg.delete()
                        except:
                            pass
                    
                    embed = Embed(
                        title="1 on 1 Networking",
                        description="Use the buttons below to Connect (queue) or Disconnect (dequeue).\n Then wait for a connection with a random user also looking to network: \n\n Rules:\n1. Provide a positive connection.\n2. Don't share personal or financial information. \n3. Beware of bad actors.\n\n Let's Connect! ",
                        color=0xdeffee
                    )
                    # Send the embed with MyView and RequestView
                    await channel.send(embed=embed, view=MyView())
        else:
            await message.channel.send("You do not have the permissions to run this command.")
    
    if message.content.startswith('!viewconnections'):
        admin_role = discord.utils.get(message.guild.roles, name="Admin")  # Replace with your actual admin role name
        if admin_role in message.author.roles:
            global connection_channel_id
            connection_channel_id = message.channel.id
            await message.channel.send(f"The connection channel has been set.")
        else:
            await message.channel.send("You don't have the permissions to set the connection channel.")





@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    global admin_channel_id  # Declare the variable as global so you can read it




# Run the bot
if os.getenv("token"):
    bot.run(TOKEN)

else:
    bot.run(config['testToken'])