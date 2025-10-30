import discord

CORES = {
    'vermelho': 0xFF0000, 'azul': 0x0000FF, 'verde': 0x00FF00, 'roxo': 0x9B59B6,
    'dourado': 0xFFD700, 'laranja': 0xFFA500, 'rosa': 0xFF69B4, 'ciano': 0x00FFFF,
    'marrom': 0x8B4513, 'azulescuro': 0x00008B, 'verdescuro': 0x006400,
    'vermelhoescuro': 0x8B0000, 'magenta': 0xFF00FF, 'verdeazul': 0x008080,
    'limao': 0x00FF00, 'marinho': 0x000080, 'coral': 0xFF7F50, 'preto': 0x000000
}

def setup(bot):
    @bot.command()
    async def painel(ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            await ctx.send("🏷️ **DIGITE O TÍTULO:**")
            titulo_msg = await bot.wait_for('message', check=check, timeout=60)

            await ctx.send("📋 **DIGITE A DESCRIÇÃO:**")
            descricao_msg = await bot.wait_for('message', check=check, timeout=60)

            await ctx.send("📝 **COLE TODO O TEXTO DO PAINEL:**")
            texto_msg = await bot.wait_for('message', check=check, timeout=120)

            await ctx.send("🎨 **DIGITE A COR:**\n" + ", ".join(CORES.keys()))
            cor_msg = await bot.wait_for('message', check=check, timeout=60)

            await ctx.send("🖼️ **COLE A URL DA IMAGEM:**")
            imagem_msg = await bot.wait_for('message', check=check, timeout=60)

            cor_int = CORES.get(cor_msg.content.lower(), 0x00FF00)

            embed = discord.Embed(
                title=f" {titulo_msg.content.upper()} ",
                description=f"**{descricao_msg.content}**\n\n{texto_msg.content}",
                color=cor_int
            )
            embed.set_image(url=imagem_msg.content)
            await ctx.send(embed=embed)

        except:
            await ctx.send("⏰ Tempo esgotado!")