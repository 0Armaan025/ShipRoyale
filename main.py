import discord
from discord.ext import commands, tasks
import random
import asyncio
from dotenv import load_dotenv
import os
import json

load_dotenv()


class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.cat_spawned = False
        self.channel_ids = []

    async def on_ready(self):
        print(f'Logged on as: {self.user}')

        
        if not bot.guilds:
            print("Bot is not in any guild.")
            return

        
        for guild in bot.guilds:
            if guild.text_channels:
                
                self.channel_ids = [channel.id for channel in guild.text_channels]
                print(f"Available channels in guild '{guild.name}': {self.channel_ids}")
                break        

        
        if not self.channel_ids:
            print("No channels available for spawning the ship.")
            return

        
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
async def start(ctx):
    await ctx.send("Welcome back traveller! I am here to help you find the best ship for your journey. Type `$ships` to see what ships you can get for free.")
    await ctx.send("As the starting award, you will also get 30000 in shipoons currency")
    
    available_ships = ["Titanic", "USS Constituion","Queen Mary", "USS Enterprise (CVN-65)", "Queen Mary 2"]

    index = 1
    await ctx.send("Available ships:")
    for ship in available_ships:
        await ctx.send(f"{index}.) {ship}\n")
        index += 1

    await ctx.send("Write `$info <ship_name>` to get more information about the ship and write `$select <ship_name>` to select the ship, remember this will be your final decision and it can't be changed later on.")


@bot.command()
async def purge(ctx, amount: str):
    if ctx.author.guild_permissions.administrator:
        if amount == "all":
            await ctx.channel.purge()
        else:
            await ctx.channel.purge(limit=int(amount))

        embed = discord.Embed(title="Purged successfully!", description=f"The messages have been purged successfully, Amount: {amount} by {ctx.author.mention}", color=discord.Color.red())   
        await ctx.send(embed=embed, delete_after=5)
    else:
        await ctx.send("You do not have the necessary permissions to use this command.")


@bot.command()
async def info(ctx, *, ship_name=None):
    
    if not ship_name:
        await ctx.send("Please provide a ship name to look up.")
        return

    with open('ships.json', 'r') as file:
        ships = json.load(file)

    
    for ship in ships:
        if ship.get("ship_name", "").lower() == ship_name.lower():
            
            embed = discord.Embed(
                title="Ship Details",
                color=discord.Color.purple(),
                description=ship.get("ship_description", "No description available")
            )

            
            def format_field(field_data):
                if not field_data:
                    return "No data available"

                formatted_data = []
                for item in field_data:
                    name = item.get("name") or item.get("stat_name") or item.get("module_name") or item.get("defense_name") or item.get("weapon_name", "Unknown")
                    value = item.get("value") or item.get("stat_value", "N/A")
                    formatted_data.append(f"{name}: {value}")
                return "\n".join(formatted_data)

            
            stats_str = format_field(ship.get("ship_stats", []))
            weapons_str = format_field(ship.get("ship_weapons", []))
            modules_str = format_field(ship.get("ship_modules", []))
            defense_str = format_field(ship.get("ship_defense_skills", []))

            embed.add_field(name="Name", value=ship.get("ship_name", "Unknown"), inline=False)
            embed.add_field(name="Type", value=ship.get("ship_type", "Unknown"), inline=False)
            embed.add_field(name="Stats", value=stats_str, inline=False)
            embed.add_field(name="Weapons", value=weapons_str, inline=False)
            embed.add_field(name="Modules", value=modules_str, inline=False)
            embed.add_field(name="Defense Skills", value=defense_str, inline=False)

            
            file_path = f"ship_images/{ship.get('ship_image', '')}"
            if os.path.exists(file_path):
                file = discord.File(file_path, filename=ship['ship_image'])
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)
            break
    else:
        
        await ctx.send(f"Ship with name '{ship_name}' not found.")
    

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

async def spawn_ship(channel_id: int):
    print(f"Spawning ship in channel {channel_id}")  
    
    with open('ships.json', 'r') as file:
        ships = json.load(file)

    random_ship = random.choice(ships)

    
    embed = discord.Embed(
        title="Ship Details", 
        color=discord.Color.purple(),
        description=f"{random_ship.get('ship_description', 'No description available')}"
    )

    
    def format_field(field_data):
        if not field_data:
            return "No data available"

        formatted_data = []
        for item in field_data:
            name = item.get('name', item.get('stat_name', item.get('module_name', item.get('defense_name', item.get('weapon_name', 'Unknown')))))
            value = item.get('value', item.get('stat_value', 'N/A'))
            formatted_data.append(f"{name}: {value}")
        return "\n".join(formatted_data)

    
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


token = os.getenv('DISCORD_TOKEN')
bot.run(token)
