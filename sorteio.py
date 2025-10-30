import discord
import random
import asyncio
import json
import os
from datetime import datetime, timedelta

# CORES
CORES = {
    'vermelho': 0xFF0000, 'azul': 0x0000FF, 'verde': 0x00FF00, 'roxo': 0x9B59B6,
    'dourado': 0xFFD700, 'laranja': 0xFFA500, 'rosa': 0xFF69B4, 'ciano': 0x00FFFF,
    'marrom': 0x8B4513, 'azulescuro': 0x00008B, 'verdescuro': 0x006400,
    'vermelhoescuro': 0x8B0000, 'magenta': 0xFF00FF, 'verdeazul': 0x008080,
    'limao': 0x00FF00, 'marinho': 0x000080, 'coral': 0xFF7F50, 'preto': 0x000000
}

# Arquivo para configurações
CONFIG_FILE = "sorteio_config.json"
# Arquivo para salvar sorteios
SORTEIOS_FILE = "sorteios_salvos.json"


def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def salvar_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def salvar_sorteios(sorteios_ativos):
    """Salva os sorteios ativos no arquivo JSON"""
    try:
        sorteios_salvaveis = {}

        for nome, info in sorteios_ativos.items():
            sorteio_salvavel = {
                'nome': info['nome'],
                'premio': info['premio'],
                'imagem_url': info.get('imagem_url'),
                'cor': info['cor'],
                'criador': info['criador'],
                'criador_name': info['criador_name'],
                'mensagem_id': info['mensagem_id'],
                'channel_id': info['channel_id'],
                'fim_sorteio': info['fim_sorteio'].isoformat(),
                'participantes': [user.id for user in info.get('participantes', [])],
                'vencedor_atual': info['vencedor_atual'].id if info.get('vencedor_atual') else None,
                'finalizado': info.get('finalizado', False)
            }
            sorteios_salvaveis[nome] = sorteio_salvavel

        with open(SORTEIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorteios_salvaveis, f, indent=4, ensure_ascii=False)
        print(f"💾 Sorteios salvos: {len(sorteios_ativos)} sorteio(s)")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar sorteios: {e}")
        return False


def carregar_sorteios():
    """Carrega os sorteios do arquivo JSON"""
    if not os.path.exists(SORTEIOS_FILE):
        print("📁 Nenhum arquivo de sorteios encontrado")
        return {}

    try:
        with open(SORTEIOS_FILE, 'r', encoding='utf-8') as f:
            sorteios_salvos = json.load(f)

        sorteios_reconstruidos = {}
        sorteios_expirados = 0

        for nome, info in sorteios_salvos.items():
            try:
                # Verificar se o sorteio já expirou
                fim_sorteio = datetime.fromisoformat(info['fim_sorteio'])
                if datetime.now() >= fim_sorteio:
                    sorteios_expirados += 1
                    continue

                sorteio_reconstruido = {
                    'nome': info['nome'],
                    'premio': info['premio'],
                    'imagem_url': info.get('imagem_url'),
                    'cor': info['cor'],
                    'criador': info['criador'],
                    'criador_name': info['criador_name'],
                    'mensagem_id': info['mensagem_id'],
                    'channel_id': info['channel_id'],
                    'fim_sorteio': fim_sorteio,
                    'participantes_ids': info.get('participantes', []),
                    'vencedor_id': info.get('vencedor_atual'),
                    'participantes': [],
                    'vencedor_atual': None,
                    'finalizado': info.get('finalizado', False)
                }

                sorteios_reconstruidos[nome] = sorteio_reconstruido

            except Exception as e:
                print(f"❌ Erro ao reconstruir sorteio {nome}: {e}")
                continue

        print(f"🔄 Sorteios carregados: {len(sorteios_reconstruidos)} ativos, {sorteios_expirados} expirados")
        return sorteios_reconstruidos

    except Exception as e:
        print(f"❌ Erro ao carregar sorteios: {e}")
        return {}


def converter_duracao(tempo_str):
    try:
        tempo_str = tempo_str.lower().replace(' ', '')
        if not any(char in tempo_str for char in 'dhm'):
            raise ValueError("❌ **ERRO**: Formato inválido! Use d, h ou m")

        segundos = 0

        if 'd' in tempo_str:
            partes = tempo_str.split('d', 1)
            if not partes[0].isdigit():
                raise ValueError("❌ **ERRO**: Número de dias inválido!")
            dias = int(partes[0])
            if dias < 0 or dias > 365:
                raise ValueError("❌ **ERRO**: Dias devem ser entre 0 e 365!")
            segundos += dias * 24 * 60 * 60
            tempo_str = partes[1] if len(partes) > 1 else ""

        if 'h' in tempo_str:
            partes = tempo_str.split('h', 1)
            if not partes[0].isdigit():
                raise ValueError("❌ **ERRO**: Número de horas inválido!")
            horas = int(partes[0])
            if horas < 0 or horas > 23:
                raise ValueError("❌ **ERRO**: Horas devem ser entre 0 e 23!")
            segundos += horas * 60 * 60
            tempo_str = partes[1] if len(partes) > 1 else ""

        if 'm' in tempo_str:
            if not tempo_str.replace('m', '').isdigit():
                raise ValueError("❌ **ERRO**: Número de minutos inválido!")
            minutos = int(tempo_str.replace('m', ''))
            if minutos < 1 or minutos > 59:
                raise ValueError("❌ **ERRO**: Minutos devem ser entre 1 e 59!")
            segundos += minutos * 60

        if segundos < 60:
            raise ValueError("❌ **ERRO**: Duração mínima é 1 minuto!")

        if segundos > 31536000:
            raise ValueError("❌ **ERRO**: Duração máxima é 1 ano!")

        return segundos

    except Exception as e:
        raise ValueError(str(e))


def setup(bot):
    sorteios_ativos = carregar_sorteios()  # 🆕 CARREGAR SORTEIOS SALVOS
    task_ativa = False

    if not hasattr(bot, 'sorteio_config'):
        bot.sorteio_config = carregar_config()

    async def reconstruir_participantes():
        """Reconstrói os objetos de participantes após o bot estar pronto"""
        try:
            for nome, info in sorteios_ativos.items():
                participantes = []
                for user_id in info.get('participantes_ids', []):
                    try:
                        user = await bot.fetch_user(user_id)
                        participantes.append(user)
                    except:
                        continue

                # Reconstruir vencedor
                vencedor_atual = None
                if info.get('vencedor_id'):
                    try:
                        vencedor_atual = await bot.fetch_user(info['vencedor_id'])
                    except:
                        pass

                info['participantes'] = participantes
                info['vencedor_atual'] = vencedor_atual

            print(f"✅ Participantes reconstruídos para {len(sorteios_ativos)} sorteio(s)")
        except Exception as e:
            print(f"❌ Erro ao reconstruir participantes: {e}")

    async def atualizar_embed_sorteio(sorteio_info):
        try:
            channel = bot.get_channel(sorteio_info['channel_id'])
            if not channel:
                return

            msg_sorteio = await channel.fetch_message(sorteio_info['mensagem_id'])
            reacao = discord.utils.get(msg_sorteio.reactions, emoji="🎉")

            num_participantes = 0
            participantes = []

            if reacao:
                async for user in reacao.users():
                    if not user.bot:
                        participantes.append(user)
                        num_participantes += 1

            entradas_extras = 0
            server_id = str(channel.guild.id)

            if hasattr(bot, 'sorteio_config') and server_id in bot.sorteio_config:
                for participante in participantes:
                    for cargo in participante.roles:
                        cargo_id = str(cargo.id)
                        if cargo_id in bot.sorteio_config[server_id]:
                            entradas_extras += bot.sorteio_config[server_id][cargo_id]

            total_entradas = num_participantes + entradas_extras

            sorteio_info['participantes'] = participantes

            embed_atualizado = discord.Embed(
                title="🎉 **SORTEIO** 🎉",
                description=f"**Nome:** {sorteio_info['nome']}\n**Prêmio:** {sorteio_info['premio']}\n**Termina:** <t:{int(sorteio_info['fim_sorteio'].timestamp())}:R>",
                color=sorteio_info['cor'],
                timestamp=sorteio_info['fim_sorteio']
            )

            embed_atualizado.add_field(name="📋 **COMO PARTICIPAR:**", value="Clique no 🎉 para participar!",
                                       inline=False)
            embed_atualizado.add_field(name="👥 **PARTICIPANTES:**", value=f"**{num_participantes}** pessoas",
                                       inline=True)
            embed_atualizado.add_field(name="🎫 **ENTRADAS EXTRAS:**", value=f"**+{entradas_extras}** entradas",
                                       inline=True)
            embed_atualizado.add_field(name="🎲 **TOTAL:**", value=f"**{total_entradas}** entradas", inline=True)

            tempo_restante = sorteio_info['fim_sorteio'] - datetime.now()

            if tempo_restante.total_seconds() <= 0:
                tempo_formatado = "⏰ **Encerrando...**"
            else:
                dias = tempo_restante.days
                horas = tempo_restante.seconds // 3600
                minutos = (tempo_restante.seconds % 3600) // 60
                segundos = tempo_restante.seconds % 60

                tempo_formatado = ""
                if dias > 0:
                    tempo_formatado += f"{dias}d "
                if horas > 0:
                    tempo_formatado += f"{horas}h "
                if minutos > 0:
                    tempo_formatado += f"{minutos}m "
                if segundos > 0 and dias == 0 and horas == 0:
                    tempo_formatado += f"{segundos}s"

                tempo_formatado = tempo_formatado.strip()

            embed_atualizado.add_field(name="⏰ **TEMPO RESTANTE:**", value=tempo_formatado, inline=True)
            embed_atualizado.add_field(name="🔄 **RESORTEAR:**", value=f"Use `!resortear {sorteio_info['nome']}`",
                                       inline=False)

            server_id = str(channel.guild.id)
            if hasattr(bot, 'sorteio_config') and server_id in bot.sorteio_config and bot.sorteio_config[server_id]:
                cargos_info = []
                for cargo_id, entradas in bot.sorteio_config[server_id].items():
                    cargo = channel.guild.get_role(int(cargo_id))
                    if cargo:
                        cargos_info.append(f"• {cargo.mention} → **+{entradas}** entradas (total: {entradas + 1})")

                if cargos_info:
                    embed_atualizado.add_field(
                        name="🎯 **CARGOS COM VANTAGENS:**",
                        value="\n".join(cargos_info),
                        inline=False
                    )

            embed_atualizado.set_footer(text="Sorteio criado por: " + sorteio_info['criador_name'])

            if sorteio_info.get('imagem_url'):
                embed_atualizado.set_image(url=sorteio_info['imagem_url'])

            await msg_sorteio.edit(embed=embed_atualizado)

        except Exception as e:
            print(f"❌ Erro ao atualizar embed: {e}")

    async def task_atualizacao_sorteios():
        nonlocal task_ativa
        task_ativa = True
        print("🚀 Task de atualização de sorteios INICIADA")

        while True:
            try:
                if not sorteios_ativos:
                    await asyncio.sleep(5)
                    continue

                for nome_sorteio, sorteio_info in list(sorteios_ativos.items()):
                    if datetime.now() >= sorteio_info['fim_sorteio']:
                        await finalizar_sorteio_by_task(nome_sorteio)
                    else:
                        await atualizar_embed_sorteio(sorteio_info)

                await asyncio.sleep(5)

            except Exception as e:
                print(f"❌ Erro na task de atualização: {e}")
                await asyncio.sleep(5)

    async def finalizar_sorteio_by_task(nome_sorteio):
        try:
            sorteio_info = sorteios_ativos.get(nome_sorteio)
            if not sorteio_info:
                return

            # VERIFICAR SE JÁ FOI FINALIZADO
            if sorteio_info.get('finalizado'):
                return

            # MARCAR COMO FINALIZADO
            sorteio_info['finalizado'] = True

            channel = bot.get_channel(sorteio_info['channel_id'])
            if not channel:
                return

            msg_sorteio = await channel.fetch_message(sorteio_info['mensagem_id'])
            reacao_final = discord.utils.get(msg_sorteio.reactions, emoji="🎉")

            participantes_base = []
            if reacao_final:
                async for user in reacao_final.users():
                    if not user.bot:
                        participantes_base.append(user)

            if not participantes_base:
                embed_final = discord.Embed(
                    title="🎊 **SORTEIO ENCERRADO** 🎊",
                    description=f"**Nome:** {nome_sorteio}\n**Prêmio:** {sorteio_info['premio']}",
                    color=0xFF0000
                )
                embed_final.add_field(name="❌ **RESULTADO:**", value="Ninguém participou do sorteio!", inline=False)
                await msg_sorteio.edit(embed=embed_final)
                await channel.send(f"❌ Sorteio **{nome_sorteio}** encerrado sem participantes!")

                if nome_sorteio in sorteios_ativos:
                    del sorteios_ativos[nome_sorteio]
                    salvar_sorteios(sorteios_ativos)  # 🆕 SALVAR ALTERAÇÕES
                return

            participantes_finais = []
            server_id = str(channel.guild.id)

            for participante in participantes_base:
                entradas = 1
                if hasattr(bot, 'sorteio_config') and server_id in bot.sorteio_config:
                    for cargo in participante.roles:
                        cargo_id = str(cargo.id)
                        if cargo_id in bot.sorteio_config[server_id]:
                            entradas += bot.sorteio_config[server_id][cargo_id]

                for _ in range(entradas):
                    participantes_finais.append(participante)

            vencedor = random.choice(participantes_finais)
            entradas_extras = len(participantes_finais) - len(participantes_base)

            embed_final = discord.Embed(
                title="🎊 **SORTEIO ENCERRADO** 🎊",
                description=f"**Nome:** {nome_sorteio}\n**Prêmio:** {sorteio_info['premio']}",
                color=sorteio_info['cor']
            )

            embed_final.add_field(name="🏆 **VENCEDOR:**", value=f"{vencedor.mention}", inline=False)
            embed_final.add_field(name="👥 **PARTICIPANTES ÚNICOS:**",
                                  value=f"**{len(participantes_base)}** pessoas", inline=True)
            embed_final.add_field(name="🎫 **ENTRADAS EXTRAS:**",
                                  value=f"**+{entradas_extras}** entradas", inline=True)
            embed_final.add_field(name="🎲 **TOTAL DE ENTRADAS:**",
                                  value=f"**{len(participantes_finais)}** no sorteio", inline=True)
            embed_final.add_field(name="🔄 **RESORTEAR:**", value=f"Use `!resortear {nome_sorteio}`", inline=False)
            embed_final.set_footer(text="Parabéns ao vencedor! 🎉")

            if sorteio_info.get('imagem_url'):
                embed_final.set_thumbnail(url=sorteio_info['imagem_url'])

            await msg_sorteio.edit(embed=embed_final)

            # ✅ CORREÇÃO: APENAS UMA MENSAGEM SIMPLES (SEM SPAM)
            await channel.send(f"🎉 **PARABÉNS!** {vencedor.mention} ganhou o sorteio **{nome_sorteio}**! 🏆")

            sorteios_ativos[nome_sorteio]['participantes'] = participantes_base
            sorteios_ativos[nome_sorteio]['vencedor_atual'] = vencedor

            salvar_sorteios(sorteios_ativos)  # 🆕 SALVAR APÓS FINALIZAR

        except Exception as e:
            print(f"❌ Erro ao finalizar sorteio: {e}")
            if nome_sorteio in sorteios_ativos:
                del sorteios_ativos[nome_sorteio]
                salvar_sorteios(sorteios_ativos)  # 🆕 SALVAR ALTERAÇÕES

    @bot.command()
    async def sorteio(ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            await ctx.send("🏷️ **QUAL O NOME DO SORTEIO?** (será usado para resortear)")
            nome_msg = await bot.wait_for('message', check=check, timeout=60)
            nome_sorteio = nome_msg.content.lower().replace(' ', '')

            if not nome_sorteio.strip():
                await ctx.send("❌ **ERRO**: Nome não pode estar vazio! Tente novamente.")
                return

            if nome_sorteio in sorteios_ativos:
                await ctx.send("❌ **ERRO**: Já existe um sorteio com este nome! Escolha outro nome.")
                return

            await ctx.send("🎁 **QUAL O PRÊMIO DO SORTEIO?**")
            premio_msg = await bot.wait_for('message', check=check, timeout=60)
            premio = premio_msg.content

            if not premio.strip():
                await ctx.send("❌ **ERRO**: Prêmio não pode estar vazio! Tente novamente.")
                return

            await ctx.send("⏰ **DURAÇÃO DO SORTEIO (ex: 30m, 2h, 1d, 2d 12h):**")
            duracao_msg = await bot.wait_for('message', check=check, timeout=60)

            try:
                duracao_segundos = converter_duracao(duracao_msg.content)
            except ValueError as e:
                await ctx.send(str(e))
                return

            await ctx.send("🖼️ **COLE A URL DA IMAGEM (ou digite 'pular'):**")
            imagem_msg = await bot.wait_for('message', check=check, timeout=60)
            imagem_url = imagem_msg.content if imagem_msg.content.lower() != 'pular' else None

            await ctx.send("🎨 **COR DO SORTEIO:**\n" + ", ".join(CORES.keys()))
            cor_msg = await bot.wait_for('message', check=check, timeout=60)

            if cor_msg.content.lower() not in CORES:
                await ctx.send("❌ **ERRO**: Cor inválida! Use uma das cores listadas. Tente novamente.")
                return

            cor_int = CORES[cor_msg.content.lower()]

            fim_sorteio = datetime.now() + timedelta(seconds=duracao_segundos)

            embed = discord.Embed(
                title="🎉 **SORTEIO** 🎉",
                description=f"**Nome:** {nome_sorteio}\n**Prêmio:** {premio}\n**Termina:** <t:{int(fim_sorteio.timestamp())}:R>",
                color=cor_int,
                timestamp=fim_sorteio
            )

            embed.add_field(name="📋 **COMO PARTICIPAR:**", value="Clique no 🎉 para participar!", inline=False)
            embed.add_field(name="👥 **PARTICIPANTES:**", value="**0** pessoas", inline=True)
            embed.add_field(name="🎫 **ENTRADAS EXTRAS:**", value="**+0** entradas", inline=True)
            embed.add_field(name="🎲 **TOTAL:**", value="**0** entradas", inline=True)

            dias = duracao_segundos // (24 * 60 * 60)
            horas = (duracao_segundos % (24 * 60 * 60)) // (60 * 60)
            minutos = (duracao_segundos % (60 * 60)) // 60

            tempo_formatado = ""
            if dias > 0:
                tempo_formatado += f"{dias}d "
            if horas > 0:
                tempo_formatado += f"{horas}h "
            if minutos > 0:
                tempo_formatado += f"{minutos}m"

            embed.add_field(name="⏰ **DURAÇÃO:**", value=tempo_formatado.strip(), inline=True)
            embed.add_field(name="🔄 **RESORTEAR:**", value=f"Use `!resortear {nome_sorteio}`", inline=False)

            server_id = str(ctx.guild.id)
            if hasattr(bot, 'sorteio_config') and server_id in bot.sorteio_config and bot.sorteio_config[server_id]:
                cargos_info = []
                for cargo_id, entradas in bot.sorteio_config[server_id].items():
                    cargo = ctx.guild.get_role(int(cargo_id))
                    if cargo:
                        cargos_info.append(f"• {cargo.mention} → **+{entradas}** entradas (total: {entradas + 1})")

                if cargos_info:
                    embed.add_field(
                        name="🎯 **CARGOS COM VANTAGENS:**",
                        value="\n".join(cargos_info),
                        inline=False
                    )

            embed.set_footer(text="Sorteio criado por: " + ctx.author.display_name)

            if imagem_url:
                embed.set_image(url=imagem_url)

            msg_sorteio = await ctx.send(embed=embed)
            await msg_sorteio.add_reaction("🎉")

            sorteios_ativos[nome_sorteio] = {
                'nome': nome_sorteio,
                'premio': premio,
                'imagem_url': imagem_url,
                'cor': cor_int,
                'criador': ctx.author.id,
                'criador_name': ctx.author.display_name,
                'mensagem_id': msg_sorteio.id,
                'channel_id': ctx.channel.id,
                'fim_sorteio': fim_sorteio,
                'participantes': [],
                'vencedor_atual': None,
                'finalizado': False
            }

            salvar_sorteios(sorteios_ativos)  # 🆕 SALVAR APÓS CRIAR
            print(f"🎉 Novo sorteio criado: '{nome_sorteio}' por {ctx.author.display_name}")

            if not task_ativa:
                bot.loop.create_task(task_atualizacao_sorteios())

        except asyncio.TimeoutError:
            await ctx.send("⏰ **ERRO**: Tempo esgotado! Tente novamente.")
        except Exception as e:
            await ctx.send(f"❌ **ERRO**: {str(e)} Tente novamente.")

    @bot.command()
    async def resortear(ctx, *, nome_sorteio: str = None):
        if nome_sorteio is None:
            embed = discord.Embed(
                title="🔄 **AJUDA - RESORTEAR**",
                description="**Como usar:** `!resortear nome_do_sorteio`",
                color=0xFFD700
            )

            sorteios_disponiveis = []
            for nome, info in sorteios_ativos.items():
                if info.get('participantes') and len(info['participantes']) >= 2:
                    sorteios_disponiveis.append(f"• `{nome}` - {info['premio']}")

            if sorteios_disponiveis:
                embed.add_field(
                    name="🎯 **SORTEIOS DISPONÍVEIS:**",
                    value="\n".join(sorteios_disponiveis),
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ **NENHUM SORTEIO:**",
                    value="Não há sorteios disponíveis para resorteio",
                    inline=False
                )

            await ctx.send(embed=embed)
            return

        nome_sorteio = nome_sorteio.lower().replace(' ', '')

        sorteio_info = sorteios_ativos.get(nome_sorteio)

        if not sorteio_info:
            await ctx.send("❌ **ERRO**: Sorteio não encontrado! Use `!resortear` para ver a lista.")
            return

        if ctx.author.id != sorteio_info['criador']:
            await ctx.send("❌ **ERRO**: Apenas o criador do sorteio pode resortear!")
            return

        participantes = sorteio_info.get('participantes', [])

        if not participantes:
            await ctx.send("❌ **ERRO**: Não há participantes para resortear!")
            return

        if len(participantes) < 2:
            await ctx.send("❌ **ERRO**: É necessário pelo menos 2 participantes para resortear!")
            return

        participantes_finais = []
        server_id = str(ctx.guild.id)

        for participante in participantes:
            entradas = 1
            if hasattr(bot, 'sorteio_config') and server_id in bot.sorteio_config:
                for cargo in participante.roles:
                    cargo_id = str(cargo.id)
                    if cargo_id in bot.sorteio_config[server_id]:
                        entradas += bot.sorteio_config[server_id][cargo_id]

            for _ in range(entradas):
                participantes_finais.append(participante)

        vencedor_anterior = sorteio_info.get('vencedor_atual')
        participantes_remanescentes = [p for p in participantes_finais if p != vencedor_anterior]

        if not participantes_remanescentes:
            await ctx.send("❌ **ERRO**: Não há outros participantes para resortear!")
            return

        novo_vencedor = random.choice(participantes_remanescentes)

        embed_resorteio = discord.Embed(
            title="🔄 **RESORTEIO REALIZADO** 🔄",
            description=f"**Nome:** {nome_sorteio}\n**Prêmio:** {sorteio_info['premio']}",
            color=sorteio_info['cor']
        )

        embed_resorteio.add_field(name="🏆 **NOVO VENCEDOR:**", value=f"{novo_vencedor.mention}", inline=False)
        embed_resorteio.add_field(name="👤 **VENCEDOR ANTERIOR:**",
                                  value=f"{vencedor_anterior.mention if vencedor_anterior else 'Nenhum'}", inline=True)
        embed_resorteio.add_field(name="👥 **PARTICIPANTES RESTANTES:**",
                                  value=f"{len(set(participantes_remanescentes))} pessoas", inline=True)
        embed_resorteio.add_field(name="🎲 **ENTRADAS RESTANTES:**",
                                  value=f"{len(participantes_remanescentes)} entradas", inline=True)
        embed_resorteio.add_field(name="🔄 **PRÓXIMO RESORTEIO:**",
                                  value=f"Use `!resortear {nome_sorteio}` novamente", inline=False)
        embed_resorteio.set_footer(text="Resorteio realizado por: " + ctx.author.display_name)

        if sorteio_info.get('imagem_url'):
            embed_resorteio.set_thumbnail(url=sorteio_info['imagem_url'])

        await ctx.send(f"🔄 {novo_vencedor.mention}", embed=embed_resorteio)

        sorteios_ativos[nome_sorteio]['vencedor_atual'] = novo_vencedor
        salvar_sorteios(sorteios_ativos)  # 🆕 SALVAR APÓS RESORTEAR

    @bot.command()
    async def meussorteios(ctx):
        embed = discord.Embed(
            title="🎯 **MEUS SORTEIOS**",
            color=0x9B59B6
        )

        meus_sorteios = []
        for nome, info in sorteios_ativos.items():
            if info['criador'] == ctx.author.id:
                participantes = len(info.get('participantes', []))
                vencedor = info.get('vencedor_atual')
                status = "✅ Finalizado" if vencedor else "⏳ Ativo"

                meus_sorteios.append(f"• **{nome}** - {info['premio']} ({status})")
                meus_sorteios.append(f"  👥 {participantes} participantes")
                if vencedor:
                    meus_sorteios.append(f"  🏆 Vencedor: {vencedor.display_name}")
                meus_sorteios.append("")

        if meus_sorteios:
            embed.description = "\n".join(meus_sorteios)
        else:
            embed.description = "❌ Você não criou nenhum sorteio ainda!"

        await ctx.send(embed=embed)

    @bot.event
    async def on_ready():
        print(f'🎉 Sistema de sorteios carregado!')
        # 🆕 RECONSTRUIR PARTICIPANTES APÓS O BOT ESTAR PRONTO
        await reconstruir_participantes()
        if not task_ativa and sorteios_ativos:
            bot.loop.create_task(task_atualizacao_sorteios())