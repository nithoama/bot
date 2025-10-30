import discord

def setup(bot):
    @bot.command()
    async def configcargo(ctx, cargo: discord.Role = None, entradas: int = 0):
        if cargo and entradas > 0:
            await ctx.send(f"✅ Cargo {cargo.mention} configurado com +{entradas} entradas!")
        else:
            await ctx.send("❌ Use: `!configcargo @cargo numero`")

    @bot.command()
    async def vercargos(ctx):
        await ctx.send("🎯 Cargos configurados aparecerão aqui!")

    @bot.command()
    async def minhasvantagens(ctx):
        await ctx.send("🎫 Suas vantagens aparecerão aqui!")