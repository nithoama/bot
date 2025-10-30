import json
import os
from datetime import datetime

# Arquivo para salvar sorteios
SORTEIOS_FILE = "sorteios_salvos.json"


def converter_para_salvavel(sorteios_ativos):
    """Converte sorteios ativos para formato salvável em JSON"""
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
            'fim_sorteio': info['fim_sorteio'].isoformat(),  # Converter datetime para string
            'participantes': [user.id for user in info.get('participantes', [])],  # Salvar apenas IDs
            'vencedor_atual': info['vencedor_atual'].id if info.get('vencedor_atual') else None,
            'finalizado': info.get('finalizado', False)
        }
        sorteios_salvaveis[nome] = sorteio_salvavel

    return sorteios_salvaveis


def salvar_sorteios(sorteios_ativos):
    """Salva os sorteios ativos no arquivo JSON"""
    try:
        sorteios_salvaveis = converter_para_salvavel(sorteios_ativos)
        with open(SORTEIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorteios_salvaveis, f, indent=4, ensure_ascii=False)
        print(f"💾 Sorteios salvos: {len(sorteios_ativos)} sorteio(s)")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar sorteios: {e}")
        return False


def carregar_sorteios(bot):
    """Carrega os sorteios do arquivo JSON e reconstrói os objetos"""
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

                # Reconstruir participantes (apenas IDs por enquanto)
                participantes_ids = info.get('participantes', [])

                # Reconstruir vencedor (apenas ID por enquanto)
                vencedor_id = info.get('vencedor_atual')

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
                    'participantes_ids': participantes_ids,  # Guardar IDs para reconstruir depois
                    'vencedor_id': vencedor_id,  # Guardar ID para reconstruir depois
                    'participantes': [],  # Será preenchido quando o bot estiver pronto
                    'vencedor_atual': None,  # Será preenchido quando o bot estiver pronto
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


async def reconstruir_objetos_discord(sorteios_ativos, bot):
    """Reconstrói objetos Discord (usuários, canais) após o bot estar pronto"""
    try:
        for nome, info in sorteios_ativos.items():
            # Reconstruir canal
            channel = bot.get_channel(info['channel_id'])
            if not channel:
                print(f"❌ Canal não encontrado para sorteio {nome}")
                continue

            # Reconstruir participantes
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

            # Atualizar informações
            info['participantes'] = participantes
            info['vencedor_atual'] = vencedor_atual

        print(f"✅ Objetos Discord reconstruídos para {len(sorteios_ativos)} sorteio(s)")
        return True

    except Exception as e:
        print(f"❌ Erro ao reconstruir objetos Discord: {e}")
        return False


def limpar_sorteios_expirados():
    """Remove sorteios expirados do arquivo de salvamento"""
    if not os.path.exists(SORTEIOS_FILE):
        return

    try:
        with open(SORTEIOS_FILE, 'r', encoding='utf-8') as f:
            sorteios_salvos = json.load(f)

        sorteios_nao_expirados = {}
        sorteios_removidos = 0

        for nome, info in sorteios_salvos.items():
            try:
                fim_sorteio = datetime.fromisoformat(info['fim_sorteio'])
                if datetime.now() < fim_sorteio:
                    sorteios_nao_expirados[nome] = info
                else:
                    sorteios_removidos += 1
            except:
                continue

        with open(SORTEIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorteios_nao_expirados, f, indent=4, ensure_ascii=False)

        print(f"🧹 Sorteios expirados removidos: {sorteios_removidos}")

    except Exception as e:
        print(f"❌ Erro ao limpar sorteios expirados: {e}")


def backup_sorteios():
    """Cria um backup dos sorteios salvos"""
    if not os.path.exists(SORTEIOS_FILE):
        return

    try:
        import shutil
        from datetime import datetime

        backup_file = f"sorteios_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(SORTEIOS_FILE, backup_file)
        print(f"📦 Backup criado: {backup_file}")

    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")