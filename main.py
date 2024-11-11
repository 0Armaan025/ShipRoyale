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

def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)

@bot.command()
async def start(ctx):
    username = str(ctx.author.name)
    users = load_users()

    if username in users:
        await ctx.send("You are already registered! Use `$info <ship_name>` to get more information on available ships.")
    else:
        users[username] = {"balance": 30000, "ships": [], "selected_ship": None}
        save_users(users)
        await ctx.send("Welcome back, traveller! You have been registered and awarded 30000 in shipoons currency.")
        await ctx.send("Available ships to start your journey: Titanic, USS Constitution, Queen Mary, USS Enterprise (CVN-65), Queen Mary 2.")
        await ctx.send("Use `$select <ship_name>` to choose your starting ship.")

@bot.command()
async def select(ctx, *, ship_name: str):
    initial_ships = ["Titanic", "USS Constitution", "Queen Mary", "USS Enterprise (CVN-65)", "Queen Mary 2"]
    username = str(ctx.author.name)
    users = load_users()

    if username not in users:
        await ctx.send("You need to register first. Use `$start` to get started.")
        return

    if users[username]["selected_ship"]:
        await ctx.send("You have already selected a ship. This choice is final.")
        return

    if ship_name in initial_ships:
        users[username]["selected_ship"] = ship_name
        users[username]["ships"].append(ship_name)
        save_users(users)
        await ctx.send(f"Congratulations! You have selected {ship_name} as your ship.")
    else:
        await ctx.send("Please choose from the available ships. Use `$start` to view them again.")

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
        return "\n".join(f"{item.get('name', item.get('stat_name', item.get('module_name', item.get('defense_name', item.get('weapon_name', 'Unknown')))))}: {item.get('value', item.get('stat_value', 'N/A'))}" for item in field_data)

    embed.add_field(name="Name", value=random_ship.get("ship_name", "Unknown"), inline=False)
    embed.add_field(name="Type", value=random_ship.get("ship_type", "Unknown"), inline=False)
    embed.add_field(name="Stats", value=format_field(random_ship.get('ship_stats', [])), inline=False)
    embed.add_field(name="Weapons", value=format_field(random_ship.get('ship_weapons', [])), inline=False)
    embed.add_field(name="Modules", value=format_field(random_ship.get('ship_modules', [])), inline=False)
    embed.add_field(name="Defense Skills", value=format_field(random_ship.get('ship_defense_skills', [])), inline=False)

    file_path = f"ship_images/{random_ship.get('ship_image', '')}"

    channel = bot.get_channel(channel_id)
    if channel:
        if os.path.exists(file_path):
            file = discord.File(file_path, filename=random_ship['ship_image'])
            await channel.send(file=file, embed=embed)
        else:
            await channel.send(embed=embed)
    else:
        print(f"Channel with ID {channel_id} not found.")

@bot.command()
async def catch(ctx):
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

            file_path = f"ship_images/{ship.get('ship_image', '')}"
            if os.path.exists(file_path):
                file = discord.File(file_path, filename=ship['ship_image'])
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)
            break
    else:
        await ctx.send(f"Ship with name '{ship_name}' not found.")

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
