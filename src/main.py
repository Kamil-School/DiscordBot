import discord
from discord.ext import commands
from discord.ui import View
import json
import os
import datetime
import math
import difflib
import Levenshtein

# Configurations and global variables

TOKEN = 'Not Sharing'
GIVEAWAY_LOG_FILE = "giveaway_log_messages.json"
DATA_FILE = "bot_data.json"
LOG_FILE = "role_dates.json"
giveaway_channel_id = 1305256907715510272

# Message Id's, will be loaded/saved
role_menu_message_id = None
special_role_menu_message_id = None
global_role_menu_message_id = None
temp_role_menu_message_id = None
poe2_role_menu_message_id = None

# Global giveaway log and a flag
giveaway_log_messages = {}
waiting = False

# Dicts for role assignments and emojis

role_assignments = {
    'Party': 'Party Play',
    'Challenge': 'Challenge Help',
    'Crafting': 'Craft Help',
    'Valdos': 'Lottos',
    'Divine': 'Crafting/Profit Alert'
}

global_role_assignments = {
    'Divine': 'Crafting/Profit Alert',
    'POEGuyNews': 'POEGuy News',
    'Leaguestart': 'League Starting'
}

temp_role_assignments = {
    'Necrosettlers': 'Necro Settlers'
}

poe2_role_assignments = {
    'Poe2': 'POE2'
}

emoji_dict = {
    'Party': '<:Party:1303588149607272468>',
    'Challenge': '<:Challenge:1303588004371107942>',
    'Crafting': '<:Crafting:1303587880832204842>',
    'Valdos': '<:Valdos:1303586402939830324>',
    'Divine': '<:Divine:1303587924771602495>'
}

global_emoji_dict = {
    'Divine': '<:Divine:1303587924771602495>',
    'POEGuyNews': '<:POEGuyNews:1306855287713431572>',
    'Leaguestart': '<:Leaguestart:1306855297595346984>'
}

temp_emoji_dict = {
    'Necro Settlers': '<:Necrosettlers:1306860317271130162>'
}

poe2_emoji_dict = {
    'Poe2': '<:Poe2:1313636460108316763>'
}

# Data handling

def save_data(role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id):
    data = {
        "role_menu_message_id": role_menu_message_id,
        "special_role_menu_message_id": special_role_menu_message_id,
        "global_role_menu_message_id": global_role_menu_message_id,
        "temp_role_menu_message_id": temp_role_menu_message_id,
        "poe2_role_menu_message_id": poe2_role_menu_message_id
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print("Important data saved to file.")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            role_menu_message_id = data.get("role_menu_message_id")
            special_role_menu_message_id = data.get("special_role_menu_message_id")
            global_role_menu_message_id = data.get("global_role_menu_message_id")
            temp_role_menu_message_id = data.get("temp_role_menu_message_id")
            poe2_role_menu_message_id = data.get("poe2_role_menu_message_id")
        print(f"Loaded role menu message ID: {role_menu_message_id}")
        print(f"Loaded global role menu message ID: {global_role_menu_message_id}")
    else:
        print("No data file found, starting fresh.")
        role_menu_message_id = special_role_menu_message_id = global_role_menu_message_id = temp_role_menu_message_id = poe2_role_menu_message_id = None
    return role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id

def load_into_dicts():
    global role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id, giveaway_log_messages
    role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id = load_data()
    giveaway_log_messages = load_giveaway_log()

def load_role_dates():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump({}, f)
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_role_dates(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def reset_role_dates():
    data = load_role_dates()
    for user_id in data.keys():
        data[user_id]["active_role_date"] = None
    save_role_dates(data)

# Giveaway logs

def load_giveaway_log():
    if os.path.exists(GIVEAWAY_LOG_FILE):
        try:
            with open(GIVEAWAY_LOG_FILE, 'r') as f:
                giveaway_log_messages = json.load(f)
            print("Giveaway log messages loaded from file.")
            return giveaway_log_messages
        except json.JSONDecodeError:
            print("JSON file is empty or corrupted. Starting with an empty giveaway log.")
            return {}
    else:
        print("No existing giveaway log file found. Starting fresh.")
        return {}

def save_giveaway_log(giveaway_log_messages):
    with open(GIVEAWAY_LOG_FILE, 'w') as f:
        json.dump(giveaway_log_messages, f, indent=4)
    print("Giveaway log messages saved to file.")

def add_giveaway_entry(user_id, log_message_id, giveaway_message_link, giveaway_log_messages, status="Pending"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "log_message_id": log_message_id,
        "timestamp": timestamp,
        "status": status,
        "giveaway_message_link": giveaway_message_link
    }
    if str(user_id) not in giveaway_log_messages:
        giveaway_log_messages[str(user_id)] = []
    giveaway_log_messages[str(user_id)].append(entry)
    print(giveaway_log_messages)
    save_giveaway_log(giveaway_log_messages)
    return giveaway_log_messages

def update_giveaway_status(user_id, log_message_id, new_status, giveaway_log_messages):
    user_key = str(user_id)
    if user_key in giveaway_log_messages:
        for entry in giveaway_log_messages[user_key]:
            if entry["log_message_id"] == log_message_id:
                entry["status"] = new_status
                save_giveaway_log(giveaway_log_messages)
                return giveaway_log_messages

# Lotto functions

async def lotto_check(bot, message, giveaway_log_messages):
    if message.reference and message.reference.message_id:
        original_message_id = message.reference.message_id
        original_channel_id = message.reference.channel_id
        guild_id = message.guild.id
        giveaway_message_link = f"https://discord.com/channels/{guild_id}/{original_channel_id}/{original_message_id}"
        if message.mentions:
            if "rerolled" in message.content.lower():
                mentioned_user = message.mentions[1]
            else:
                mentioned_user = message.mentions[0]
            try:
                dm_message = await mentioned_user.send("You have won a giveaway! Would you like to accept it?")
                await dm_message.add_reaction("✅")
                await dm_message.add_reaction("❌")
                giveaway_channel = bot.get_channel(giveaway_channel_id)
                if giveaway_channel:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_message = await giveaway_channel.send(
                        f"Giveaway Result:\nWinner: {mentioned_user.name}\nDate/Time: {timestamp}\n"
                        f"Status: Pending\nOriginal Giveaway: [Click Here]({giveaway_message_link})"
                    )
                    giveaway_log_messages = add_giveaway_entry(mentioned_user.id, log_message.id, giveaway_message_link, giveaway_log_messages)
            except discord.Forbidden:
                await message.channel.send(f"Could not DM {mentioned_user.mention}. They may have DMs disabled.")
        else:
            print("No user was mentioned in the congratulations message.")
    else:
        print("The congratulations message was not a reply to an original giveaway message.")
    return giveaway_log_messages

# Giveaway claim fuction

async def claim(ctx, bot):
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if replied_message.author == bot.user:
            new_content = replied_message.content + " [CLAIMED]"
            await replied_message.edit(content=new_content)
            await ctx.send("Message successfully claimed!")
            logs = load_giveaway_log()
            for user_id, entries in list(logs.items()):
                for entry in entries:
                    if entry["log_message_id"] == replied_message.id:
                        entries.remove(entry)
                        if not entries:
                            del logs[user_id]
                        save_giveaway_log(logs)
                        await ctx.send("Giveaway log entry deleted.")
                        return
            await ctx.send("No corresponding giveaway log entry found.")
        else:
            await ctx.send("You can only claim messages sent by the bot.")
    else:
        await ctx.send("Please reply to a bot message with `!claimed` to claim it.")

# Role menu creations

async def create_temp_role_menu(ctx, bot):
    if not ctx.author.guild_permissions.administrator and ctx.author.id != 1044685722021539860:
        await ctx.send("You do not have permission to use this command.")
        return
    global temp_role_menu_message_id
    intro_embed = discord.Embed(
        title="🎉 Join the Necro Settlers Event!",
        description=(
            "To make the most of this temporary event, we’ve set up custom roles so you can stay updated and engaged. "
            "We'll be using this role to ping out Divine drop hours during the Necro Settlers league. Let your FOMO go free!\n\n"
            "This role will be deleted at the end of the event.\n\n"
            f"{temp_emoji_dict['Necro Settlers']} **Necro Settlers**"
        ),
        color=discord.Color.orange()
    )
    message = await ctx.send(embed=intro_embed)
    temp_role_menu_message_id = message.id
    for emote_name, emote_str in temp_emoji_dict.items():
        try:
            emoji_id = int(emote_str.split(':')[-1][:-1])
            emoji = bot.get_emoji(emoji_id)
            if emoji:
                await message.add_reaction(emoji)
            else:
                print(f"Couldn't find emoji for {emote_name}")
        except discord.HTTPException:
            print(f"Couldn't add reaction for {emote_name}")
    return temp_role_menu_message_id

async def create_global_role_menu(ctx, bot):
    if not ctx.author.guild_permissions.administrator and ctx.author.id != 1044685722021539860:
        await ctx.send("You do not have permission to use this command.")
        return
    global global_role_menu_message_id
    intro_embed = discord.Embed(
        title="📢 Customize Your Discord Experience!",
        description=(
            "To help you control what notifications you receive, we offer role options you can assign or unassign at any time. "
            "Choose only the alerts relevant to you and avoid unnecessary pings. Simply react to this post with the emoji for the role(s) you want!\n\n"
            f"{global_emoji_dict['Divine']} **Crafting/Profit Alert** – Stay informed on crafting and profit opportunities as they come up. "
            "Please note: general alerts in the Discord differ from Guild-Exclusive pings.\n\n"
            f"{global_emoji_dict['POEGuyNews']} **POEGuy News** – Get the latest updates from POEGuy. Track his videos in <#1158676000096407613>, "
            "and be alerted when new videos or major announcements drop.\n\n"
            f"{global_emoji_dict['Leaguestart']} **League Starting** – Perfect if you're starting a league! Receive pings about changes, nerfs, buffs, "
            "new tech, and build updates early in the league. Once you've progressed past league-start, feel free to unassign this role.\n\n"
            "React below to customize your notifications!"
        ),
        color=discord.Color.purple()
    )
    message = await ctx.send(embed=intro_embed)
    global_role_menu_message_id = message.id
    for emote_name, emote_str in global_emoji_dict.items():
        try:
            emoji_id = int(emote_str.split(':')[-1][:-1])
            emoji = bot.get_emoji(emoji_id)
            if emoji:
                await message.add_reaction(emoji)
            else:
                print(f"Couldn't find emoji for {emote_name}")
        except discord.HTTPException:
            print(f"Couldn't add reaction for {emote_name}")
    return global_role_menu_message_id

async def create_role_menu(ctx, bot):
    if not ctx.author.guild_permissions.administrator and ctx.author.id != 1044685722021539860:
        await ctx.send("You do not have permission to use this command.")
        return
    global role_menu_message_id
    intro_embed = discord.Embed(
        title="🎮 Auto Role Menu 🎮",
        description=(
            "With our guild growing and everyone having unique interests, we want you to receive only the pings that "
            "matter most to you, while skipping those that don’t.\n\n"
            "You can assign or unassign these roles to yourself anytime, ensuring you’ll only get notifications "
            "relevant to your chosen activities. Just react to this post with the emoji for the role you’re "
            "interested in, and you’ll be automatically assigned!\n\n"
            "📝 **Here’s what each role does:**\n"
            f"\n{emoji_dict['Divine']} **Crafting / Profit Alerts** - Get notifications about the latest crafting opportunities "
            "and profitable items! Great for those who want to make some in-game currency and share tips on the "
            "best items to craft.\n\n"
            f"{emoji_dict['Valdos']} **Lottos** - If you’re into fun raffles or in-game lottery events, this is the role for you! "
            "You’ll be pinged when there’s a new lotto event, so you never miss out on a chance to win.\n\n"
            f"{emoji_dict['Party']} **Party Play** - If you’re looking to team up for group rotas or group farming, be ready to "
            "sync your clocks.\n\n"
            f"{emoji_dict['Crafting']} **Craft Help** - This role is for those who need help with crafting or want to lend their "
            "expertise to others. Connect with others for support and advice!\n\n"
            f"{emoji_dict['Challenge']} **Challenge Help** - For those tackling challenges, this role will give you access to others "
            "who want to help (or need a hand themselves). Share progress towards 40/40.\n\n"
            "React below with the emojis to claim your role:\n\n"
            f"{emoji_dict['Divine']}: for Crafting / Profit Alerts\n"
            f"{emoji_dict['Valdos']}: for Lottos\n"
            f"{emoji_dict['Party']}: for Party Play\n"
            f"{emoji_dict['Crafting']}: for Craft Help\n"
            f"{emoji_dict['Challenge']}: for Challenge Help\n\n"
            "Let’s make our community even better by helping each other and having more fun together. Happy gaming! 🎲🎮"
        ),
        color=discord.Color.purple()
    )
    message = await ctx.send(embed=intro_embed)
    role_menu_message_id = message.id
    for emote_name, emote_str in emoji_dict.items():
        try:
            emoji_id = int(emote_str.split(':')[-1][:-1])
            emoji = bot.get_emoji(emoji_id)
            if emoji:
                await message.add_reaction(emoji)
            else:
                print(f"Couldn't find emoji for {emote_name}")
        except discord.HTTPException:
            print(f"Couldn't add reaction for {emote_name}")
    return role_menu_message_id

async def inactive_menu(ctx):
    if ctx.author != ctx.guild.owner and ctx.author.id != 1044685722021539860:
        await ctx.send("Only the server owner can create this role menu.")
        return
    description = "React with 🔄 to mark all members as 'Inactive' and remove the 'Active' role if they have it."
    message = await ctx.send(description)
    special_role_menu_message_id = message.id
    await message.add_reaction('🔄')
    return special_role_menu_message_id

async def create_poe2_role_menu(ctx, bot):
    if not ctx.author.guild_permissions.administrator and ctx.author.id != 1044685722021539860:
        await ctx.send("You do not have permission to use this command.")
        return
    global poe2_role_menu_message_id
    intro_embed = discord.Embed(
        title="📢 Path of Exile 2!",
        description=(
            f"{poe2_emoji_dict['Poe2']} React below to gain access to POE2-related channels!\n\n"
            "Since the game is in Early Access, this role is perfect for those diving into the game—or for the brave (or masochist) souls "
            "who enjoy watching content for a game they’re not playing.\n\n"
            "By default, you'll see all the POE1 server channels. Use the reaction below to opt in or out of POE2 content and customize your experience!"
        ),
        color=discord.Color.purple()
    )
    message = await ctx.send(embed=intro_embed)
    poe2_role_menu_message_id = message.id
    for emote_name, emote_str in poe2_emoji_dict.items():
        try:
            emoji_id = int(emote_str.split(':')[-1][:-1])
            emoji = bot.get_emoji(emoji_id)
            if emoji:
                await message.add_reaction(emoji)
            else:
                print(f"Couldn't find emoji for {emote_name}")
        except discord.HTTPException:
            print(f"Couldn't add reaction for {emote_name}")
    return poe2_role_menu_message_id

# Reaction handlers

async def role_menu_reacts(payload, guild, user):
    emoji_name = payload.emoji.name
    print(f"Reaction added: {emoji_name} by {user.name} on main role menu message")
    if emoji_name in role_assignments:
        role_name = role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.add_roles(role)
                print(f"Assigned {role_name} role to {user.name}")
            except discord.Forbidden:
                print(f"Cannot assign role {role_name} to {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while assigning role {role_name} to {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the main role assignments.")

async def poe2_role_menu_reacts(payload, guild, user):
    emoji_name = payload.emoji.name
    print(f"Reaction added: {emoji_name} by {user.name} on POE2 role menu message")
    if emoji_name in poe2_role_assignments:
        role_name = poe2_role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.add_roles(role)
                print(f"Assigned {role_name} role to {user.name}")
            except discord.Forbidden:
                print(f"Cannot assign role {role_name} to {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while assigning role {role_name} to {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the POE2 role assignments.")

async def temp_role_menu_reacts_add(payload, user, guild):
    emoji_name = payload.emoji.name
    print(f"Reaction added: {emoji_name} by {user.name} on temp role menu message")
    if emoji_name in temp_role_assignments:
        role_name = temp_role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.add_roles(role)
                print(f"Assigned {role_name} role to {user.name}")
            except discord.Forbidden:
                print(f"Cannot assign role {role_name} to {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while assigning role {role_name} to {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the temp role assignments.")

async def global_role_menu_reacts(payload, guild, user):
    emoji_name = payload.emoji.name
    print(f"Reaction added: {emoji_name} by {user.name} on global role menu message")
    if emoji_name in global_role_assignments:
        role_name = global_role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.add_roles(role)
                print(f"Assigned {role_name} role to {user.name}")
            except discord.Forbidden:
                print(f"Cannot assign role {role_name} to {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while assigning role {role_name} to {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the global role assignments.")

async def DM_react(reaction, bot, user):
    giveaway_channel = bot.get_channel(giveaway_channel_id)
    log_message_id = None
    with open(GIVEAWAY_LOG_FILE, 'r') as f:
        giveaway_log_messages = json.load(f)
    if str(user.id) in giveaway_log_messages:
        for entry in giveaway_log_messages[str(user.id)]:
            if entry["status"] == "Pending":
                log_message_id = entry["log_message_id"]
                break
    if not log_message_id or not giveaway_channel:
        return
    log_message = await giveaway_channel.fetch_message(log_message_id)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Fetched the log message")
    if reaction.emoji == "✅":
        await reaction.message.channel.send("Thank you for accepting the giveaway!")
        await log_message.edit(
            content=f"Giveaway Result:\nWinner: {user.name}\nDate/Time: {timestamp}\n"
                    f"Status: Accepted\nOriginal Giveaway: [Click Here]({giveaway_log_messages[str(user.id)][0]['giveaway_message_link']})"
        )
        giveaway_log_messages = update_giveaway_status(user.id, log_message_id, "Accepted", giveaway_log_messages)
    elif reaction.emoji == "❌":
        await reaction.message.channel.send("You have declined the giveaway.")
        await log_message.edit(
            content=f"Giveaway Result:\nWinner: {user.name}\nDate/Time: {timestamp}\n"
                    f"Status: Declined\nOriginal Giveaway: [Click Here]({giveaway_log_messages[str(user.id)][0]['giveaway_message_link']})"
        )
        giveaway_log_messages = update_giveaway_status(user.id, log_message_id, "Declined", giveaway_log_messages)
    return giveaway_log_messages

async def inactivity_reaction(bot, payload, guild, user, inactive_role_name, active_role_name):
    channel = bot.get_channel(payload.channel_id)
    await channel.send("Starting the process to assign 'Inactive' role to members with the specified role.")
    inactive_role = discord.utils.get(guild.roles, name=inactive_role_name)
    active_role = discord.utils.get(guild.roles, name=active_role_name)
    specific_role = discord.utils.get(guild.roles, id=1158834836161691810)
    if not inactive_role:
        await channel.send("The 'Inactive' role does not exist. Please create it first.")
        return
    if not specific_role:
        await channel.send("The specified role to check members for does not exist.")
        return
    data_dates = load_role_dates()
    for member in guild.members:
        if specific_role in member.roles:
            try:
                await member.add_roles(inactive_role)
                if active_role and active_role in member.roles:
                    await member.remove_roles(active_role)
                if str(member.id) not in data_dates:
                    data_dates[str(member.id)] = {
                        "username": member.name,
                        "active_role_date": None
                    }
                else:
                    data_dates[str(member.id)]["username"] = member.name
            except discord.Forbidden:
                print(f"Could not update roles for {member.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while updating {member.name}: {e}")
    save_role_dates(data_dates)
    await channel.send("All members with the specified role have been marked as 'Inactive' and 'Active' roles removed.")
    message = await channel.fetch_message(payload.message_id)
    await message.remove_reaction('🔄', user)

# Reaction removal functions
async def role_menu_reacts_remove(payload, user, guild):
    emoji_name = payload.emoji.name
    print(f"Reaction removed: {emoji_name} by {user.name} on main role menu message")
    if emoji_name in role_assignments:
        role_name = role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.remove_roles(role)
                print(f"Removed {role_name} role from {user.name}")
            except discord.Forbidden:
                print(f"Cannot remove role {role_name} from {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while removing role {role_name} from {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the main role assignments.")

async def poe2_role_menu_reacts_remove(payload, user, guild):
    emoji_name = payload.emoji.name
    print(f"Reaction removed: {emoji_name} by {user.name} on POE2 role menu message")
    if emoji_name in poe2_role_assignments:
        role_name = poe2_role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.remove_roles(role)
                print(f"Removed {role_name} role from {user.name}")
            except discord.Forbidden:
                print(f"Cannot remove role {role_name} from {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while removing role {role_name} from {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the POE2 role assignments.")

async def temp_role_menu_reacts_remove(payload, user, guild):
    emoji_name = payload.emoji.name
    print(f"Reaction removed: {emoji_name} by {user.name} on temp role menu message")
    if emoji_name in temp_role_assignments:
        role_name = temp_role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.remove_roles(role)
                print(f"Removed {role_name} role from {user.name}")
            except discord.Forbidden:
                print(f"Cannot remove role {role_name} from {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while removing role {role_name} from {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the temp role assignments.")

async def global_role_menu_reacts_remove(payload, user, guild):
    emoji_name = payload.emoji.name
    print(f"Reaction removed: {emoji_name} by {user.name} on global role menu message")
    if emoji_name in global_role_assignments:
        role_name = global_role_assignments[emoji_name]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                await user.remove_roles(role)
                print(f"Removed {role_name} role from {user.name}")
            except discord.Forbidden:
                print(f"Cannot remove role {role_name} from {user.name} due to insufficient permissions.")
            except Exception as e:
                print(f"An error occurred while removing role {role_name} from {user.name}: {e}")
        else:
            print(f"Role {role_name} not found in the guild.")
    else:
        print(f"Emoji {emoji_name} does not match any role in the global role assignments.")

# Wiki command functions

async def wiki(ctx, query):
    formatted_query = query.replace(" ", "%20")
    wiki_url = f"https://www.poewiki.net/index.php?search={formatted_query}"
    print(query)
    embed = discord.Embed(
        title=f"Path of Exile Wiki - {query}",
        description=f"Click the link to view the page: [**{query}**]({wiki_url})",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

async def wiki2(ctx, query):
    formatted_query = query.replace(" ", "%20")
    wiki_url = f"https://www.poe2wiki.net/index.php?search={formatted_query}"
    print(query)
    embed = discord.Embed(
        title=f"Path of Exile 2 Wiki - {query}",
        description=f"Click the link to view the page: [**{query}**]({wiki_url})",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

def find_best_match(item_name, poe_data):
    if item_name in poe_data:
        return item_name
    input_words = item_name.lower().split()
    potential_matches = [key for key in poe_data.keys() if all(word in key.lower() for word in input_words)]
    if not potential_matches:
        potential_matches = difflib.get_close_matches(item_name, poe_data.keys(), n=20, cutoff=0.8)
    if potential_matches:
        best_match = min(potential_matches, key=lambda x: Levenshtein.distance(item_name.lower(), x.lower()))
        return best_match
    return None

async def wikifromdatabase(ctx, item_name, poe_data):
    best_match = find_best_match(item_name, poe_data)
    if best_match:
        embed = discord.Embed(
            title=f"Did you mean '{best_match}'?",
            description=f"[{best_match}]({poe_data[best_match]})",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Path of Exile Wiki Lookup")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="No Match Found",
            description="Sorry, I couldn't find anything close to that item name.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Custom update roles command

async def update_roles(ctx, role_menu_message_id):
    try:
        message = await ctx.channel.fetch_message(role_menu_message_id)
    except discord.NotFound:
        await ctx.send("Role menu message not found.")
        return
    except discord.Forbidden:
        await ctx.send("I don't have permission to access the role menu message.")
        return

    for reaction in message.reactions:
        emoji_name = reaction.emoji.name if isinstance(reaction.emoji, discord.PartialEmoji) else reaction.emoji
        if emoji_name in role_assignments:
            role_name = role_assignments[emoji_name]
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role is None:
                await ctx.send(f"Role {role_name} does not exist.")
                continue
            async for user in reaction.users():
                if user.bot:
                    continue
                member = ctx.guild.get_member(user.id)
                if member and role not in member.roles:
                    try:
                        await member.add_roles(role)
                        print(f"Assigned {role_name} role to {member.name}")
                    except discord.Forbidden:
                        print(f"Could not assign role {role_name} to {member.name}. Insufficient permissions.")
                    except Exception as e:
                        print(f"An error occurred while assigning role {role_name} to {member.name}: {e}")
    await ctx.send("Roles have been updated based on reactions.")

# Member list

class MemberListView(View):
    def __init__(self, members, active_role, inactive_role, role_dates, per_page=20):
        super().__init__(timeout=None)
        self.members = members
        self.active_role = active_role
        self.inactive_role = inactive_role
        self.role_dates = role_dates
        self.per_page = per_page
        self.page = 0
        self.total_pages = (len(members) - 1) // per_page + 1

    def generate_page(self):
        start = self.page * self.per_page
        end = start + self.per_page
        current_members = self.members[start:end]
        active_count = sum(1 for member in self.members if self.active_role in member.roles)
        inactive_count = len(self.members) - active_count
        member_status = [
            f"{index + 1}. {member.name} - " +
            f"{'Active' if self.active_role in member.roles else 'Inactive'} - " +
            f"{self.role_dates.get(str(member.id), {}).get('active_role_date', 'null') if self.active_role in member.roles else 'null'}"
            for index, member in enumerate(current_members, start=start)
        ]
        header = f"Active: {active_count}, Inactive: {inactive_count}\n"
        return header + "\n".join(member_status)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button_callback(self, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button_callback(self, interaction: discord.Interaction):
        if self.page < self.total_pages - 1:
            self.page += 1
            await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Member List",
            description=self.generate_page(),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page {self.page + 1} of {self.total_pages}")
        await interaction.response.edit_message(embed=embed, view=self)

# Bot setup and commands

intents = discord.Intents.default()
intents.reactions = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

with open('poe_data.json', 'r') as f:
    poe_data = json.load(f)

@bot.event
async def on_ready():
    print(f'{bot.user} is connected and ready!')

@bot.command(name='create_global_role_menu')
async def create_global_role_menu_command(ctx):
    global global_role_menu_message_id
    global_role_menu_message_id = await create_global_role_menu(ctx, bot)
    save_data(role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id)
    load_into_dicts()

@bot.command(name='create_temp_role_menu')
async def create_temp_role_menu_command(ctx):
    global temp_role_menu_message_id
    temp_role_menu_message_id = await create_temp_role_menu(ctx, bot)
    save_data(role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id)
    load_into_dicts()

@bot.command(name='create_poe2_role_menu')
async def create_poe2_role_menu_command(ctx):
    global poe2_role_menu_message_id
    poe2_role_menu_message_id = await create_poe2_role_menu(ctx, bot)
    save_data(role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id)
    load_into_dicts()

@bot.command(name='create_role_menu')
async def create_role_menu_command(ctx):
    global role_menu_message_id
    role_menu_message_id = await create_role_menu(ctx, bot)
    save_data(role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id)
    load_into_dicts()

@bot.command(name='create_inactive_menu')
async def create_inactive_menu_command(ctx):
    global special_role_menu_message_id
    special_role_menu_message_id = await inactive_menu(ctx)
    save_data(role_menu_message_id, special_role_menu_message_id, global_role_menu_message_id, temp_role_menu_message_id, poe2_role_menu_message_id)
    load_into_dicts()

@bot.event
async def on_message(message):
    global waiting, giveaway_log_messages
    inactive_role = discord.utils.get(message.guild.roles, name="Inactive")
    active_role = discord.utils.get(message.guild.roles, name="Active")
    if message.author == bot.user:
        return

    elif message.author.id == 294882584201003009 and "congratulations" in message.content.lower():
        giveaway_log_messages = await lotto_check(bot, message, giveaway_log_messages)
        load_into_dicts()

    elif inactive_role in message.author.roles and not waiting:
        specific_role = discord.utils.get(message.guild.roles, id=1158834836161691810)
        if specific_role not in message.author.roles:
            return
        try:
            if inactive_role in message.author.roles:
                await message.author.remove_roles(inactive_role)
                await message.author.add_roles(active_role)
                print(f"Updated {message.author.name} from 'Inactive' to 'Active'.")
            elif active_role not in message.author.roles:
                await message.author.add_roles(active_role)
                print(f"Added 'Active' role to {message.author.name}.")
            data_dates = load_role_dates()
            data_dates[str(message.author.id)] = {
                "username": message.author.name,
                "active_role_date": datetime.datetime.now().strftime("%m/%d/%Y")
            }
            save_role_dates(data_dates)
        except discord.Forbidden:
            print(f"Could not update roles for {message.author.name} due to insufficient permissions.")
        except Exception as e:
            print(f"An error occurred while processing {message.author.name}: {e}")
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    global waiting, giveaway_log_messages
    if payload.user_id == bot.user.id:
        return
    guild = bot.get_guild(payload.guild_id) if payload.guild_id else None
    user = guild.get_member(payload.user_id) if guild else await bot.fetch_user(payload.user_id)
    if payload.message_id == role_menu_message_id:
        await role_menu_reacts(payload, guild, user)
        load_into_dicts()
    elif payload.message_id == temp_role_menu_message_id:
        await temp_role_menu_reacts_add(payload, user, guild)
        load_into_dicts()
    elif payload.message_id == global_role_menu_message_id:
        await global_role_menu_reacts(payload, guild, user)
        load_into_dicts()
    elif payload.message_id == special_role_menu_message_id and payload.emoji.name == '🔄' and (user == guild.owner or user.id == 1044685722021539860):
        guild = bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        waiting = True
        await inactivity_reaction(bot, payload, guild, user, "Inactive", "Active")
        waiting = False
    elif payload.message_id == poe2_role_menu_message_id:
        await poe2_role_menu_reacts(payload, guild, user)

@bot.event
async def on_reaction_add(reaction, user):
    if user.id == bot.user.id:
        return
    if isinstance(reaction.message.channel, discord.DMChannel):
        await DM_react(reaction, bot, user, giveaway_log_messages)
        load_into_dicts()

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    if payload.message_id == role_menu_message_id:
        await role_menu_reacts_remove(payload, user, guild)
        load_into_dicts()
    elif payload.message_id == temp_role_menu_message_id:
        await temp_role_menu_reacts_remove(payload, user, guild)
        load_into_dicts()
    elif payload.message_id == global_role_menu_message_id:
        await global_role_menu_reacts_remove(payload, user, guild)
        load_into_dicts()
    elif payload.message_id == poe2_role_menu_message_id:
        await poe2_role_menu_reacts_remove(payload, user, guild)
        load_into_dicts()

@bot.command(name="wiki")
async def wiki_command(ctx, *, query: str):
    await wiki(ctx, query)

@bot.command(name="wiki2")
async def wiki2_command(ctx, *, query: str):
    await wiki2(ctx, query)

@bot.command(name="wikifromdatabase")
async def wikifromdatabase_command(ctx, *, item_name: str):
    await wikifromdatabase(ctx, item_name, poe_data)

@bot.command(name="customcommand")
async def customcommand(ctx, *, command: str):
    if ctx.author.id != 1044685722021539860:
        return
    else:
        if command == "updateroles":
            await update_roles(ctx, role_menu_message_id)

@bot.command(name="claimed")
async def claimed_command(ctx):
    await claim(ctx, bot)
    load_into_dicts()

@bot.command()
async def stats(ctx, odds: str, trials: int, successes: int = None):
    try:
        numerator, denominator = map(int, odds.split('/'))
        probability = numerator / denominator
        if successes is not None:
            p_success = math.comb(trials, successes) * (probability ** successes) * ((1 - probability) ** (trials - successes))
            result = f"The probability of getting exactly {successes} successes in {trials} trials with odds {odds} is ({p_success * 100:.2f}%)."
        else:
            p_no_success = (1 - probability) ** trials
            p_at_least_one = 1 - p_no_success
            result = f"The probability of getting at least 1 success in {trials} trials with odds {odds} is ({p_at_least_one * 100:.2f}%)."
        await ctx.send(result)
    except ValueError:
        await ctx.send("Invalid input, Please use the format `!stats 1/50 100 [optional: successes]`.")

@bot.command(name="list_members")
async def list_members_command(ctx):
    guild = ctx.guild
    specific_role = discord.utils.get(guild.roles, id=1158834836161691810)
    active_role = discord.utils.get(guild.roles, name="Active")
    inactive_role = discord.utils.get(guild.roles, name="Inactive")
    if not specific_role:
        await ctx.send("The specified role does not exist in this server.")
        return
    if not active_role or not inactive_role:
        await ctx.send("Active or Inactive role does not exist in this server.")
        return
    members_with_role = [member for member in guild.members if specific_role in member.roles]
    members_sorted = sorted(members_with_role, key=lambda m: m.name)
    if not members_sorted:
        await ctx.send("No members with the specified role were found.")
        return
    role_dates = load_role_dates()
    view = MemberListView(members_sorted, active_role, inactive_role, role_dates)
    embed = discord.Embed(
        title="Member List",
        description=view.generate_page(),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Page 1 of {view.total_pages}")
    await ctx.send(embed=embed, view=view)

@bot.command()
async def resetdates(ctx):
    reset_role_dates()
    await ctx.send("All active role dates have been set to null.")


load_into_dicts()
bot.run(TOKEN)
