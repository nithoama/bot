import discord

def setup(bot):
    @bot.command()
    async def ajuda(ctx):
        embed = discord.Embed(
            title="🛠️ **COMANDOS DISPONÍVEIS**",
            description="Todos os comandos do bot:",
            color=0x00FF00
        )
        embed.add_field(name="🎨 !painel", value="Criar painel personalizado", inline=False)
        embed.add_field(name="🎉 !sorteio", value="Criar sorteio", inline=False)
        embed.add_field(name="🔄 !resortear", value="Resortear sorteio", inline=False)
        embed.add_field(name="📋 !meussorteios", value="Ver seus sorteios", inline=False)
        embed.add_field(name="🎯 !configcargo", value="Configurar cargos", inline=False)
        embed.add_field(name="ℹ️ !ajuda", value="Mostra esta mensagem", inline=False)
        await ctx.send(embed=embed)

    @bot.command()
    async def info(ctx):
        await ctx.send("🤖 Informações do bot!")

    @bot.command()
    async def cores(ctx):
        await ctx.send("🎨 Lista de cores disponíveis!")