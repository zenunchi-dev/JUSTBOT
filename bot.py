import os
from dotenv import load_dotenv  
load_dotenv()                   

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
import json
import random
from datetime import UTC, timedelta
from flask import Flask
from threading import Thread

# ================= KEEP-ALIVE 24/7 =================
app = Flask('')

@app.route('/')
def home():
    return "Botul este Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= BAZA DE DATE =================
def load_data():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"warnings": {}, "invites": {}}, f)
    with open("data.json") as f:
        data = json.load(f)
        if "invites" not in data: data["invites"] = {}
        return data

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= CONFIGURARE BOT =================
intents = discord.Intents.all() 
TOKEN = os.getenv("DISCORD_TOKEN")

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="#", intents=intents)

    async def setup_hook(self):
        self.add_view(TicketView())
        self.add_view(CloseTicketView())
        self.add_view(SelfRoleView())
        self.add_view(ApplyView())
        self.add_view(ApplyActionView(0))

bot = MyBot()
invites_cache = {}

# ================= ID-URI =================
TRIAL_ID = 1444684277110542368
STAFF_ID = 1325279044396126261
REJECT_ROLE_ID = 1477702698936701019
BOOST_ROLE_MIN = 1411137733975347293  
BOOST_CH_ID = 1476419627482611762      
BENEFITS_CH_ID = 1476425405304012843   
LOG_CH_ID = 1444796054313766922         
BAN_LOG_CH_ID = 1436891992150769664     
MOD_LOG_CH_ID = 1464383652866556039     
WELCOME_CH_ID = 1325279589915955321 
BOT_COMMANDS_CH = 1436559828859359373
CHAT_CHANNEL_ID = 1436554745622827258
STAFF_CMD_CHANNEL = 1449824932371632248
UPDATE_LOG_CH_ID = 1477448913827921922 
TICKET_CATEGORY_ID = 1444684157833056256 
WARN1_ROLE_ID = 1436538867850416289
W2_ID = 1436538789311811624
W3_ID = 1450009480417902796
INVITE_LOG_CH_ID = 1473636271891943456
INVITE_REWARD_ROLE_ID = 1482140556867010764
MEMBER_ROLE_ALLOWED = 1438996505964052601 
BAN_ROLE_ID = 1482386779846869094 
CLEAR_100_ROLES = [1437845412383031467, 1411137733975347293, 1436506319459844249, 1473101230103330925, 1476422451545116853, 1478173655832727672, 1478173861144035449]

MY_GIF = "https://media.discordapp.net/attachments/1440112412266205194/1461843437694484684/f63ce9f5-d6b6-47d9-91f0-eb1e166ab02a.gif"
BOOST_GIF = "https://media.tenor.com/7123Lof2_mEAAAAC/make-it-rain-money.gif"
CUSTOM_EMOJI = "<:emoji_16:1448074879961268451>"
VERSION = "4.9"
CHANGES_LOG = "✅ Conversie completă la Slash Commands (/)"

# ================= FUNCȚII LOGICĂ =================

async def sync_ban_role_permissions(guild):
    role = guild.get_role(BAN_ROLE_ID)
    if not role: return
    for channel in guild.channels:
        if channel.overwrites_for(role).read_messages is not False:
            try: await channel.set_permissions(role, view_channel=False, send_messages=False, connect=False)
            except: continue

async def send_boost_announcement(member, guild):
    channel = bot.get_channel(BOOST_CH_ID)
    if not channel: return
    content = f"{member.mention} is RICH ASFFF!! 💸"
    embed = discord.Embed(title=f"{CUSTOM_EMOJI} **Another Star on the Board!**", color=0xf47fff, timestamp=datetime.datetime.now(UTC))
    embed.description = (f"💎 | A huge shoutout to **{member.name}** for boosting!\n\n"
                        f"✨ | You just made the server even better.\n"
                        f"📈 | We are now at **{guild.premium_subscription_count}** boosts!\n\n"
                        f"🎁 | Claim your rewards here: <#{BENEFITS_CH_ID}>")
    embed.set_image(url=BOOST_GIF)
    embed.set_footer(text=f"Server Level: {guild.premium_tier} • We appreciate you!")
    await channel.send(content=content, embed=embed)

async def send_sanction_log(action, staff, member, reason="Nespecificat", duration=None):
    act_low = action.lower()
    if "ban" in act_low: target_ch_id = BAN_LOG_CH_ID
    elif any(x in act_low for x in ["mute", "kick", "warn", "unmute", "unwarn", "lock", "unlock", "slow", "vmute"]):
        target_ch_id = MOD_LOG_CH_ID
    else: target_ch_id = LOG_CH_ID
    channel = bot.get_channel(target_ch_id)
    if not channel: return
    embed = discord.Embed(title=f"⛔ {action} | {member.name if hasattr(member, 'name') else str(member)}", color=0x2b2d31, timestamp=datetime.datetime.now(UTC))
    embed.set_thumbnail(url=MY_GIF)
    embed.add_field(name="👤 User", value=member.mention if hasattr(member, 'mention') else str(member), inline=True)
    embed.add_field(name="🛡️ Staff", value=staff.mention if staff else "@Sistem Automat", inline=True)
    embed.add_field(name="📄 Motiv", value=reason if reason else "Nespecificat", inline=True)
    if duration: embed.add_field(name="⏳ Detalii", value=duration, inline=True)
    embed.set_footer(text=f"ID: {member.id if hasattr(member, 'id') else 'N/A'}")
    await channel.send(embed=embed)

# ================= CLASE UI =================

class SelfRoleView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def toggle_role(self, interaction: discord.Interaction, role_id: int):
        role = interaction.guild.get_role(role_id)
        if not role: return await interaction.response.send_message("❌ Rolul nu a fost găsit!", ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Rolul {role.name} a fost scos.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rolul {role.name} a fost adăugat!", ephemeral=True)

    @discord.ui.button(label="18+", style=discord.ButtonStyle.secondary, custom_id="role_18plus", emoji="<:18Plus:1455072960812548157>")
    async def role_18plus(self, interaction, button): await self.toggle_role(interaction, 1455073585306800128)
    @discord.ui.button(label="Under 18", style=discord.ButtonStyle.secondary, custom_id="role_under18", emoji="<:Under18:1455078800307126334>")
    async def role_under18(self, interaction, button): await self.toggle_role(interaction, 1455080987146064014)
    @discord.ui.button(label="Girl", style=discord.ButtonStyle.secondary, custom_id="role_girl", emoji="<:emoji_15:1448074655775719444>")
    async def role_girl(self, interaction, button): await self.toggle_role(interaction, 1455080720409034907)
    @discord.ui.button(label="Boy", style=discord.ButtonStyle.secondary, custom_id="role_boy", emoji="<:emoji_16:1448074879961268451>")
    async def role_boy(self, interaction, button): await self.toggle_role(interaction, 1455079548445130883)
    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.secondary, custom_id="role_giveaway", emoji="<a:purplepresent:1455082484604604531>")
    async def role_giveaway(self, interaction, button): await self.toggle_role(interaction, 1455081282009694258)
    @discord.ui.button(label="Wake Up", style=discord.ButtonStyle.secondary, custom_id="role_wakeup", emoji="<:__:1451889127581548648>")
    async def role_wakeup(self, interaction, button): await self.toggle_role(interaction, 1455082758094327922)

class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        channel_name = f"{category_name}-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel: return await interaction.response.send_message(f"❌ Ai deja un ticket deschis: {existing_channel.mention}", ephemeral=True)
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        embed = discord.Embed(title=f"🎫 Ticket: {category_name.upper()}", description=f"Salut {interaction.user.mention}!", color=0x2b2d31)
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket creat: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="REPORT STAFF", style=discord.ButtonStyle.secondary, custom_id="t_staff", emoji="⚠️")
    async def t_staff(self, interaction, button): await self.create_ticket(interaction, "staff")
    @discord.ui.button(label="REPORT MEMBER", style=discord.ButtonStyle.secondary, custom_id="t_member", emoji="👥")
    async def t_member(self, interaction, button): await self.create_ticket(interaction, "member")
    @discord.ui.button(label="BAN REPORTS", style=discord.ButtonStyle.secondary, custom_id="t_ban", emoji="🚫")
    async def t_ban(self, interaction, button): await self.create_ticket(interaction, "ban")
    @discord.ui.button(label="CONTACT OWNER", style=discord.ButtonStyle.secondary, custom_id="t_owner", emoji="👑")
    async def t_owner(self, interaction, button): await self.create_ticket(interaction, "owner")
    @discord.ui.button(label="INFO & OTHERS", style=discord.ButtonStyle.secondary, custom_id="t_info", emoji="❓")
    async def t_info(self, interaction, button): await self.create_ticket(interaction, "info")

class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Închide Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, interaction, button):
        await interaction.response.send_message("Tichetul se va închide în 5 secunde...")
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

class ApplyActionView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
    @discord.ui.button(label="Acceptă (Trial)", style=discord.ButtonStyle.success, custom_id="apply_accept_btn")
    async def accept(self, interaction, button):
        member = interaction.guild.get_member(self.applicant_id)
        role = interaction.guild.get_role(TRIAL_ID)
        if member and role:
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ {member.mention} a primit Trial.")
            await asyncio.sleep(5)
            await interaction.channel.delete()
    @discord.ui.button(label="Respinge", style=discord.ButtonStyle.danger, custom_id="apply_deny_btn")
    async def deny(self, interaction, button):
        await interaction.response.send_message("🚫 Respins.")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ApplyModal(discord.ui.Modal, title="Formular Aplicare Helper"):
    nume = discord.ui.TextInput(label="Nume și Vârstă")
    experienta = discord.ui.TextInput(label="Experiență", style=discord.TextStyle.paragraph)
    motiv = discord.ui.TextInput(label="De ce tu?", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(f"apply-{interaction.user.name}", category=category)
        embed = discord.Embed(title=f"📝 Cerere Helper: {interaction.user.name}")
        embed.add_field(name="Nume", value=self.nume.value)
        embed.add_field(name="Experiență", value=self.experienta.value)
        await channel.send(embed=embed, view=ApplyActionView(interaction.user.id))
        await interaction.response.send_message("✅ Cerere trimisă!", ephemeral=True)

class ApplyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="HELPER APPLY", style=discord.ButtonStyle.success, custom_id="main_apply_btn", emoji="📝")
    async def apply_button(self, interaction, button): await interaction.response.send_modal(ApplyModal())

# ================= SLASH COMMANDS =================

@bot.command()
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Slash Commands sincronizate!")

@bot.tree.command(name="kick", description="Kick un membru")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Nespecificat"):
    if interaction.user.top_role.position < interaction.guild.get_role(STAFF_ID).position:
        return await interaction.response.send_message("❌ Nu ești staff!", ephemeral=True)
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ {member.name} a primit kick.")
    await send_sanction_log("Kick", interaction.user, member, reason)

@bot.tree.command(name="ban", description="Ban (Rol) un membru")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Nespecificat"):
    role = interaction.guild.get_role(BAN_ROLE_ID)
    await member.add_roles(role)
    await sync_ban_role_permissions(interaction.guild)
    await interaction.response.send_message(f"✅ {member.mention} banat.")
    await send_sanction_log("Ban (Role)", interaction.user, member, reason)

@bot.tree.command(name="mute", description="Timeout un membru")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Nespecificat"):
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await interaction.response.send_message(f"🔇 {member.mention} mute {minutes}m.")
    await send_sanction_log("Mute", interaction.user, member, reason, f"{minutes}m")

@bot.tree.command(name="unmute", description="Scoate timeout")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 {member.mention} unmute.")

@bot.tree.command(name="clear", description="Șterge mesaje")
async def clear(interaction: discord.Interaction, amount: int):
    can_clear_100 = any(role.id in CLEAR_100_ROLES for role in interaction.user.roles)
    limit = 100 if can_clear_100 else 10
    if amount > limit: return await interaction.response.send_message(f"❌ Max {limit}!", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 {len(deleted)} mesaje șterse.")

@bot.tree.command(name="warn", description="Warn un membru")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Nespecificat"):
    data = load_data()
    uid = str(member.id)
    data["warnings"][uid] = data["warnings"].get(uid, 0) + 1
    count = data["warnings"][uid]
    save_data(data)
    await interaction.response.send_message(f"⚠️ {member.mention} warn {count}/3.")
    await send_sanction_log(f"Warn {count}/3", interaction.user, member, reason)

@bot.tree.command(name="unwarn", description="Resetează warn-uri")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    data = load_data()
    uid = str(member.id)
    if uid in data["warnings"]: del data["warnings"][uid]
    save_data(data)
    await interaction.response.send_message(f"✅ Resetat warn-uri pentru {member.mention}.")

@bot.tree.command(name="invites", description="Vezi invitațiile tale")
async def invites(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    data = load_data()
    stats = data["invites"].get(str(target.id), {"total": 0, "fake": 0, "leaves": 0})
    embed = discord.Embed(title=f"📩 Invites | {target.name}", color=0x2b2d31)
    embed.add_field(name="✅ Reale", value=str(stats["total"]))
    embed.add_field(name="❌ Fake", value=str(stats["fake"]))
    embed.add_field(name="📤 Plecați", value=str(stats["leaves"]))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup_apply", description="Setup panou aplicații")
async def setup_apply(interaction: discord.Interaction):
    await interaction.response.send_message("Panou activat.", ephemeral=True)
    await interaction.channel.send(embed=discord.Embed(title="✨ RECRUTARE HELPER", description="Aplică folosind butonul."), view=ApplyView())

@bot.tree.command(name="setup_roles", description="Setup panou roluri")
async def setup_roles(interaction: discord.Interaction):
    await interaction.response.send_message("Panou roluri activat.", ephemeral=True)
    await interaction.channel.send(embed=discord.Embed(description="🎭 **ALEGE-ȚI ROLURILE**"), view=SelfRoleView())

@bot.tree.command(name="setup_ticket", description="Setup panou ticket")
async def setup_ticket(interaction: discord.Interaction):
    await interaction.response.send_message("Panou ticket activat.", ephemeral=True)
    await interaction.channel.send(embed=discord.Embed(description="🎫 **TICKETS**"), view=TicketView())

@bot.tree.command(name="avatar", description="Vezi avatarul cuiva")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    embed = discord.Embed(title=f"Avatar • {target.name}")
    embed.set_image(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Info server")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"{g.name}", color=0x2b2d31)
    embed.add_field(name="Membri", value=g.member_count)
    embed.add_field(name="Boosts", value=g.premium_subscription_count)
    await interaction.response.send_message(embed=embed)

# ================= EVENIMENTE =================

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Tickets & /commands"))
    for guild in bot.guilds:
        try:
            invs = await guild.invites()
            invites_cache[guild.id] = {inv.code: inv.uses for inv in invs}
            await sync_ban_role_permissions(guild)
        except: pass

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CH_ID)
    if channel:
        embed = discord.Embed(description=f"🎉 Bun venit {member.mention}", color=0x2b2d31)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot: return
    # Logica de prefix #sync rămâne pentru sincronizare manuală
    await bot.process_commands(message)

keep_alive()
bot.run(TOKEN)
