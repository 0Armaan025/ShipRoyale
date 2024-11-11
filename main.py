import discord
from discord.ext import commands, tasks
import random
import asyncio
from dotenv import load_dotenv
import os
import json

load_dotenv()

GUILD_ID = 0  # Replace with your actual guild ID

class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.cat_spawned = False
        self.channel_ids = []

    async def on_ready(self):
        print(f'Logged on as: {self.user}')

        # Ensure the bot is in at least one guild and check text channels
        if not bot.guilds:
            print("Bot is not in any guild.")
            return

        # Iterate through all the guilds the bot is part of
        for guild in bot.guilds:
            if guild.text_channels:
                # Get the channel IDs from the text channels in this guild
                self.channel_ids = [channel.id for channel in guild.text_channels]
                print(f"Available channels in guild '{guild.name}': {self.channel_ids}")
                break  # Stop after the first guild with text channels is found

        # Check if we found any channels to spawn the cat
        if not self.channel_ids:
            print("No channels available for spawning the ship.")
            return

        # Start the cat spawn loop
        self.cat_spawn_loop.start()

    @tasks.loop(seconds=60)
    async def cat_spawn_loop(self):
        
        if not self.cat_spawned and self.channel_ids:
            spawn_delay = random.randint(0, 1)
            await asyncio.sleep(spawn_delay)

            
            if not self.cat_spawned:
                self.cat_spawned = True
                cat_emoji = "🐱"
                channel_id = random.choice(self.channel_ids) 
                channel = self.get_channel(channel_id)
                if channel:
                    print(f"Spawning ship in channel {channel_id}")
                    await spawn_ship(channel.id)  
                else:
                    print(f"Failed to get channel {channel_id}")
            else:
                print("Cat already spawned, skipping spawn.")


bot = MyBot(command_prefix='$', intents=discord.Intents.all())

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

async def spawn_ship(channel_id: int):
    print(f"Spawning ship in channel {channel_id}")  # Debugging line

    # Load the ship data from the JSON file
    with open('ships.json', 'r') as file:
        ships = json.load(file)

    random_ship = random.choice(ships)

    # Create an embed to show the ship details
    embed = discord.Embed(
        title="Ship Details", 
        color=discord.Color.orange(),
        description=f"{random_ship.get('ship_description', 'No description available')}"
    )

    # Helper function to format the field data
    def format_field(field_data):
        if not field_data:
            return "No data available"

        formatted_data = []
        for item in field_data:
            name = item.get('name', item.get('stat_name', item.get('module_name', item.get('defense_name', item.get('weapon_name', 'Unknown')))))
            value = item.get('value', item.get('stat_value', 'N/A'))
            formatted_data.append(f"{name}: {value}")
        return "\n".join(formatted_data)

    # Format and add fields to the embed
    stats_str = format_field(random_ship.get('ship_stats', []))
    weapons_str = format_field(random_ship.get('ship_weapons', []))
    modules_str = format_field(random_ship.get('ship_modules', []))
    defense_str = format_field(random_ship.get('ship_defense_skills', []))
    
    embed.add_field(name="Name", value=random_ship.get("ship_name", "Unknown"), inline=False)
    embed.add_field(name="Type", value=random_ship.get("ship_type", "Unknown"), inline=False)
    embed.add_field(name="Stats", value=stats_str, inline=False)
    embed.add_field(name="Weapons", value=weapons_str, inline=False)
    embed.add_field(name="Modules", value=modules_str, inline=False)
    embed.add_field(name="Defense skills", value=defense_str, inline=False)

    # Handle the ship image file
    file_path = f"ship_images/{random_ship.get('ship_image', '')}"

    if os.path.exists(file_path):
        file = discord.File(file_path, filename=random_ship['ship_image'])
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(file=file, embed=embed)
        else:
            print(f"Channel with ID {channel_id} not found.")
    else:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
        else:
            print(f"Channel with ID {channel_id} not found.")

@bot.command()
async def catch(ctx):
    if bot.cat_spawned:
        bot.cat_spawned = False
        await ctx.send(f"Congratulations {ctx.author.mention}! You conquered the ship! ⚓🚢")
    else:
        await ctx.send("There is no ship to attack right now!")

# Run the bot
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
