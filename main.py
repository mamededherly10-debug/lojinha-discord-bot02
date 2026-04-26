import discord
from discord.ext import commands
import aiosqlite
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

produtos = {
    "VIP": 10,
    "SKIN": 5,
    "DIAMANTE": 3
}

async def setup_db():
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, saldo INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS estoque (produto TEXT, conteudo TEXT)")
        await db.commit()

async def get_saldo(user_id):
    async with aiosqlite.connect("db.sqlite") as db:
        cur = await db.execute("SELECT saldo FROM users WHERE id=?", (user_id,))
        row = await cur.fetchone()
        if not row:
            await db.execute("INSERT INTO users VALUES (?, ?)", (user_id, 0))
            await db.commit()
            return 0
        return row[0]

async def add_saldo(user_id, valor):
    saldo = await get_saldo(user_id)
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("UPDATE users SET saldo=? WHERE id=?", (saldo+valor, user_id))
        await db.commit()

class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for nome in produtos:
            self.add_item(ComprarButton(nome))

class ComprarButton(discord.ui.Button):
    def __init__(self, produto):
        super().__init__(label=produto, style=discord.ButtonStyle.green)
        self.produto = produto

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        preco = produtos[self.produto]
        saldo = await get_saldo(user_id)

        if saldo < preco:
            await interaction.response.send_message("❌ Saldo insuficiente!", ephemeral=True)
            return

        async with aiosqlite.connect("db.sqlite") as db:
            cur = await db.execute("SELECT conteudo FROM estoque WHERE produto=?", (self.produto,))
            item = await cur.fetchone()

            if not item:
                await interaction.response.send_message("❌ Produto sem estoque!", ephemeral=True)
                return

            await db.execute("DELETE FROM estoque WHERE produto=? LIMIT 1", (self.produto,))
            await db.commit()

        await add_saldo(user_id, -preco)

        await interaction.response.send_message("✅ Compra realizada! Veja seu privado 📩", ephemeral=True)

        try:
            await interaction.user.send(f"📦 Seu produto: {item[0]}")
        except:
            pass

@bot.command()
async def loja(ctx):
    embed = discord.Embed(title="🛒 Loja", color=discord.Color.green())
    for nome, preco in produtos.items():
        embed.add_field(name=nome, value=f"{preco} moedas", inline=False)
    await ctx.send(embed=embed, view=LojaView())

@bot.command()
async def saldo(ctx):
    saldo = await get_saldo(str(ctx.author.id))
    await ctx.send(f"💰 Saldo: {saldo}")

@bot.command()
@commands.has_permissions(administrator=True)
async def addsaldo(ctx, user: discord.Member, valor: int):
    await add_saldo(str(user.id), valor)
    await ctx.send("💸 Saldo adicionado!")

@bot.command()
@commands.has_permissions(administrator=True)
async def estoque(ctx, produto, *, conteudo):
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("INSERT INTO estoque VALUES (?, ?)", (produto, conteudo))
        await db.commit()
    await ctx.send("📦 Produto adicionado ao estoque!")

@bot.event
async def on_ready():
    await setup_db()
    print("Bot online!")

bot.run(os.getenv("TOKEN"))
