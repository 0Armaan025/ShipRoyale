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

        if not self.guilds:
            print("Bot is not in any guild.")
            return

        for guild in self.guilds:
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
                channel_id = random.choice(self.channel_ids) 
                channel = self.get_channel(channel_id)
                if channel:
                    print(f"Spawning ship in channel {channel_id}")
                    await spawn_ship(channel.id)  
                else:
                    print(f"Failed to get channel {channel_id}")
            else:
                print("Ship already spawned, skipping spawn.")

bot = MyBot(command_prefix='$', intents=discord.Intents.all())

def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as file:
            return json.load(file)
    return {}

@bot.command()
async def shop(ctx):
    user_id = str(ctx.author.name)

    users = load_users()

    if user_id not in users:
        await ctx.send("You need to register first. Use `$start` to get started.")
        return
    
    with open("ships.json", "r") as f:
        all_ships = json.load(f)

    user_ships = users[user_id].get("ships",[])

    available_ships = [ship for ship in all_ships if ship['ship_name'] not in user_ships]

    if available_ships:
        embed = discord.Embed(title="Ship Shop", description="Here are the ships available for purchase:", color=discord.Color.green())
        
        for ship in available_ships:
            embed.add_field(name=ship["ship_name"] , value=(
                    f"Type: {ship['ship_type']}\n"
                    f"Price: {next(stat['stat_value'] for stat in ship['ship_stats'] if stat['stat_name'] == 'Price')}\n"
                    f"Description: {ship['ship_description'][:100]}..."  # Shorten description
                ), inline=False)
        
        # Set the image URL outside of the loop
        embed.set_image(url=f"{available_ships[0]['ship_image']}")

        await ctx.send(embed=embed)
    else:
        await ctx.send("You own all the ships already!")    

    await ctx.send("Welcome traveller to the shop! The ships you have will not appear on the list to buy!")

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
    embed.set_image(url=f"{random_ship['ship_image']}")
    
    file_path = f"ship_images/{random_ship.get('ship_image', '')}"

    if os.path.exists(file_path):
        # file = discord.File(file_path, filename=random_ship['ship_image'])
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send( embed=embed)
        else:
            print(f"Channel with ID {channel_id} not found.")
    else:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
        else:
            print(f"Channel with ID {channel_id} not found.")

@bot.command()
async def conquer(ctx):
    username = str(ctx.author.name)
    users = load_users()

    if username not in users:
        await ctx.send("You need to register first. Use `$start` to get started.")
        return

    if not bot.cat_spawned:
        await ctx.send("No ship to conquer at the moment!")
        return

    bot.cat_spawned = False
    await ctx.send(f"Congratulations {ctx.author.mention}! You conquered the ship! ⚓🚢")

@bot.command()
async def ships(ctx):
    # it's going to display ur ships that u have

    user_id = str(ctx.author.name)
    users = load_users()

    # get the list of users :)

    if user_id not in users:
        await ctx.send("You need to register first, please type `$start` to get started.")
        return # just return then

    # otherwise:

    user_ships = users[user_id].get("ships",[])
    if not user_ships:
        await ctx.send("You currently have no ships, please use `$start` and then `$select <ship_name>` from the available early ships to get started.")
        return
    
    # otherwise:

    embed = discord.Embed(title=f"{ctx.author.display_name}'s Ships:", color=discord.Color.blue(), description="Here are the ships that you own:")

    for ship in user_ships:
        embed.add_field(name=ship, value="", inline=False)


    await ctx.send(embed=embed)        

@bot.command()
async def purge(ctx, limit: str):
    if ctx.author.guild_permissions.administrator:
        if limit == "all":
            await ctx.channel.purge()
            embed = discord.Embed(title="Purge", description=f"Successfully purged all messages in {ctx.channel.mention} by {ctx.author.display_name}.", color=discord.Color.green(), timestamp=ctx.message.created_at)
            message = await ctx.send(embed=embed, delete_after=3)
            
        else:     
            await ctx.channel.purge(limit=int(limit))
            embed = discord.Embed(title="Purge", description=f"Successfully purged {limit} messages in {ctx.channel.mention} by {ctx.author.display_name}.", color=discord.Color.green(), timestamp=ctx.message.created_at)
            message = await ctx.send(embed=embed, delete_after=3)
    else:
        await ctx.send("Sorry!, but you do not have the permission.")

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
                return "\n".join(f"{item.get('name', item.get('stat_name', item.get('module_name', item.get('defense_name', item.get('weapon_name', 'Unknown')))))}: {item.get('value', item.get('stat_value', 'N/A'))}" for item in field_data)

            embed.add_field(name="Name", value=ship.get("ship_name", "Unknown"), inline=False)
            embed.add_field(name="Type", value=ship.get("ship_type", "Unknown"), inline=False)
            embed.add_field(name="Stats", value=format_field(ship.get("ship_stats", [])), inline=False)
            embed.add_field(name="Weapons", value=format_field(ship.get("ship_weapons", [])), inline=False)
            embed.add_field(name="Modules", value=format_field(ship.get("ship_modules", [])), inline=False)
            embed.add_field(name="Defense Skills", value=format_field(ship.get("ship_defense_skills", [])), inline=False)
            embed.set_image(url=f"{ship['ship_image']}")
    

            file_path = f"ship_images/{ship.get('ship_image', '')}"
            if os.path.exists(file_path):
                # file = discord.File(file_path, filename=ship['ship_image'])
                await ctx.send( embed=embed)
            else:
                await ctx.send(embed=embed)
            break
    else:
        await ctx.send(f"Ship with name '{ship_name}' not found.")

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
