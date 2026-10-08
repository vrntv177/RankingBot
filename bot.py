import discord
from discord.ext import commands, tasks
from datetime import datetime
import json
import os

from config import TOKEN


# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_DADOS = "ranking.json"

TOP_MENSAGENS = 5
TOP_CALL = 5

# COLOQUE AQUI O ID DO SEU CANAL DE RANKING
CANAL_RANKING_ID = 1557738264641802280

# Atualização automática
INTERVALO_ATUALIZACAO = 3


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True


# =========================================================
# BOT
# =========================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# DADOS
# =========================================================

dados = {}

# Guarda quando cada usuário entrou na call
entradas_call = {}

# Guarda a mensagem do ranking
mensagens_ranking = {}


# =========================================================
# CARREGAR DADOS
# =========================================================

def carregar_dados():

    global dados

    if not os.path.exists(ARQUIVO_DADOS):

        dados = {}

        return

    try:

        with open(
            ARQUIVO_DADOS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

    except Exception as erro:

        print(
            f"⚠️ Erro ao carregar dados: {erro}"
        )

        dados = {}


# =========================================================
# SALVAR DADOS
# =========================================================

def salvar_dados():

    try:

        with open(
            ARQUIVO_DADOS,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

    except Exception as erro:

        print(
            f"⚠️ Erro ao salvar dados: {erro}"
        )


# =========================================================
# GARANTIR SERVIDOR
# =========================================================

def garantir_guild(guild_id):

    guild_id = str(guild_id)

    if guild_id not in dados:

        dados[guild_id] = {}


# =========================================================
# GARANTIR USUÁRIO
# =========================================================

def garantir_usuario(guild_id, user_id):

    guild_id = str(guild_id)
    user_id = str(user_id)

    garantir_guild(guild_id)

    if user_id not in dados[guild_id]:

        dados[guild_id][user_id] = {

            "mensagens": 0,

            "call_segundos": 0

        }


# =========================================================
# FORMATAR TEMPO
# =========================================================

def formatar_tempo(segundos):

    segundos = int(segundos)

    horas = segundos // 3600

    minutos = (segundos % 3600) // 60

    segundos_restantes = segundos % 60

    return (
        f"{horas:02d}h "
        f"{minutos:02d}m "
        f"{segundos_restantes:02d}s"
    )


# =========================================================
# PEGAR TEMPO DE CALL
# =========================================================

def pegar_tempo_call(guild_id, user_id):

    garantir_usuario(
        guild_id,
        user_id
    )

    tempo = dados[
        str(guild_id)
    ][
        str(user_id)
    ].get(
        "call_segundos",
        0
    )

    chave = (
        guild_id,
        user_id
    )

    # Se está em call, soma o tempo atual
    if chave in entradas_call:

        entrada = entradas_call[chave]

        tempo += (
            datetime.now() - entrada
        ).total_seconds()

    return int(tempo)


# =========================================================
# TOP MENSAGENS
# =========================================================

def top_mensagens(guild):

    garantir_guild(guild.id)

    usuarios = []

    for user_id, info in dados[
        str(guild.id)
    ].items():

        mensagens = info.get(
            "mensagens",
            0
        )

        member = guild.get_member(
            int(user_id)
        )

        if member:

            usuarios.append(
                (
                    member,
                    mensagens
                )
            )

    usuarios.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return usuarios[:TOP_MENSAGENS]


# =========================================================
# TOP CALL
# =========================================================

def top_call(guild):

    garantir_guild(guild.id)

    usuarios = []

    for user_id, info in dados[
        str(guild.id)
    ].items():

        member = guild.get_member(
            int(user_id)
        )

        if member:

            tempo = pegar_tempo_call(
                guild.id,
                member.id
            )

            usuarios.append(
                (
                    member,
                    tempo
                )
            )

    usuarios.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return usuarios[:TOP_CALL]


# =========================================================
# POSIÇÃO EM MENSAGENS
# =========================================================

def posicao_mensagens(guild, user_id):

    garantir_guild(guild.id)

    todos = []

    for uid, info in dados[
        str(guild.id)
    ].items():

        member = guild.get_member(
            int(uid)
        )

        if member:

            todos.append(
                (
                    member.id,
                    info.get(
                        "mensagens",
                        0
                    )
                )
            )

    todos.sort(
        key=lambda x: x[1],
        reverse=True
    )

    for posicao, (uid, _) in enumerate(
        todos,
        start=1
    ):

        if uid == user_id:

            return posicao

    return 0


# =========================================================
# POSIÇÃO EM CALL
# =========================================================

def posicao_call(guild, user_id):

    garantir_guild(guild.id)

    todos = []

    for uid in dados[
        str(guild.id)
    ]:

        member = guild.get_member(
            int(uid)
        )

        if member:

            tempo = pegar_tempo_call(
                guild.id,
                member.id
            )

            todos.append(
                (
                    member.id,
                    tempo
                )
            )

    todos.sort(
        key=lambda x: x[1],
        reverse=True
    )

    for posicao, (uid, _) in enumerate(
        todos,
        start=1
    ):

        if uid == user_id:

            return posicao

    return 0


# =========================================================
# BOTÃO
# =========================================================

class RankingView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Minhas Estatísticas",
        emoji="📊",
        style=discord.ButtonStyle.primary
    )
    async def minhas_estatisticas(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        user = interaction.user

        if guild is None:

            await interaction.response.send_message(
                "❌ Esse botão só funciona dentro de um servidor.",
                ephemeral=True
            )

            return

        garantir_usuario(
            guild.id,
            user.id
        )

        # Mensagens
        mensagens = dados[
            str(guild.id)
        ][
            str(user.id)
        ].get(
            "mensagens",
            0
        )

        # Tempo de call
        tempo_call = pegar_tempo_call(
            guild.id,
            user.id
        )

        # Verifica se está em call
        chave = (
            guild.id,
            user.id
        )

        if chave in entradas_call:

            status_call = (
                "🟢 Você está em call agora!"
            )

        else:

            status_call = (
                "⚪ Você não está em call."
            )

        # Posições
        pos_msg = posicao_mensagens(
            guild,
            user.id
        )

        pos_call = posicao_call(
            guild,
            user.id
        )

        # Embed
        embed = discord.Embed(
            title="📊 Suas Estatísticas",
            color=discord.Color.blurple()
        )

        embed.description = (
            f"👤 **Usuário:** {user.mention}\n\n"

            f"{status_call}\n\n"

            f"🎙️ **Tempo em Call**\n"
            f"**{formatar_tempo(tempo_call)}**\n\n"

            f"💬 **Mensagens Enviadas**\n"
            f"**{mensagens:,}**".replace(",", ".")
            + "\n\n"

            f"🏆 **Posição em Mensagens:** "
            f"**#{pos_msg}**\n"

            f"🎙️ **Posição em Call:** "
            f"**#{pos_call}**"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =========================================================
# GERAR RANKING
# =========================================================

def gerar_ranking(guild):

    linhas = []

    linhas.append(
        "🏆 **Ranking do Servidor**"
    )

    linhas.append(
        "━━━━━━━━━━━━━━━━━━━━"
    )

    linhas.append("")

    # =====================================================
    # CALL
    # =====================================================

    linhas.append(
        "🎙️ **Top 5 — Tempo em Call**"
    )

    linhas.append("")

    ranking_call = top_call(guild)

    if not ranking_call:

        linhas.append(
            "`Nenhum dado de call ainda.`"
        )

    else:

        for posicao, (member, tempo) in enumerate(
            ranking_call,
            start=1
        ):

            linhas.append(
                f"`{posicao:02d}` — "
                f"{member.mention} • "
                f"**{formatar_tempo(tempo)}**"
            )

    linhas.append("")

    # =====================================================
    # MENSAGENS
    # =====================================================

    linhas.append(
        "💬 **Top 5 — Mensagens**"
    )

    linhas.append("")

    ranking_msg = top_mensagens(guild)

    if not ranking_msg:

        linhas.append(
            "`Nenhum dado de mensagens ainda.`"
        )

    else:

        for posicao, (member, mensagens) in enumerate(
            ranking_msg,
            start=1
        ):

            numero = f"{mensagens:,}".replace(
                ",",
                "."
            )

            linhas.append(
                f"`{posicao:02d}` — "
                f"{member.mention} • "
                f"**{numero} msgs**"
            )

    linhas.append("")

    linhas.append(
        "━━━━━━━━━━━━━━━━━━━━"
    )

    linhas.append(
        "🔄 Atualização automática a cada 3 segundos"
    )

    return "\n".join(linhas)


# =========================================================
# ATUALIZAR RANKING
# =========================================================

async def atualizar_ranking(guild):

    if CANAL_RANKING_ID is None:

        return

    canal = guild.get_channel(
        CANAL_RANKING_ID
    )

    if canal is None:

        return

    try:

        mensagem = mensagens_ranking.get(
            guild.id
        )

        # Procura a mensagem existente
        if mensagem is None:

            async for msg in canal.history(
                limit=20
            ):

                if (
                    msg.author.id == bot.user.id
                    and msg.embeds
                ):

                    mensagem = msg

                    mensagens_ranking[
                        guild.id
                    ] = msg

                    break

        # =================================================
        # CRIA RANKING
        # =================================================

        if mensagem is None:

            embed = discord.Embed(
                description=gerar_ranking(guild),
                color=discord.Color.blurple()
            )

            mensagem = await canal.send(
                embed=embed,
                view=RankingView()
            )

            mensagens_ranking[
                guild.id
            ] = mensagem

            return

        # =================================================
        # ATUALIZA RANKING
        # =================================================

        embed = discord.Embed(
            description=gerar_ranking(guild),
            color=discord.Color.blurple()
        )

        await mensagem.edit(
            embed=embed,
            view=RankingView()
        )

    except discord.NotFound:

        mensagens_ranking.pop(
            guild.id,
            None
        )

    except discord.HTTPException as erro:

        print(
            f"⚠️ Discord recusou a atualização: {erro}"
        )

    except Exception as erro:

        print(
            f"⚠️ Erro no ranking: {erro}"
        )


# =========================================================
# ATUALIZAÇÃO AUTOMÁTICA
# =========================================================

@tasks.loop(seconds=INTERVALO_ATUALIZACAO)
async def atualizar_todos():

    try:

        for guild in bot.guilds:

            await atualizar_ranking(
                guild
            )

    except Exception as erro:

        print(
            f"⚠️ Erro no sistema de atualização: {erro}"
        )


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():

    carregar_dados()

    print(
        f"✅ Bot online como {bot.user}"
    )

    try:

        sincronizados = await bot.tree.sync()

        print(
            f"✅ {len(sincronizados)} comandos sincronizados."
        )

    except Exception as erro:

        print(
            f"❌ Erro ao sincronizar comandos: {erro}"
        )

    if not atualizar_todos.is_running():

        atualizar_todos.start()


# =========================================================
# CONTAR MENSAGENS
# =========================================================

@bot.event
async def on_message(message):

    if message.author.bot:

        return

    if message.guild is None:

        return

    garantir_usuario(
        message.guild.id,
        message.author.id
    )

    dados[
        str(message.guild.id)
    ][
        str(message.author.id)
    ][
        "mensagens"
    ] += 1

    salvar_dados()

    await bot.process_commands(
        message
    )


# =========================================================
# ENTRADA / SAÍDA DE CALL
# =========================================================

@bot.event
async def on_voice_state_update(
    member,
    antes,
    depois
):

    if member.bot:

        return

    guild_id = member.guild.id

    user_id = member.id

    garantir_usuario(
        guild_id,
        user_id
    )

    chave = (
        guild_id,
        user_id
    )

    # =====================================================
    # ENTROU NA CALL
    # =====================================================

    if (
        antes.channel is None
        and depois.channel is not None
    ):

        entradas_call[chave] = datetime.now()

        print(
            f"🎙️ {member} entrou em call."
        )

    # =====================================================
    # SAIU DA CALL
    # =====================================================

    elif (
        antes.channel is not None
        and depois.channel is None
    ):

        if chave in entradas_call:

            entrada = entradas_call.pop(
                chave
            )

            segundos = (
                datetime.now() - entrada
            ).total_seconds()

            dados[
                str(guild_id)
            ][
                str(user_id)
            ][
                "call_segundos"
            ] += int(segundos)

            salvar_dados()

            print(
                f"🎙️ {member} ficou "
                f"{int(segundos)} segundos em call."
            )


# =========================================================
# /RANKING
# =========================================================

@bot.tree.command(
    name="ranking",
    description="Mostra o ranking do servidor."
)
async def ranking(interaction):

    embed = discord.Embed(
        description=gerar_ranking(
            interaction.guild
        ),
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(
        embed=embed,
        view=RankingView()
    )


# =========================================================
# /MEURANKING
# =========================================================

@bot.tree.command(
    name="meuranking",
    description="Mostra suas estatísticas."
)
async def meuranking(interaction):

    guild = interaction.guild

    user = interaction.user

    garantir_usuario(
        guild.id,
        user.id
    )

    mensagens = dados[
        str(guild.id)
    ][
        str(user.id)
    ].get(
        "mensagens",
        0
    )

    tempo = pegar_tempo_call(
        guild.id,
        user.id
    )

    embed = discord.Embed(
        title=(
            f"📊 Estatísticas de "
            f"{user.display_name}"
        ),
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="💬 Mensagens",
        value=(
            f"**{mensagens:,}**"
        ).replace(",", "."),
        inline=True
    )

    embed.add_field(
        name="🎙️ Tempo em Call",
        value=(
            f"**{formatar_tempo(tempo)}**"
        ),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /RESET-RANKING
# =========================================================

@bot.tree.command(
    name="reset-ranking",
    description="Zera o ranking do servidor."
)
async def reset_ranking(interaction):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ Você precisa ser administrador.",
            ephemeral=True
        )

        return

    dados[
        str(interaction.guild.id)
    ] = {}

    salvar_dados()

    await interaction.response.send_message(
        "✅ Ranking zerado com sucesso."
    )


# =========================================================
# INICIAR
# =========================================================

bot.run(TOKEN)