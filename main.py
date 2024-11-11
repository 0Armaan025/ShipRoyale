import discord
from discord.ext import commands, tasks
import random
import asyncio
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

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
            spawn_delay = random.randint(0,1)
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
async def balance(ctx):
    user_id = str(ctx.author.name)

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    if user_id not in users:
        await ctx.send("You need to register first. Use `$start` to get started.")
        return
    else:
        balance = users[user_id].get("balance", 0)
        await ctx.send(f"{ctx.author.mention}, your current balance is {balance} shipoons.")            

@bot.command()
async def buy(ctx,*,ship_name):
    user_id = str(ctx.author.name)

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    try:
        with open("ships.json", "r") as f:
            ships = json.load(f)
    except FileNotFoundError:
        await ctx.send("Ship data not available, try later!")
        return

    ship_data = next((ship for ship in ships if ship['ship_name'].lower() == ship_name.lower()), None) 
    if not ship_data:
        await ctx.send(f"The ship **{ship_name}** is not available for purchase, sorry!")
        return

    ship_price = None

    for stat in ship_data.get("ship_stats", []):
        if stat["stat_name"] == "Price":
            ship_price = stat["stat_value"]
            break

    if ship_price is None:
        await ctx.send("Could not find the price of the ship, try again later!")
        return
    
    if user_id not in users:
        users[user_id] = {"balance": 0, "ships": [], "selected_ship": None}

    user_data = users[user_id]    
    
    if ship_name in user_data["ships"]:
        await ctx.send("You already own this ship!")
        return
    
    if user_data["balance"] < ship_price:
        await ctx.send("You do not have enough shipoons to purchase this ship!")
        return
    
    user_data['balance'] -= ship_price
    user_data['ships'].append(ship_name)

    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

    await ctx.send(f"Congratulations! 🥳 {ctx.author.mention}, you have finally purchased this ship, type `$ships` to view your ships!")
    await ctx.send("Thanks for shopping, please come again too...")

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
                    f"Description: {ship['ship_description'][:100]}..."  
                ), inline=False)
        
        
        embed.set_image(url=f"{available_ships[0]['ship_image']}")

        await ctx.send(embed=embed)
    else:
        await ctx.send("You own all the ships already!")    

    await ctx.send("Welcome traveller to the shop! The ships you have will not appear on the list to buy!")



@bot.command()
async def select(ctx, *, ship_name):
    user_id = str(ctx.author.name)
    try:
        with open("users.json","r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    if user_id in users:
        user_data = users[user_id]
        if "ships" in user_data and ship_name in user_data['ships']:
            user_data['selected_ship'] = ship_name

            with open("users.json","w") as f:
                json.dump(users,f,indent=4)

            await ctx.send(f"{ctx.author.mention}, you have successfully selected **{ship_name}** as your primary ship!")

        else:
            await ctx.send(f"{ctx.author.mention}, you don't own a ship named **{ship_name}.**")        
    else:
        await ctx.send(f"{ctx.author.mention}, you don't have any ships to select.")

def get_ship_stat_value(ship, stat_name):
    
    
    for stat in ship.get("ship_stats", []):
        if stat["stat_name"].lower() == stat_name.lower():
            return stat["stat_value"]
    
    
    for weapon in ship.get("ship_weapons", []):
        if weapon["weapon_name"].lower() == stat_name.lower():
            return weapon["stat_value"]
    
    
    for module in ship.get("ship_modules", []):
        if module["module_name"].lower() == stat_name.lower():
            return module["stat_value"]
    
    
    for defense in ship.get("ship_defense_skills", []):
        if defense["defense_name"].lower() == stat_name.lower():
            return defense["stat_value"]


def load_ships():
    try:
        with open("ships.json", "r") as file:
            ships = json.load(file)
            return ships
    except FileNotFoundError:
        print("Error: ships.json file not found.")
        return []

def get_ship_stat_value(ship, stat_name):
    for stat in ship.get("ship_stats", []):
        if stat["stat_name"].lower() == stat_name.lower():
            return stat["stat_value"]
    return 0  


def get_random_ship_attack_value(ship):
    weapons = ship.get("ship_weapons", [])
    if not weapons:
        return 0  

    random_weapon = random.choice(weapons)  
    weapon_name = random_weapon.get("weapon_name", "Unknown Weapon")
    weapon_value = random_weapon.get("stat_value", 0)

    print(f"Using weapon: {weapon_name} with attack value: {weapon_value}")
    return weapon_value, weapon_name


def get_ship_defense_value(ship):
    for defense in ship.get("ship_defense_skills", []):
        if "stat_value" in defense:
            return defense["stat_value"]
    return 0  

async def spawn_ship(channel_id: int):
    print(f"Spawning ship in channel {channel_id}")  
    
    with open('ships.json', 'r') as file:
        ships = json.load(file)

    random_ship = random.choice(ships)

    while random_ship.get("ship_name") == "SUPER BATTLE SHIP":
        random_ship = random.choice(ships)

    bot.spawned_ship = random_ship.get("ship_name")
    bot.random_spawned_ship = random_ship
    
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

def get_ship_attack_value(ship):
    return sum(weapon["stat_value"] for weapon in ship.get("ship_weapons", []))



@bot.command()
async def start(ctx):

    await ctx.send("🌌 **Welcome back, traveller!** I'm here to guide you on your journey to the stars and beyond. To begin, I'll help you find a worthy ship for your adventures!")
    await ctx.send("💰 **As a starter reward, you'll receive 30,000 Shipoons, our exclusive currency!**")


    available_ships = ["Titanic", "USS Constitution", "Queen Mary", "USS Enterprise (CVN-65)", "Queen Mary 2"]
    await ctx.send("🚢 **Available Starter Ships:**")
    for index, ship in enumerate(available_ships, start=1):
        await ctx.send(f"{index}. **{ship}**")


    user_id = str(ctx.author.name)
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}


    if user_id in users:
        await ctx.send("👀 You are already registered, Captain! Ready to sail the cosmos again?")
    else:

        users[user_id] = {
            "balance": 30000,
            "selected_ship": "",
            "ships": [],
            "last_beg": "",
            "wins": 0,
            "loses": 0
        }
        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)


        await ctx.send("To learn more about any of the ships, use `$info <ship_name>`. When you're ready, use `$select_initial <ship_name>` to choose your starting ship.")
        await ctx.send("**⚠️ Note:** Choosing your ship is a one-time decision, so select wisely as it cannot be changed later.")

@bot.command()
async def select_initial(ctx, *, ship_name: str):

    available_ships = ["Titanic", "USS Constitution", "Queen Mary", "USS Enterprise (CVN-65)", "Queen Mary 2"]


    if ship_name.lower() not in [ship.lower() for ship in available_ships]:
        await ctx.send("⚠️ **Invalid selection!** Please choose a ship from the available list by typing `$start` to view your options.")
        return

    user_id = str(ctx.author.name)
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        await ctx.send("🚨 **User data not found.** Please begin your journey by typing `$start`.")
        return


    if user_id not in users:
        await ctx.send("🚨 **Unregistered!** You must register first with `$start` to choose a ship.")
        return

    user_data = users[user_id]
    if user_data["selected_ship"]:

        await ctx.send(f"{ctx.author.mention}, you've already selected **{user_data['selected_ship']}** as your ship, and this decision is final.")
        return


    user_data["selected_ship"] = ship_name
    user_data["ships"].append(ship_name)

    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)


    await ctx.send(f"🎉 **Congratulations, Captain {ctx.author.mention}!** You've chosen **{ship_name}** as your starting ship. Set your course, and let the adventure begin! 🚢💨")
    await ctx.send("🌠 **May the stars guide you on this incredible journey.**")




@bot.command()
async def conquer(ctx):
    username = str(ctx.author.name)
    users = load_users()

    if username not in users:
        await ctx.send("🛑 You need to register first. Use `$start` to get started and prepare for your conquest!")
        return

    ships = load_ships()

    super_random_no = random.randint(0,1000000)
    if super_random_no>=8999777:
        await ctx.send("🛳️💨 The ship has disappeared in the fog, sorry!")
        return

    user_ship_name = users[username]["selected_ship"]
    user_ship = next((ship for ship in ships if ship["ship_name"].lower() == user_ship_name.lower()), None)

    if user_ship is None:
        await ctx.send("⚠️ Couldn't locate your selected ship. Please double-check your selection or register a new ship.")
        return

    random_ship = bot.random_spawned_ship

    
    user_attack = get_ship_attack_value(user_ship)
    user_defense = get_ship_defense_value(user_ship)
    user_hp = get_ship_stat_value(user_ship, "HP")

    enemy_attack = get_ship_attack_value(random_ship)
    enemy_defense = get_ship_defense_value(random_ship)
    enemy_hp = get_ship_stat_value(random_ship, "HP")

    await ctx.send(f"🚀 **Battle Begins!** 🚀\n\n**Your Ship:** {user_ship['ship_name']}\n💙 HP: {user_hp}\n🗡️ Attack: {user_attack}\n🛡️ Defense: {user_defense}\n\n**Enemy Ship:** {random_ship['ship_name']}\n💙 HP: {enemy_hp}\n🗡️ Attack: {enemy_attack}\n🛡️ Defense: {enemy_defense}\n\n")

    while user_hp > 0 and enemy_hp > 0:
        await ctx.send("Choose your action:\n1️⃣ **Attack**\n2️⃣ **Defend**\n3️⃣ **Run Away**")
        
        def check(m):
            return m.author == ctx.author and m.content.lower() in ['1', '2', '3']
        
        try:
            user_choice = await bot.wait_for('message', check=check, timeout=30)
        except TimeoutError:
            await ctx.send("⏰ You hesitated too long! The enemy seizes the opportunity and attacks!")
            user_choice = None

        if user_choice:
            choice = user_choice.content.lower()

            if choice == '1':  
                damage, weapon_name = get_random_ship_attack_value(user_ship)
                random_module = random.choice(random_ship["ship_modules"])
                random_module_name = random_module.get("module_name", "Unknown Module")

                enemy_hp -= damage
                await ctx.send(f"💥 You fire your **{weapon_name}**, dealing **{damage}** damage to the enemy's **{random_module_name}**! 🎯\n🔻 Enemy HP: {enemy_hp}")
            
            elif choice == '2':  
                defense_boost = random.randint(5, user_defense)
                await ctx.send(f"🛡️ You take a defensive stance, boosting your defense by **{defense_boost}**!")
                user_defense += defense_boost

            elif choice == '3':  
                await ctx.send("🏃 You decided to retreat. The battle ends in your escape, but the enemy may return...")
                return

            
            if enemy_hp > 0:
                enemy_damage = random.randint(10, enemy_attack)
                user_hp -= enemy_damage
                await ctx.send(f"🔥 The enemy retaliates! You take **{enemy_damage}** damage.\n💔 Your HP: {user_hp}")


        if user_hp <= 0:
            await ctx.send(f"💀 **{ctx.author.mention}, your ship has been defeated in battle!** 💔")
            users[username]["wins"] = users[username].get("losses", 0) + 1
            with open('users.json', 'w') as file:
                json.dump(users, file, indent=4)
            break
        elif enemy_hp <= 0:
            if "ships" not in users[username]:
                users[username]["ships"] = []
            
            users[username]["ships"].append(random_ship.get("ship_name"))

            await ctx.send(f"🎉 **{ctx.author.mention}, you have triumphed! The enemy ship is defeated!** 🏆")
            random_shipoons = random.randint(0, 50000)
            await ctx.send(f"Congrats! you also looted {random_shipoons} shipoons from their ship too!")
            users[username]["balance"] = users[username].get("balance", 0) + random_shipoons
            users[username]["wins"] = users[username].get("wins", 0) + 1
            with open('users.json', 'w') as file:
                json.dump(users, file, indent=4)
            break




@bot.command()
async def ships(ctx):
    

    user_id = str(ctx.author.name)
    users = load_users()

    

    if user_id not in users:
        await ctx.send("You need to register first, please type `$start` to get started.")
        return 

    

    user_ships = users[user_id].get("ships",[])
    if not user_ships:
        await ctx.send("You currently have no ships, please use `$start` and then `$select <ship_name>` from the available early ships to get started.")
        return
    
    

    embed = discord.Embed(title=f"{ctx.author.display_name}'s Ships:", color=discord.Color.blue(), description="Here are the ships that you own:")

    for ship in user_ships:
        embed.add_field(name=ship, value="", inline=False)


    await ctx.send(embed=embed)        




@bot.command()
async def beg(ctx):
    username = str(ctx.author.name)
    users = load_users()
    if username in users:
        if "last_beg" in users[username]:
            last_beg = datetime.fromisoformat(users[username]["last_beg"])
            if datetime.now() - last_beg < timedelta(hours=1):
                await ctx.send("You can beg for more shipoons in 1 hour.")
                return

@bot.command()
async def purge(ctx, limit: str):
    if ctx.author.guild_permissions.administrator:
        if limit == "all":
            await ctx.channel.purge()
            embed = discord.Embed(title="Purge", description=f"Successfully purged all messages in {ctx.channel.mention} by {ctx.author.display_name}.", color=discord.Color.green(), timestamp=ctx.message.created_at)
            await ctx.send(embed=embed, delete_after=3)
            
        else:     
            await ctx.channel.purge(limit=int(limit))
            embed = discord.Embed(title="Purge", description=f"Successfully purged {limit} messages in {ctx.channel.mention} by {ctx.author.display_name}.", color=discord.Color.green(), timestamp=ctx.message.created_at)
            await ctx.send(embed=embed, delete_after=3)
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
            
                await ctx.send( embed=embed)
            else:
                await ctx.send(embed=embed)
            break
    else:
        await ctx.send(f"Ship with name '{ship_name}' not found.")

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
