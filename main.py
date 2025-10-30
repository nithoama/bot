import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("❌ Token não encontrado! Crie um arquivo .env com DISCORD_TOKEN=seu_token")

bot = commands.Bot(command_prefix='!', intents=intents)

# Importar e ligar todos os comandos
try:
    import painel
    import sorteio  # 🆕 JÁ INCLUI O SISTEMA DE SALVAR SORTEIOS
    import ajuda
    import cargos

    # Configurar cada comando no bot
    painel.setup(bot)
    sorteio.setup(bot)  # 🆕 AGORA INCLUI SALVAMENTO AUTOMÁTICO
    ajuda.setup(bot)
    cargos.setup(bot)

    print("✅ Todos os comandos carregados com sucesso!")
    print(f"📋 Comandos carregados: {len(bot.commands)}")

    # Listar comandos carregados
    for command in bot.commands:
        print(f"   ✅ !{command.name}")

except ImportError as e:
    print(f"❌ Erro ao carregar comandos: {e}")


@bot.event
async def on_ready():
    print('🎉 BOT ONLINE!')
    print(f'🤖 Logado como: {bot.user.name}')
    print(f'📊 ID: {bot.user.id}')
    print(f'🏠 Servidores: {len(bot.guilds)}')
    print(f'⚡ Comandos: {len(bot.commands)}')

    # Status do bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="!ajuda | Sistema Completo"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado! Use `!ajuda` para ver os comandos disponíveis.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando!")
    else:
        await ctx.send(f"❌ Ocorreu um erro: {error}")


@bot.command()
async def ping(ctx):
    """🏓 Verifica a latência do bot"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 PONG!",
        description=f"**Latência:** {latency}ms",
        color=0x00FF00
    )
    await ctx.send(embed=embed)


if __name__ == "__main__":
    print("🚀 Iniciando bot Discord...")
    print("📁 Carregando módulos...")
    bot.run(TOKEN)