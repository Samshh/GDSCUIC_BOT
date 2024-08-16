import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from discord import ui
from discord.ui import Modal, TextInput

load_dotenv()
TOKEN = os.getenv('TOKEN')
BOT_CREATOR_ID = int(os.getenv('BOT_CREATOR_ID'))
PREFIX = os.getenv('PREFIX')

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

client = MyBot()

@client.event
async def on_ready():
    print('Bot is ready!')
    if PREFIX:
        print(f'Loaded prefix: {PREFIX}')
    else:
        print('No prefix loaded.')
    await update_presence()

def has_admin_permissions(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

@client.event
async def on_member_join(member):
    print(f'{member} has joined the server {member.guild.name}!')
    await update_presence()

async def update_presence():
    if client.is_ready():
        total_member_count = sum(guild.member_count for guild in client.guilds if guild.member_count)
        activity = discord.Activity(name=f"over {total_member_count} Developers!", type=discord.ActivityType.watching)
        await client.change_presence(activity=activity)
        print('Bot presence updated!')
    else:
        print('Bot not ready, presence update skipped.')

class RuleMakerModal(ui.Modal, title="Create Rules"):
    rule_title = ui.TextInput(label="Title", placeholder="Enter the title of the rules")
    number_of_rules = ui.TextInput(label="Number of Rules", placeholder="Enter the number of rules (max 100)", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        title = self.rule_title.value
        number_of_rules = min(int(self.number_of_rules.value), 100)
        await ruleMaker(interaction, title, number_of_rules)

@client.tree.command(name='rulemaker', description='Create rules for the server')
@app_commands.check(has_admin_permissions)
async def ruleMakerCommand(interaction: discord.Interaction):
    modal = RuleMakerModal()
    await interaction.response.send_modal(modal)

async def ruleMaker(interaction: discord.Interaction, title: str, number_of_rules: int):
    try:
        await interaction.response.send_message("Let's create the rules. I'll ask for each rule one by one.", ephemeral=True)
        
        rules = []
        for i in range(number_of_rules):
            await interaction.followup.send(f"Enter the name for rule {i+1}:", ephemeral=True)
            rule_name_msg = await client.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == interaction.channel, timeout=300)
            
            await interaction.followup.send(f"Enter the description for rule {i+1}:", ephemeral=True)
            rule_desc_msg = await client.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == interaction.channel, timeout=300)
            
            rules.append((rule_name_msg.content, rule_desc_msg.content))

        guild = interaction.guild
        if not guild.rules_channel:
            rules_channel = await guild.create_text_channel('rules')
            await rules_channel.edit(topic='Server rules')
            await guild.edit(rules_channel=rules_channel)
        else:
            rules_channel = guild.rules_channel

        embed = discord.Embed(title=title, color=0xffffff)
        for rule_name, rule_description in rules:
            embed.add_field(name=rule_name, value=rule_description, inline=False)

        gif_url = "https://media.discordapp.net/attachments/1273845440219185202/1273867017622917210/20240816_125225.gif?ex=66c02c9c&is=66bedb1c&hm=62855b107f2cf4f1d731da8cccc693b4a018bccc12a8e06448c940e6b11c39c9&="
        embed.set_image(url=gif_url)

        await rules_channel.send(embed=embed)
        await interaction.followup.send(f'Rules created in {rules_channel.name}', ephemeral=True)
    
    except asyncio.TimeoutError:
        await interaction.followup.send("You took too long to respond. Please try again.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f'An error occurred: {str(e)}', ephemeral=True)

class AnnouncementModal(Modal, title="Make an Announcement"):
    channel_reference = TextInput(label="Channel", placeholder="Enter channel name or #channel-mention")
    announcement_text = TextInput(label="Announcement", style=discord.TextStyle.paragraph, placeholder="Enter your announcement here")

    async def on_submit(self, interaction: discord.Interaction):
        await announce_message(interaction, self.channel_reference.value, self.announcement_text.value)

@client.tree.command(name='announce', description='Announce a message in a channel')
@app_commands.check(has_admin_permissions)
async def announce_command(interaction: discord.Interaction):
    await interaction.response.send_modal(AnnouncementModal())

async def announce_message(interaction: discord.Interaction, channel_reference: str, message: str):
    try:
        if channel_reference.startswith("<#") and channel_reference.endswith(">"):
            channel_id = int(channel_reference[2:-1])
            target_channel = interaction.guild.get_channel(channel_id)
        else:
            target_channel = discord.utils.get(interaction.guild.channels, name=channel_reference)
        
        if target_channel:
            await target_channel.send(message)
            await interaction.response.send_message(
                f'Announcement sent in {target_channel.mention}\n\nMessage: {message}',
                ephemeral=True
            )
        else:
            available_channels = ", ".join(c.name for c in interaction.guild.text_channels)
            await interaction.response.send_message(
                f'Channel "{channel_reference}" not found. Available text channels: {available_channels}',
                ephemeral=True
            )
    except discord.errors.Forbidden:
        await interaction.response.send_message(
            "You do not have permission to send messages in that channel.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f'An error occurred: {str(e)}', ephemeral=True)

client.run(TOKEN)