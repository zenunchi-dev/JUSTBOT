import os
from dotenv import load_dotenv  
load_dotenv()                   

import discord
from discord.ext import commands
import asyncio
import datetime
import json
import random
from datetime import UTC, timedelta
import time  # pentru cooldown XP
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
# ===================================================

# ================= Încărcare token =================
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN nu este setat în variabile de mediu!")

# ================= BAZA DE DATE =================
def load_data():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"warnings": {}, "levels": {}, "invites": {}}, f)
    with open("data.json") as f:
        data = json.load(f)
        if "invites" not in data: data["invites"] = {}
        return data

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= CONFIGURARE BOT =================
intents = discord.Intents.all() 

bot = commands.Bot(command_prefix="#", intents=intents)

# Cache pentru invitații
invites_cache = {}

# ================= ID-URI ACTUALIZATE =================
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

# NOILE ID-URI PENTRU INVITES
INVITE_LOG_CH_ID = 1473636271891943456
INVITE_REWARD_ROLE_ID = 1482140556867010764
MEMBER_ROLE_ALLOWED = 1438996505964052601 

BAN_ROLE_ID = 1482386779846869094 # Rolul care se dă în loc de ban

MY_GIF = "https://media.discordapp.net/attachments/1440112412266205194/1461843437694484684/f63ce9f5-d6b6-47d9-91f0-eb1e166ab02a.gif"
BOOST_GIF = "https://media.tenor.com/7123Lof2_mEAAAAC/make-it-rain-money.gif"
CUSTOM_EMOJI = "<:emoji_16:1448074879961268451>"

VERSION = "5.0"
CHANGES_LOG = """
✅ **Permisiuni Update**: Rolurile Helper și Staff au acum acces diferențiat la comenzi.
"""

XP_COOLDOWN = 8
last_xp_time = {}  

# ================= FUNCȚIE SYNC PERMISIUNI BAN =================

async def sync_ban_role_permissions(guild):
    """Setează automat permisiunea de a NU vedea canalele pentru rolul de ban."""
    role = guild.get_role(BAN_ROLE_ID)
    if not role:
        return
    
    for channel in guild.channels:
        if channel.overwrites_for(role).read_messages is not False:
            try:
                await channel.set_permissions(role, view_channel=False, send_messages=False, connect=False)
            except:
                continue

# ================= CLASE UI PERSISTENTE =================

class SelfRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def toggle_role(self, interaction: discord.Interaction, role_id: int):
        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("❌ Rolul nu a fost găsit!", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Rolul {role.name} a fost scos.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rolul {role.name} a fost adăugat!", ephemeral=True)

    @discord.ui.button(label="18+", style=discord.ButtonStyle.secondary, custom_id="role_18plus", emoji="<:18Plus:1455072960812548157>")
    async def role_18plus(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455073585306800128)

    @discord.ui.button(label="Under 18", style=discord.ButtonStyle.secondary, custom_id="role_under18", emoji="<:Under18:1455078800307126334>")
    async def role_under18(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455080987146064014)

    @discord.ui.button(label="Girl", style=discord.ButtonStyle.secondary, custom_id="role_girl", emoji="<:emoji_15:1448074655775719444>")
    async def role_girl(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455080720409034907)

    @discord.ui.button(label="Boy", style=discord.ButtonStyle.secondary, custom_id="role_boy", emoji="<:emoji_16:1448074879961268451>")
    async def role_boy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455079548445130883)

    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.secondary, custom_id="role_giveaway", emoji="<a:purplepresent:1455082484604604531>")
    async def role_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455081282009694258)

    @discord.ui.button(label="Wake Up", style=discord.ButtonStyle.secondary, custom_id="role_wakeup", emoji="<:__:1451889127581548648>")
    async def role_wakeup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455082758094327922)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        
        channel_name = f"{category_name}-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        
        if existing_channel:
            return await interaction.response.send_message(f"❌ Ai deja un ticket de acest tip deschis: {existing_channel.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        
        embed = discord.Embed(
            title=f"🎫 Ticket: {category_name.upper()}", 
            description=f"Salut {interaction.user.mention}!\nAi deschis un ticket pentru: **{category_name.replace('-', ' ')}**.\nEchipa Staff va prelua cererea ta în cel mai scurt timp.\n\nFolosește butonul de mai jos pentru a închide tichetul.", 
            color=0x2b2d31
        )
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket creat: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="REPORT STAFF", style=discord.ButtonStyle.secondary, custom_id="t_staff", emoji="⚠️")
    async def t_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "staff")

    @discord.ui.button(label="REPORT MEMBER", style=discord.ButtonStyle.secondary, custom_id="t_member", emoji="👥")
    async def t_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "member")

    @discord.ui.button(label="BAN REPORTS", style=discord.ButtonStyle.secondary, custom_id="t_ban", emoji="🚫")
    async def t_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "ban")

    @discord.ui.button(label="CONTACT OWNER", style=discord.ButtonStyle.secondary, custom_id="t_owner", emoji="👑")
    async def t_owner(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "owner")

    @discord.ui.button(label="INFO & OTHERS", style=discord.ButtonStyle.secondary, custom_id="t_info", emoji="❓")
    async def t_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "info")

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Închide Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tichetul se va închide în 5 secunde...")
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ================= SISTEM APPLY =================

class ApplyActionView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        staff_role = interaction.guild.get_role(STAFF_ID)
        if not staff_role or interaction.user.top_role.position <= staff_role.position:
            await interaction.response.send_message("❌ Doar conducerea poate folosi aceste butoane!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Acceptă (Trial)", style=discord.ButtonStyle.success, custom_id="apply_accept_btn")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.applicant_id)
        role_trial = guild.get_role(TRIAL_ID)
        
        if member and role_trial:
            await member.add_roles(role_trial)
            try: await member.send(f"🎉 Cererea ta de Helper pe **{guild.name}** a fost acceptată! Bine ai venit.")
            except: pass
            await interaction.response.send_message(f"✅ {member.mention} a primit gradul de Trial. Canalul se va închide în 10 secunde.")
            await asyncio.sleep(10)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Utilizatorul nu mai este pe server sau rolul Trial nu există.", ephemeral=True)

    @discord.ui.button(label="Respinge", style=discord.ButtonStyle.danger, custom_id="apply_deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.applicant_id)
        role_reject = guild.get_role(REJECT_ROLE_ID)
        
        if member:
            if role_reject:
                await member.add_roles(role_reject)
            try: await member.send(f"❌ Cererea ta de Helper pe **{interaction.guild.name}** a fost respinsă.")
            except: pass
        await interaction.response.send_message("🚫 Cerere respinsă. Canalul se va închide în 5 secunde.")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ApplyModal(discord.ui.Modal, title="Formular Aplicare Helper"):
    nume = discord.ui.TextInput(label="Nume și Vârstă", placeholder="Ex: Andrei, 19 ani", min_length=3)
    experienta = discord.ui.TextInput(label="Experiență", style=discord.TextStyle.paragraph, placeholder="Unde ai mai fost Staff?")
    motiv = discord.ui.TextInput(label="De ce tu?", style=discord.TextStyle.paragraph, placeholder="Cu ce poți ajuta comunitatea?")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(f"apply-{interaction.user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(title=f"📝 Cerere Helper: {interaction.user.name}", color=0x3498db, timestamp=datetime.datetime.now(UTC))
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Aplicant", value=interaction.user.mention)
        embed.add_field(name="🎂 Nume/Vârstă", value=self.nume.value, inline=False)
        embed.add_field(name="🧠 Experiență", value=self.experienta.value, inline=False)
        embed.add_field(name="✨ Motiv", value=self.motiv.value, inline=False)
        
        await channel.send(content=f"🔔 <@&{STAFF_ID}>", embed=embed, view=ApplyActionView(interaction.user.id))
        await interaction.response.send_message(f"✅ Canalul tău de aplicare a fost creat: {channel.mention}", ephemeral=True)

class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="HELPER APPLY", style=discord.ButtonStyle.success, custom_id="main_apply_btn", emoji="📝")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())

# ================= FUNCȚII AJUTĂTOARE =================

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

# ================= VERIFICĂRI PERMISIUNI =================

def is_trial_up():
    async def pred(ctx):
        role = ctx.guild.get_role(TRIAL_ID)
        return role and ctx.author.top_role.position >= role.position
    return commands.check(pred)

def is_staff_up():
    async def pred(ctx):
        role = ctx.guild.get_role(STAFF_ID)
        return role and ctx.author.top_role.position >= role.position
    return commands.check(pred)

def is_above_staff():
    async def pred(ctx):
        role_staff = ctx.guild.get_role(STAFF_ID)
        return role_staff and ctx.author.top_role.position > role_staff.position
    return commands.check(pred)

# ================= COMENZI STAFF (ROL STAFF) =================

@bot.command()
@is_staff_up()
async def kick(ctx, member: discord.Member, *, reason="Nespecificat"):
    if member.top_role >= ctx.author.top_role:
        return await ctx.send("❌ Nu poți da kick cuiva cu grad egal sau mai mare!", delete_after=5)
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.name} a primit kick.", delete_after=5)
    await send_sanction_log("Kick", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def ban(ctx, member: discord.Member, *, reason="Nespecificat"):
    if member.top_role >= ctx.author.top_role:
        return await ctx.send("❌ Nu poți sancționa pe cineva cu grad egal sau mai mare!", delete_after=5)
    role = ctx.guild.get_role(BAN_ROLE_ID)
    if role:
        await member.add_roles(role, reason=reason)
        await sync_ban_role_permissions(ctx.guild)
        await ctx.send(f"✅ {member.mention} a primit rolul de Ban.", delete_after=5)
        await send_sanction_log("Ban (Role)", ctx.author, member, reason)
    else:
        await ctx.send("❌ Rolul de ban nu a fost găsit!", delete_after=5)

@bot.command()
@is_staff_up()
async def unban(ctx, id: int):
    try:
        user = await bot.fetch_user(id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ {user.name} a primit unban.", delete_after=5)
    except:
        member = ctx.guild.get_member(id)
        if member:
            role = ctx.guild.get_role(BAN_ROLE_ID)
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"✅ Rol ban scos lui {member.name}.", delete_after=5)

@bot.command()
@is_staff_up()
async def warn(ctx, member: discord.Member, *, reason="Nespecificat"):
    data = load_data()
    uid = str(member.id)
    data["warnings"][uid] = data["warnings"].get(uid, 0) + 1
    count = data["warnings"][uid]
    save_data(data)
    if count >= 3:
        role = ctx.guild.get_role(BAN_ROLE_ID)
        if role: 
            await member.add_roles(role)
            await sync_ban_role_permissions(ctx.guild)
        await ctx.send(f"⛔ {member.mention} Ban automat (3/3).")
    else:
        warn_roles = [WARN1_ROLE_ID, W2_ID, W3_ID]
        if count <= len(warn_roles):
            role = ctx.guild.get_role(warn_roles[count-1])
            if role: await member.add_roles(role)
        await ctx.send(f"⚠️ {member.mention} warn {count}/3.", delete_after=5)
        await send_sanction_log(f"Warn {count}/3", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unwarn(ctx, member: discord.Member):
    data = load_data()
    uid = str(member.id)
    if uid in data["warnings"]: del data["warnings"][uid]
    save_data(data)
    for rid in [WARN1_ROLE_ID, W2_ID, W3_ID]:
        role = ctx.guild.get_role(rid)
        if role and role in member.roles: await member.remove_roles(role)
    await ctx.send(f"✅ Warns resetate.", delete_after=5)

@bot.command()
@is_staff_up()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    if role.position >= ctx.author.top_role.position:
        return await ctx.send("❌ Nu poți pune un rol egal sau mai mare!", delete_after=5)
    await member.add_roles(role)
    await ctx.send(f"✅ Adăugat rol {role.name}.", delete_after=5)

@bot.command()
@is_staff_up()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    if role.position >= ctx.author.top_role.position:
        return await ctx.send("❌ Nu poți scoate un rol egal sau mai mare!", delete_after=5)
    await member.remove_roles(role)
    await ctx.send(f"✅ Scos rol {role.name}.", delete_after=5)

# ================= COMENZI HELPER (ROL TRIAL) =================

@bot.command()
@is_trial_up()
async def mute(ctx, member: discord.Member, duration: str, *, reason="Nespecificat"):
    try:
        unit = duration[-1].lower()
        amt = int(duration[:-1])
        seconds = {"s": amt, "m": amt*60, "h": amt*3600, "d": amt*86400}.get(unit, 3600)
        await member.timeout(timedelta(seconds=seconds), reason=reason)
        await ctx.send(f"🔇 {member.mention} mute {duration}.", delete_after=5)
        await send_sanction_log("Mute", ctx.author, member, reason, duration)
    except:
        await ctx.send("❌ Eroare la format (ex: 10m, 1h).")

@bot.command()
@is_trial_up()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 {member.mention} unmute.", delete_after=5)

@bot.command()
@is_trial_up()
async def vmute(ctx, member: discord.Member, *, reason="Nespecificat"):
    if member.voice:
        await member.edit(mute=True)
        await ctx.send(f"🔇 {member.name} mute pe voice.", delete_after=5)

@bot.command()
@is_trial_up()
async def vunmute(ctx, member: discord.Member):
    if member.voice:
        await member.edit(mute=False)
        await ctx.send(f"🔊 {member.name} unmute pe voice.", delete_after=5)

@bot.command()
@is_trial_up()
async def warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    count = data["warnings"].get(str(member.id), 0)
    await ctx.send(f"🔍 {member.name} are {count}/3 warn-uri.", delete_after=8)

@bot.command()
@is_trial_up()
async def comenzi(ctx):
    if ctx.channel.id != STAFF_CMD_CHANNEL: return
    emb = discord.Embed(title="📜 Comenzi Staff", color=0x2b2d31)
    emb.add_field(name="Helper (Trial)", value="#mute, #unmute, #vmute, #vunmute, #warns", inline=False)
    emb.add_field(name="Staff", value="#kick, #ban, #unban, #warn, #unwarn, #addrole, #removerole", inline=False)
    await ctx.send(embed=emb)

# ================= ALTE COMENZI (CONFIG / ADMIN) =================

@bot.command()
@is_above_staff()
async def clear(ctx, amount: int = 100):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 Șters {amount} mesaje.", delete_after=5)

@bot.command()
@is_above_staff()
async def setup_apply(ctx):
    await ctx.send(embed=discord.Embed(title="✨ APLICĂ HELPER", description="Apasă butonul pentru formular"), view=ApplyView())

@bot.command()
@is_above_staff()
async def setup_roles(ctx):
    await ctx.send("Panou Roluri", view=SelfRoleView())

@bot.command()
@is_above_staff()
async def setup_ticket(ctx):
    await ctx.send("Panou Tichete", view=TicketView())

@bot.command()
@is_above_staff()
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Canal blocat.")

@bot.command()
@is_above_staff()
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Canal deblocat.")

@bot.command()
@is_above_staff()
async def slow(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"⏳ Slowmode: {seconds}s")

@bot.command()
@is_above_staff()
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

# ================= FUNCȚII INVITE TRACKER =================

async def get_inviter(member):
    guild = member.guild
    before_invs = invites_cache.get(guild.id, {})
    try:
        after_invs = await guild.invites()
    except:
        return None
    inviter = None
    for inv in after_invs:
        if inv.code in before_invs:
            if inv.uses > before_invs[inv.code]:
                inviter = inv.inviter
                break
        elif inv.uses > 0: 
            inviter = inv.inviter
            break
    invites_cache[guild.id] = {inv.code: inv.uses for inv in after_invs}
    return inviter

@bot.command()
async def invites(ctx, member: discord.Member = None):
    if ctx.channel.id != BOT_COMMANDS_CH: return
    target = member or ctx.author
    data = load_data()
    stats = data["invites"].get(str(target.id), {"total": 0, "fake": 0, "leaves": 0})
    await ctx.send(f"📩 {target.name}: {stats['total']} reale, {stats['fake']} fake.")

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    if ctx.channel.id != BOT_COMMANDS_CH: return
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def serverinfo(ctx):
    if ctx.channel.id != BOT_COMMANDS_CH: return
    await ctx.send(f"Server: {ctx.guild.name} | Membri: {ctx.guild.member_count}")

# ================= EVENIMENTE AUTOMATE =================

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    for g in bot.guilds: 
        try:
            invs = await g.invites()
            invites_cache[g.id] = {inv.code: inv.uses for inv in invs}
            await sync_ban_role_permissions(g)
        except: pass
    bot.add_view(TicketView()); bot.add_view(CloseTicketView()); bot.add_view(SelfRoleView()); bot.add_view(ApplyView())

@bot.event
async def on_member_join(member):
    inviter = await get_inviter(member)
    if inviter and not inviter.bot:
        data = load_data()
        inv_id = str(inviter.id)
        if inv_id not in data["invites"]:
            data["invites"][inv_id] = {"total": 0, "fake": 0, "leaves": 0, "invited_list": []}
        is_fake = (datetime.datetime.now(UTC) - member.created_at).days < 2
        if is_fake:
            data["invites"][inv_id]["fake"] += 1
        else:
            data["invites"][inv_id]["total"] += 1
            data["invites"][inv_id]["invited_list"].append(member.id)
            if data["invites"][inv_id]["total"] >= 25:
                role = member.guild.get_role(INVITE_REWARD_ROLE_ID)
                inv_member = member.guild.get_member(inviter.id)
                if role and inv_member: await inv_member.add_roles(role)
        save_data(data)
    channel = bot.get_channel(WELCOME_CH_ID)
    if channel: await channel.send(f"🎉 Bun venit {member.mention}!")

@bot.event
async def on_member_remove(member):
    data = load_data()
    for inv_id, stats in data["invites"].items():
        if member.id in stats.get("invited_list", []):
            stats["invited_list"].remove(member.id)
            stats["total"] -= 1
            stats["leaves"] += 1
            save_data(data)
            break

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    
    # Anti-link logic
    content_low = message.content.lower()
    if ("http" in content_low or "discord.gg/" in content_low) and not any(x in content_low for x in ["youtube.com", "youtu.be"]):
        trial_role = message.guild.get_role(TRIAL_ID)
        if not (trial_role and message.author.top_role.position >= trial_role.position):
            try: await message.delete(); await message.channel.send(f"❌ {message.author.mention}, link-uri interzise!", delete_after=5)
            except: pass
            return

    # XP System
    uid = str(message.author.id)
    now = time.time()
    if uid not in last_xp_time or now - last_xp_time[uid] > XP_COOLDOWN:
        last_xp_time[uid] = now
        data = load_data()
        if uid not in data["levels"]: data["levels"][uid] = {"xp": 0, "level": 1}
        data["levels"][uid]["xp"] += 10
        save_data(data)

    # Auto Reply
    if message.channel.id == CHAT_CHANNEL_ID:
        low = message.content.lower()
        if low in ["salut", "sall", "buna"]: await message.channel.send(f"Salut {message.author.mention}!")

    await bot.process_commands(message)

keep_alive()
bot.run(TOKEN)