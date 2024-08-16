import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')
BOT_CREATOR_ID = int(os.getenv('BOT_CREATOR_ID'))
PREFIX = os.getenv('PREFIX')

# Define the bot class
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

# Create an instance of the bot
client = MyBot()

# Event handler for when the bot is ready
@client.event
async def on_ready():
    print('Bot is ready!')
    if PREFIX:
        print(f'Loaded prefix: {PREFIX}')
    else:
        print('No prefix loaded.')

# Check if the user has admin permissions
def has_admin_permissions(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# Define the modal for collecting the title and number of rules
class RuleMakerModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create Rules")
        self.title = discord.ui.TextInput(label="Title", placeholder="Enter the title of the rules")
        self.number_of_rules = discord.ui.TextInput(label="Number of Rules", placeholder="Enter the number of rules", style=discord.TextStyle.short)
        self.add_item(self.title)
        self.add_item(self.number_of_rules)

    async def on_submit(self, interaction: discord.Interaction):
        title = self.title.value
        number_of_rules = int(self.number_of_rules.value)
        await ruleMaker(interaction, title, number_of_rules)

# Command to create rules for the server
@client.tree.command(name='rulemaker', description='Create rules for the server')
@app_commands.check(has_admin_permissions)
async def ruleMakerCommand(interaction: discord.Interaction):
    await interaction.response.send_modal(RuleMakerModal())

# Function to handle the rule creation process
async def ruleMaker(interaction: discord.Interaction, title: str, number_of_rules: int):
    try:
        guild = interaction.guild
        if not guild.rules_channel:
            rules_channel = await guild.create_text_channel('rules')
            await rules_channel.edit(topic='Server rules')
            await guild.edit(rules_channel=rules_channel)
        else:
            rules_channel = guild.rules_channel

        rules = []
        await interaction.followup.send(f'Please enter the rules:', ephemeral=True)
        for i in range(number_of_rules):
            await interaction.followup.send(f'Please enter the name for rule {i+1}:', ephemeral=True)
            rule_name = await client.wait_for('message', check=lambda m: m.author == interaction.user)
            await interaction.followup.send(f'Please enter the description for rule {i+1}:', ephemeral=True)
            rule_description = await client.wait_for('message', check=lambda m: m.author == interaction.user)
            rules.append((rule_name.content, rule_description.content))

        embed = discord.Embed(title=title, color=0xffffff)
        for rule_name, rule_description in rules:
            embed.add_field(name=rule_name, value=rule_description, inline=False)

        await rules_channel.send(embed=embed)
        await interaction.followup.send(f'`Rules created in {rules_channel.name}`', ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f'`An error occurred: {e}`', ephemeral=True)

# Command to announce a message in a channel
@client.tree.command(name='announce', description='announce on a channel')
@app_commands.check(has_admin_permissions)
async def announce(interaction: discord.Interaction, channel_reference: str, message: str):
    try:
        if channel_reference.startswith("<#") and channel_reference.endswith(">"):
            channel_id = int(channel_reference[2:-1])
            target_channel = client.get_channel(channel_id)
        else:
            target_channel = discord.utils.get(interaction.guild.channels, name=channel_reference)
        if target_channel:
            await target_channel.send(f'{message}')
            await interaction.response.send_message(
                f'`Announcement sent in {target_channel.name}` {message}')
        else:
            available_channels = ", ".join(c.name for c in interaction.guild.channels)
            await interaction.response.send_message(
                f'`Channel {channel_reference} not found. Available channels: {available_channels}`',
                ephemeral=True)
    except discord.errors.Forbidden:
        await interaction.response.send_message(
            "`You do not have permission to send messages in that channel.`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'`An error occurred: {e}`', ephemeral=True)

# Error handler for the announce command
@announce.error
async def announce_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

# Run the bot
client.run(TOKEN)