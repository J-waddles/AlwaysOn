import discord
from discord.ext import commands, tasks
import json
from discord.ui import Button, View
from discord import Embed

from utils.roles import add_role_to_user, remove_role_from_user
from utils.channels import create_private_channel, delete_private_channel, find_channel_by_name
from utils.queue import enqueue_user, dequeue_user, is_pair_available, get_next_pair, remove_user_from_queue

# Define Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Load the config file
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize the bot
bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label='Connect', style=discord.ButtonStyle.secondary, custom_id="connect_button")
    async def connect_button(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        print(type(interaction), interaction)  # For debugging
        print(type(button), button)  # For debugging
    
        guild = interaction.guild  # Notice we are using interaction here
        print(guild)  # For debugging
        
        user = interaction.user
        enqueue_user(user.id)
        
        if is_pair_available():
            user1_id, user2_id = get_next_pair()
            user1 = guild.get_member(user1_id)
            user2 = guild.get_member(user2_id)

            #testing
            print(f"User 1 ID: {user1_id}, User 2 ID: {user2_id}")

            user1 = await guild.fetch_member(user1_id)
            user2 = await guild.fetch_member(user2_id)

            print(f"User 1 Object: {user1}, User 2 Object: {user2}")
            
            channel = await create_private_channel(guild, f'networking-{user1.name}-{user2.name}', user1, user2)
            await add_role_to_user(user1, "Connected", guild)
            await add_role_to_user(user2, "Connected", guild)

            embed = Embed(
                title="Connected",
                description=f"Congratulations!\n\nYou are now connected for networking!",
                color=0xdeffee  
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            

            class ChannelView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=180)

                @discord.ui.button(label='Disconnect', style=discord.ButtonStyle.danger, custom_id="disconnect_channel_button")
                async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    print(type(interaction), interaction)
                    user = interaction.user
                    guild = interaction.guild
                    channel = interaction.channel

                    # Remove roles (if any)
                    await remove_role_from_user(user, "Connected", guild)

                    # Delete the private channel
                    if "networking-" in channel.name:
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
            
            await channel.send(embed=embed, view=ChannelView())
            # await channel.send(f"{user1.mention} and {user2.mention}, you are now connected for networking!", view=ChannelView())
        else:
            embed = Embed(
                title="Queued",
                description="You're in the queue. \nPlease wait for another user to connect with.",
                color=0xdeffee  
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='Disconnect', style=discord.ButtonStyle.danger, custom_id="disconnect_button")
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(type(button), button)
        print(type(interaction), interaction)
        user = interaction.user
        remove_user_from_queue(user.id)
        embed = Embed(
            title="Leaving line",
            description="You've now been removed from the queue. \n\nHope to see you back shortly :)",
            color=0xdeffee  
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    channel = bot.get_channel(1154032057056501791)
    if channel:
        async for message in channel.history(limit=100):  # Fetch last 100 messages
            try:
                await message.delete()
            except:
                pass
        
        embed = Embed(
            title="Connection",
            description="Use the buttons below to connect or disconnect: \n\n Rules:\n1. Provide a positive connection.\n2. Don't share personal or financial information. \n3. Beware of bad actors.\n\n Lets Connect! ",
            color=0xdeffee
        )
        # embed.set_thumbnail(url="https://example.com/your-logo.png")  # Replace with the URL of your logo
        await channel.send(embed=embed, view=MyView())

# Run the bot
bot.run(config['token'])
