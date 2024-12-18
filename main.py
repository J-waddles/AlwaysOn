import json
import os
import discord
from discord.ext import commands
from discord import app_commands, Embed
from db import create_db_connection, initialize_tables
from utils.queue import enqueue_user, dequeue_user, is_pair_available, get_next_pair, remove_user_from_queue
from utils.channels import create_private_channel
import mysql.connector
from mysql.connector import Error

# Define Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

admin_channel_id = None
connection_channel_id = None
connection_category_name = None  # Add a global variable to store the category name

bot = commands.Bot(command_prefix="!", intents=intents)
bot.mydb = None  # Database connection placeholder

if os.getenv("TOKEN"):
    TOKEN = os.environ.get("TOKEN")
    PREFIX = os.environ.get("PREFIX", "!")  # The "!" is a default value in case PREFIX is not set
else:
# Load the config file for Test Bot
    with open('config.json', 'r') as f:
        config = json.load(f)

@bot.event
async def on_guild_join(guild):
    if bot.mydb:
        cursor = bot.mydb.cursor()
        try:
            cursor.execute("""
                INSERT INTO servers (server_id, server_name, active)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE active = TRUE;
            """, (guild.id, guild.name, True))
            bot.mydb.commit()
            print(f"Added server {guild.name} (ID: {guild.id}) to database.")
        except Error as e:
            print(f"Error adding server to database: {e}")

# Slash Command: View Connections
@bot.tree.command(name="viewconnections", description="Set the connection channel and category.")
@app_commands.default_permissions(administrator=True)
async def view_connections(interaction: discord.Interaction):
    if bot.mydb:
        cursor = bot.mydb.cursor()
        try:
            cursor.execute("""
                INSERT INTO channels (channel_id, server_id, channel_name, category_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE channel_name = VALUES(channel_name), category_name = VALUES(category_name);
            """, (interaction.channel.id, interaction.guild.id, interaction.channel.name, interaction.channel.category.name if interaction.channel.category else None))
            bot.mydb.commit()
            await interaction.response.send_message(f"The connection channel has been set to '{interaction.channel.name}' under category '{interaction.channel.category.name}'.", ephemeral=True)
        except Error as e:
            await interaction.response.send_message("Failed to update connection details in the database.", ephemeral=True)
            print(f"Database error in view_connections: {e}")
    else:
        await interaction.response.send_message("Database is not connected.", ephemeral=True)

# Slash Command: Request Pair
@bot.tree.command(name="requestpair", description="Request a pairing with another user.")
async def request_pair(interaction: discord.Interaction):
    enqueue_user(interaction.guild.id, interaction.user.id)
    if is_pair_available(interaction.guild.id):
        user1_id, user2_id = get_next_pair(interaction.guild.id)
        user1 = await interaction.guild.fetch_member(user1_id)
        user2 = await interaction.guild.fetch_member(user2_id)
        channel = await create_private_channel(
            guild=interaction.guild,
            channel_name=f'on-{user1.name}-{user2.name}',
            user1=user1,
            user2=user2,
            category_name=interaction.channel.category.name
        )
        #here
        embed = Embed(
            title="Connected",
            description=f"Congratulations, {user1.mention} and {user2.mention}! You are now connected for networking!",
            color=0x00FF00
        )
        await channel.send(embed=embed)
        await interaction.response.send_message(f"You are now connected in channel {channel.name}.", ephemeral=True)
    else:
        await interaction.response.send_message("You're in the queue. Waiting for another user to connect with.", ephemeral=True)

# Slash Command: Disconnect
@bot.tree.command(name="disconnect", description="Disconnect and delete the private channel.")
async def disconnect(interaction: discord.Interaction):
    channel = interaction.channel
    if channel.name.startswith(("buddy-", "on-")):
        try:
            await channel.delete()
            await interaction.response.send_message("Channel deleted successfully.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to delete this channel.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed to delete channel: {e}", ephemeral=True)
    else:
        await interaction.response.send_message("This is not a connectable channel.", ephemeral=True)

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, custom_id="connect_button")
    async def connect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the 'Start' button to add the user to the queue and manage pairing."""
        guild = interaction.guild
        user = interaction.user

        # Add the user to the server-specific queue
        enqueue_user(guild.id, user.id)

        # Check if a pair is available
        if is_pair_available(guild.id):
            user1_id, user2_id = get_next_pair(guild.id)
            user1 = await guild.fetch_member(user1_id)
            user2 = await guild.fetch_member(user2_id)

            # Create a private channel for the pair
            try:
                category_name = interaction.channel.category.name if interaction.channel.category else None
                channel = await create_private_channel(
                    guild=guild,
                    channel_name=f"on-{user1.name}-{user2.name}",
                    user1=user1,
                    user2=user2,
                    category_name=category_name,
                )

                # Embed for the private channel
                private_embed = Embed(
                    title="Connected!",
                    description=(
                        f"Congratulations, {user1.mention} and {user2.mention}!\n\n"
                        "You are now connected in this private networking channel.\n"
                        "Use this space to connect and collaborate.\n\n"
                        "**Tip:** When you're done, use the 'Disconnect' button below to close this channel."
                    ),
                    color=0x00FF00,
                )

                # Add `ChannelView` to the private channel
                await channel.send(embed=private_embed, view=ChannelView())

                # Notify the interacting user
                await interaction.response.send_message(
                    f"Thank you for getting connected, we have paired you in channel {channel.name}.",
                    ephemeral=True,
                )
            except Exception as e:
                print(f"Error creating private channel: {e}")
                await interaction.response.send_message(
                    "Failed to create a private channel. Please contact an admin.", ephemeral=True
                )
        else:
            # Notify the user they are in the queue
            queue_embed = Embed(
                title="Queued",
                description=(
                    "You're in the queue. Please wait for another user to connect with.\n\n"
                    "**Tip:** Stay active and be ready when paired!"
                ),
                color=0xFFFF00,
            )
            await interaction.response.send_message(embed=queue_embed, ephemeral=True)

    @discord.ui.button(label="Disconnect", style=discord.ButtonStyle.danger, custom_id="disconnect_button")
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the 'Disconnect' button to remove the user from the queue."""
        guild = interaction.guild
        user = interaction.user

        # Remove the user from the server-specific queue
        remove_user_from_queue(guild.id, user.id)

        # Notify the user of successful removal
        embed = Embed(
            title="Disconnected",
            description="You have been removed from the queue. Feel free to join again later!",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Disconnect", style=discord.ButtonStyle.danger, custom_id="disconnect_channel_button")
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the 'Disconnect' button to delete the private channel."""
        user = interaction.user
        channel = interaction.channel

        # Ensure the channel is a private networking channel
        if "on-" in channel.name or "buddy-" in channel.name:
            try:
                await interaction.response.send_message(
                    f"The networking channel '{channel.name}' has been deleted.", ephemeral=True
                )
                await channel.delete()
                
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to delete this channel.", ephemeral=True
                )
            except discord.HTTPException as e:
                await interaction.response.send_message(
                    f"Failed to delete the channel: {e}", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "This command is only valid for networking channels.", ephemeral=True
            )

@bot.tree.command(name="starton", description="Start the networking interface.")
@app_commands.default_permissions(administrator=True)
async def start_on(interaction: discord.Interaction):
    """Initialize the friendly UI Views and start the networking system."""
    # Check if the bot is connected to the database
    if bot.mydb:
        cursor = bot.mydb.cursor()
        try:
            # Insert or update the connection channel and category in the database
            cursor.execute("""
                INSERT INTO channels (channel_id, server_id, channel_name, category_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE channel_name = VALUES(channel_name), category_name = VALUES(category_name);
            """, (interaction.channel.id, interaction.guild.id, interaction.channel.name, interaction.channel.category.name if interaction.channel.category else None))
            bot.mydb.commit()
        except Error as e:
            await interaction.response.send_message("Failed to initialize the networking system in the database.", ephemeral=True)
            print(f"Database error in /starton: {e}")
            return

    # Create the friendly UI Views
    embed = Embed(
        title="1-on-1 Networking",
        description=(
            "Your opportunity to connect with members is about to begin!\n\n"
            "Click **Start** to join the queue. Then wait for a connection with another member looking to network!\n\n"
            "**Rules:**\n"
            "1. Provide a positive connection experience.\n"
            "2. Don't share personal or financial information.\n"
            "3. Beware of bad actors. Admins are here to help if needed.\n\n"
            "Let's Connect!"
        ),
        color=0x00FF00
    )
    view = MyView()  # This view includes the `Start` and `Disconnect` buttons

    # Send the embed with the interactive view
    await interaction.response.send_message(embed=embed, view=view)


async def create_private_channel(guild, channel_name, user1, user2, category_name):
    """Create a private text channel for two users."""
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        user2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
    }

    # Locate or create the category
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        category = await guild.create_category(category_name)

    # Create the private channel
    channel = await guild.create_text_channel(
        name=channel_name, overwrites=overwrites, category=category
    )

    return channel



@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    bot.mydb = create_db_connection()
    if bot.mydb:
        initialize_tables(bot.mydb)
    # Sync commands
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")



# Run the bot
if os.getenv("TOKEN"):
    print("Running in production mode.")
    bot.run(TOKEN)

# a seperate token to test without needing to upload
else:
    print("Running in test mode.")
    bot.run(config['TESTTOKEN'])