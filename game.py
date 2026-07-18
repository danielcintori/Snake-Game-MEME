import os
import random
import sys

import pygame


# ==================================================
# INICIALIZAÇÃO
# ==================================================

pygame.init()
pygame.mixer.init()

# ==================================================
# CONFIGURAÇÕES DA TELA
# ==================================================

LARGURA = 800
ALTURA = 600
FPS = 60

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Jogo da Cobrinha")

relogio = pygame.time.Clock()

# ==================================================
# CORES
# ==================================================

PRETO = (15, 15, 15)
CINZA_ESCURO = (35, 35, 35)
CINZA = (90, 90, 90)

VERDE_CABECA = (0, 220, 0)
VERDE_CORPO = (0, 150, 0)

VERMELHO = (255, 60, 60)
AMARELO = (255, 220, 0)
AZUL = (40, 130, 255)

BRANCO = (255, 255, 255)

# ==================================================
# GRADE
# ==================================================

TAMANHO_BLOCO = 20

CIMA = (0, -TAMANHO_BLOCO)
BAIXO = (0, TAMANHO_BLOCO)
ESQUERDA = (-TAMANHO_BLOCO, 0)
DIREITA = (TAMANHO_BLOCO, 0)

# ==================================================
# INTERVALOS DE MOVIMENTO
# ==================================================
#
# Quanto menor o intervalo, mais rápida a cobra.
# Os valores são dados em milissegundos.
# ==================================================

INTERVALO_NORMAL = 100
INTERVALO_LENTO = 180
INTERVALO_RAPIDO = 55

# Duração do efeito depois que o alimento é consumido
DURACAO_EFEITO_AMARELO = 6000
DURACAO_EFEITO_AZUL = 5000

# Tempo que os alimentos especiais ficam disponíveis
TEMPO_COMIDA_AMARELA = 8000
TEMPO_COMIDA_AZUL = 4500

# Mensagens temporárias
DURACAO_MENSAGEM = 1800

# ==================================================
# PONTUAÇÃO
# ==================================================

PONTOS_VERMELHO = 1
PONTOS_AMARELO = 2
PONTOS_AZUL = 5

MULTIPLICADOR_AZUL = 2

# ==================================================
# FONTES
# ==================================================

fonte = pygame.font.SysFont("Arial", 30, bold=True)
fonte_media = pygame.font.SysFont("Arial", 22, bold=True)
fonte_pequena = pygame.font.SysFont("Arial", 18)

# ==================================================
# CAMINHOS
# ==================================================

PASTA_JOGO = os.path.dirname(os.path.abspath(__file__))
PASTA_SONS = os.path.join(PASTA_JOGO, "sons")


def caminho_som(nome):
    return os.path.join(PASTA_SONS, nome)


# ==================================================
# CARREGAMENTO SEGURO DE SONS
# ==================================================

def carregar_som_opcional(nome_arquivo, volume=0.7):
    """
    Carrega um som se o arquivo existir.

    Caso o arquivo não exista, o jogo continua funcionando.
    """

    caminho = caminho_som(nome_arquivo)

    if not os.path.exists(caminho):
        print(f"Aviso: som não encontrado: {caminho}")
        return None

    try:
        som = pygame.mixer.Sound(caminho)
        som.set_volume(volume)
        return som

    except pygame.error as erro:
        print(f"Não foi possível carregar {nome_arquivo}: {erro}")
        return None


som_inicio = carregar_som_opcional("start.mp3", 0.7)
som_morte = carregar_som_opcional("death.mp3", 0.8)

# Sons opcionais adicionais
som_comer = carregar_som_opcional("eat.mp3", 0.6)
som_lento = carregar_som_opcional("slow.mp3", 0.8)
som_rapido = carregar_som_opcional("speed.mp3", 0.8)
som_expirar = carregar_som_opcional("expire.mp3", 0.5)

CAMINHO_MUSICA = caminho_som("music.mp3")

canal_inicio = pygame.mixer.Channel(1)
musica_iniciada = False

# ==================================================
# FUNÇÕES DE SOM
# ==================================================

def tocar_som(som):
    """Toca um som somente se ele tiver sido carregado."""

    if som is not None:
        som.play()


def iniciar_audio_jogo():
    """
    Para os áudios anteriores e toca o som inicial.
    Depois, a música de fundo será iniciada.
    """

    global musica_iniciada

    pygame.mixer.music.stop()
    pygame.mixer.stop()

    musica_iniciada = False

    if som_inicio is not None:
        canal_inicio.play(som_inicio)

    else:
        iniciar_musica()


def iniciar_musica():
    """Inicia a música de fundo em repetição."""

    global musica_iniciada

    if musica_iniciada:
        return

    if not os.path.exists(CAMINHO_MUSICA):
        print(f"Aviso: música não encontrada: {CAMINHO_MUSICA}")
        musica_iniciada = True
        return

    try:
        pygame.mixer.music.load(CAMINHO_MUSICA)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)

    except pygame.error as erro:
        print(f"Não foi possível tocar a música: {erro}")

    musica_iniciada = True


def atualizar_audio():
    """Começa a música quando o som de início terminar."""

    if fim_de_jogo:
        return

    if not musica_iniciada and not canal_inicio.get_busy():
        iniciar_musica()


def executar_audio_morte():
    """Para a música e toca o som de morte."""

    global musica_iniciada

    canal_inicio.stop()
    pygame.mixer.music.stop()
    musica_iniciada = False

    tocar_som(som_morte)


# ==================================================
# UTILIDADES
# ==================================================

def direcoes_opostas(direcao_a, direcao_b):
    """Verifica se duas direções são opostas."""

    return (
        direcao_a[0] == -direcao_b[0]
        and direcao_a[1] == -direcao_b[1]
    )


def distancia_em_blocos(posicao_a, posicao_b):
    """
    Calcula uma distância baseada na grade.

    Usa a distância de Manhattan:
    diferença horizontal + diferença vertical.
    """

    diferenca_x = abs(posicao_a[0] - posicao_b[0])
    diferenca_y = abs(posicao_a[1] - posicao_b[1])

    return (diferenca_x + diferenca_y) // TAMANHO_BLOCO


# ==================================================
# SISTEMA DE MENSAGENS
# ==================================================

def definir_mensagem(texto, cor=BRANCO):
    """Mostra uma mensagem temporária na tela."""

    global mensagem_temporaria
    global cor_mensagem
    global inicio_mensagem

    mensagem_temporaria = texto
    cor_mensagem = cor
    inicio_mensagem = pygame.time.get_ticks()


def atualizar_mensagem():
    """Remove a mensagem quando seu tempo terminar."""

    global mensagem_temporaria

    if mensagem_temporaria == "":
        return

    tempo_atual = pygame.time.get_ticks()

    if tempo_atual - inicio_mensagem >= DURACAO_MENSAGEM:
        mensagem_temporaria = ""


# ==================================================
# SISTEMA DE ALIMENTOS
# ==================================================

def sortear_tipo_comida():
    """
    Probabilidade dos alimentos:

    Vermelho: 60%
    Amarelo: 25%
    Azul: 15%
    """

    numero = random.randint(1, 100)

    if numero <= 60:
        return "vermelha"

    if numero <= 85:
        return "amarela"

    return "azul"


def gerar_posicao_comida(corpo_cobra, tipo):
    """
    Gera uma posição livre para o alimento.

    Os alimentos especiais não surgem muito perto
    da cabeça da cobra.
    """

    cabeca = corpo_cobra[0]

    if tipo == "vermelha":
        distancia_minima = 2

    elif tipo == "amarela":
        distancia_minima = 5

    else:
        # O alimento azul deve exigir mais risco.
        distancia_minima = 8

    tentativas = 0

    while tentativas < 1000:
        tentativas += 1

        x = random.randrange(0, LARGURA, TAMANHO_BLOCO)
        y = random.randrange(0, ALTURA, TAMANHO_BLOCO)

        posicao = (x, y)

        if posicao in corpo_cobra:
            continue

        if distancia_em_blocos(posicao, cabeca) < distancia_minima:
            continue

        return posicao

    # Plano alternativo caso não encontre uma posição ideal.
    while True:
        x = random.randrange(0, LARGURA, TAMANHO_BLOCO)
        y = random.randrange(0, ALTURA, TAMANHO_BLOCO)

        posicao = (x, y)

        if posicao not in corpo_cobra:
            return posicao


def gerar_comida(corpo_cobra):
    """Cria um novo alimento."""

    tipo = sortear_tipo_comida()

    return {
        "tipo": tipo,
        "posicao": gerar_posicao_comida(corpo_cobra, tipo),
        "criada_em": pygame.time.get_ticks()
    }


def obter_cor_comida(tipo):
    if tipo == "amarela":
        return AMARELO

    if tipo == "azul":
        return AZUL

    return VERMELHO


def obter_tempo_maximo_comida(tipo):
    """Retorna quanto tempo o alimento pode ficar na tela."""

    if tipo == "amarela":
        return TEMPO_COMIDA_AMARELA

    if tipo == "azul":
        return TEMPO_COMIDA_AZUL

    # A comida vermelha não desaparece.
    return None


def atualizar_validade_comida():
    """
    Substitui um alimento especial quando seu tempo termina.
    """

    global comida

    tempo_maximo = obter_tempo_maximo_comida(comida["tipo"])

    if tempo_maximo is None:
        return

    tempo_atual = pygame.time.get_ticks()
    tempo_na_tela = tempo_atual - comida["criada_em"]

    if tempo_na_tela >= tempo_maximo:
        tipo_expirado = comida["tipo"]

        comida = gerar_comida(cobra)
        tocar_som(som_expirar)

        if tipo_expirado == "azul":
            definir_mensagem("O alimento azul desapareceu!", AZUL)
        else:
            definir_mensagem("O alimento amarelo desapareceu!", AMARELO)


def obter_tempo_restante_comida():
    """Retorna o tempo restante do alimento especial."""

    tempo_maximo = obter_tempo_maximo_comida(comida["tipo"])

    if tempo_maximo is None:
        return None

    tempo_atual = pygame.time.get_ticks()
    tempo_passado = tempo_atual - comida["criada_em"]

    return max(0, tempo_maximo - tempo_passado)


# ==================================================
# EFEITOS DE VELOCIDADE
# ==================================================

def ativar_efeito(novo_efeito):
    """
    Ativa o efeito amarelo ou azul.

    Um efeito cancela o outro.
    Pegar o mesmo efeito reinicia sua duração.
    """

    global efeito_ativo
    global inicio_efeito
    global duracao_efeito

    efeito_anterior = efeito_ativo

    if novo_efeito == "lento":
        duracao_efeito = DURACAO_EFEITO_AMARELO

    else:
        duracao_efeito = DURACAO_EFEITO_AZUL

    efeito_ativo = novo_efeito
    inicio_efeito = pygame.time.get_ticks()

    if efeito_anterior == novo_efeito:

        if novo_efeito == "lento":
            definir_mensagem("Tempo do efeito amarelo renovado!", AMARELO)
        else:
            definir_mensagem("Tempo do efeito azul renovado!", AZUL)

    elif efeito_anterior is not None:

        if efeito_anterior == "rapido":
            definir_mensagem("Efeito azul cancelado pelo amarelo!", AMARELO)
        else:
            definir_mensagem("Efeito amarelo cancelado pelo azul!", AZUL)

    else:

        if novo_efeito == "lento":
            definir_mensagem("Modo lento ativado!", AMARELO)
        else:
            definir_mensagem("Modo de risco ativado: pontos em dobro!", AZUL)


def atualizar_efeito():
    """Finaliza o efeito de velocidade após seu tempo."""

    global efeito_ativo

    if efeito_ativo is None:
        return

    tempo_atual = pygame.time.get_ticks()

    if tempo_atual - inicio_efeito >= duracao_efeito:

        efeito_encerrado = efeito_ativo
        efeito_ativo = None

        if efeito_encerrado == "lento":
            definir_mensagem("Efeito amarelo encerrado.", AMARELO)
        else:
            definir_mensagem("Efeito azul encerrado.", AZUL)


def obter_tempo_restante_efeito():
    if efeito_ativo is None:
        return 0

    tempo_atual = pygame.time.get_ticks()
    tempo_passado = tempo_atual - inicio_efeito

    return max(0, duracao_efeito - tempo_passado)


def obter_intervalo_movimento():
    """Retorna o intervalo atual entre movimentos."""

    if efeito_ativo == "lento":
        return INTERVALO_LENTO

    if efeito_ativo == "rapido":
        return INTERVALO_RAPIDO

    return INTERVALO_NORMAL


def aplicar_comida(tipo):
    """Aplica pontos, sons e efeitos do alimento."""

    global pontuacao
    global azuis_seguidos

    if tipo == "vermelha":

        if efeito_ativo == "rapido":
            pontos_recebidos = PONTOS_VERMELHO * MULTIPLICADOR_AZUL
            definir_mensagem(
                f"Multiplicador azul: +{pontos_recebidos} pontos!",
                AZUL
            )
        else:
            pontos_recebidos = PONTOS_VERMELHO

        pontuacao += pontos_recebidos
        tocar_som(som_comer)

    elif tipo == "amarela":

        pontuacao += PONTOS_AMARELO
        azuis_seguidos = 0

        ativar_efeito("lento")
        tocar_som(som_lento)

    elif tipo == "azul":

        azuis_seguidos += 1

        bonus_sequencia = PONTOS_AZUL * azuis_seguidos
        pontuacao += bonus_sequencia

        ativar_efeito("rapido")
        tocar_som(som_rapido)

        definir_mensagem(
            f"Azul x{azuis_seguidos}: +{bonus_sequencia} pontos!",
            AZUL
        )


# ==================================================
# JOGO
# ==================================================

def reiniciar_jogo():
    """Reinicia todas as variáveis da partida."""

    global cobra
    global direcao
    global proxima_direcao
    global comida
    global pontuacao
    global fim_de_jogo

    global efeito_ativo
    global inicio_efeito
    global duracao_efeito

    global ultimo_movimento
    global mensagem_temporaria
    global inicio_mensagem
    global cor_mensagem

    global azuis_seguidos

    cobra = [
        (LARGURA // 2, ALTURA // 2),
        (LARGURA // 2 - TAMANHO_BLOCO, ALTURA // 2),
        (LARGURA // 2 - 2 * TAMANHO_BLOCO, ALTURA // 2)
    ]

    direcao = DIREITA
    proxima_direcao = DIREITA

    comida = gerar_comida(cobra)

    pontuacao = 0
    azuis_seguidos = 0

    fim_de_jogo = False

    efeito_ativo = None
    inicio_efeito = 0
    duracao_efeito = 0

    ultimo_movimento = pygame.time.get_ticks()

    mensagem_temporaria = ""
    inicio_mensagem = 0
    cor_mensagem = BRANCO

    iniciar_audio_jogo()


def finalizar_jogo():
    """Encerra a partida apenas uma vez."""

    global fim_de_jogo

    if fim_de_jogo:
        return

    fim_de_jogo = True
    executar_audio_morte()


def mover_cobra():
    """Executa um movimento completo da cobra."""

    global direcao
    global comida
    global pontuacao
    global azuis_seguidos

    direcao = proxima_direcao

    cabeca_atual = cobra[0]

    nova_cabeca = (
        cabeca_atual[0] + direcao[0],
        cabeca_atual[1] + direcao[1]
    )

    # Verificação antecipada das paredes
    bateu_na_parede = (
        nova_cabeca[0] < 0
        or nova_cabeca[0] >= LARGURA
        or nova_cabeca[1] < 0
        or nova_cabeca[1] >= ALTURA
    )

    if bateu_na_parede:
        finalizar_jogo()
        return

    cobra.insert(0, nova_cabeca)

    comeu = nova_cabeca == comida["posicao"]

    if comeu:
        tipo_comido = comida["tipo"]

        aplicar_comida(tipo_comido)
        comida = gerar_comida(cobra)

    else:
        cobra.pop()

        # A sequência azul é quebrada quando outro azul
        # não é consumido imediatamente.
        if efeito_ativo != "rapido":
            azuis_seguidos = 0

    bateu_no_corpo = nova_cabeca in cobra[1:]

    if bateu_no_corpo:
        finalizar_jogo()


# ==================================================
# DESENHO
# ==================================================

def desenhar_grade():
    """Desenha uma grade discreta no fundo."""

    for x in range(0, LARGURA, TAMANHO_BLOCO):
        pygame.draw.line(
            tela,
            CINZA_ESCURO,
            (x, 0),
            (x, ALTURA)
        )

    for y in range(0, ALTURA, TAMANHO_BLOCO):
        pygame.draw.line(
            tela,
            CINZA_ESCURO,
            (0, y),
            (LARGURA, y)
        )


def desenhar_comida():
    """Desenha o alimento e seu indicador de validade."""

    posicao = comida["posicao"]
    tipo = comida["tipo"]
    cor = obter_cor_comida(tipo)

    retangulo = pygame.Rect(
        posicao[0],
        posicao[1],
        TAMANHO_BLOCO,
        TAMANHO_BLOCO
    )

    if tipo == "vermelha":
        pygame.draw.rect(tela, cor, retangulo, border_radius=5)

    elif tipo == "amarela":
        pygame.draw.circle(
            tela,
            cor,
            retangulo.center,
            TAMANHO_BLOCO // 2
        )

    else:
        # Azul representado como losango.
        centro_x, centro_y = retangulo.center

        pontos = [
            (centro_x, posicao[1]),
            (posicao[0] + TAMANHO_BLOCO, centro_y),
            (centro_x, posicao[1] + TAMANHO_BLOCO),
            (posicao[0], centro_y)
        ]

        pygame.draw.polygon(tela, cor, pontos)

    tempo_restante = obter_tempo_restante_comida()
    tempo_maximo = obter_tempo_maximo_comida(tipo)

    if tempo_restante is not None and tempo_maximo is not None:

        proporcao = tempo_restante / tempo_maximo
        largura = int(TAMANHO_BLOCO * proporcao)

        pygame.draw.rect(
            tela,
            CINZA,
            (
                posicao[0],
                posicao[1] - 5,
                TAMANHO_BLOCO,
                3
            )
        )

        pygame.draw.rect(
            tela,
            cor,
            (
                posicao[0],
                posicao[1] - 5,
                largura,
                3
            )
        )


def obter_cor_cabeca():
    """Muda a cabeça conforme o efeito ativo."""

    if efeito_ativo == "lento":
        return AMARELO

    if efeito_ativo == "rapido":
        return AZUL

    return VERDE_CABECA


def desenhar_cobra():
    """Desenha a cobra."""

    for indice, bloco in enumerate(cobra):

        if indice == 0:
            cor = obter_cor_cabeca()
        else:
            cor = VERDE_CORPO

        retangulo = pygame.Rect(
            bloco[0],
            bloco[1],
            TAMANHO_BLOCO - 1,
            TAMANHO_BLOCO - 1
        )

        pygame.draw.rect(
            tela,
            cor,
            retangulo,
            border_radius=4
        )


def desenhar_barra_efeito():
    """Desenha a barra de duração do efeito ativo."""

    if efeito_ativo is None or fim_de_jogo:
        return

    tempo_restante = obter_tempo_restante_efeito()
    proporcao = tempo_restante / duracao_efeito

    largura_maxima = 250
    altura_barra = 16

    x = 20
    y = 90

    largura_atual = int(largura_maxima * proporcao)

    if efeito_ativo == "lento":
        cor = AMARELO
        texto = "MODO LENTO"
    else:
        cor = AZUL
        texto = f"MODO RÁPIDO — PONTOS x{MULTIPLICADOR_AZUL}"

    texto_efeito = fonte_media.render(texto, True, cor)
    tela.blit(texto_efeito, (x, 60))

    pygame.draw.rect(
        tela,
        BRANCO,
        (x, y, largura_maxima, altura_barra),
        width=2,
        border_radius=4
    )

    if largura_atual > 0:
        pygame.draw.rect(
            tela,
            cor,
            (x, y, largura_atual, altura_barra),
            border_radius=4
        )

    segundos = tempo_restante / 1000

    texto_tempo = fonte_pequena.render(
        f"{segundos:.1f}s",
        True,
        BRANCO
    )

    tela.blit(
        texto_tempo,
        (x + largura_maxima + 10, y - 2)
    )


def desenhar_interface():
    """Desenha pontuação, efeito e legenda."""

    texto_pontos = fonte.render(
        f"Pontos: {pontuacao}",
        True,
        BRANCO
    )

    tela.blit(texto_pontos, (20, 15))

    desenhar_barra_efeito()

    legenda_1 = fonte_pequena.render(
        "Vermelho: +1",
        True,
        VERMELHO
    )

    legenda_2 = fonte_pequena.render(
        "Amarelo: +2 e reduz a velocidade",
        True,
        AMARELO
    )

    legenda_3 = fonte_pequena.render(
        "Azul: +5 ou mais e ativa pontos em dobro",
        True,
        AZUL
    )

    tela.blit(legenda_1, (20, ALTURA - 70))
    tela.blit(legenda_2, (20, ALTURA - 48))
    tela.blit(legenda_3, (20, ALTURA - 26))

    if mensagem_temporaria:

        texto_mensagem = fonte_media.render(
            mensagem_temporaria,
            True,
            cor_mensagem
        )

        retangulo = texto_mensagem.get_rect(
            center=(LARGURA // 2, 135)
        )

        tela.blit(texto_mensagem, retangulo)


def desenhar_game_over():
    """Desenha a tela de fim de jogo."""

    if not fim_de_jogo:
        return

    camada = pygame.Surface(
        (LARGURA, ALTURA),
        pygame.SRCALPHA
    )

    camada.fill((0, 0, 0, 170))
    tela.blit(camada, (0, 0))

    texto_game_over = fonte.render(
        "FIM DE JOGO",
        True,
        VERMELHO
    )

    texto_pontuacao = fonte_media.render(
        f"Pontuação final: {pontuacao}",
        True,
        BRANCO
    )

    texto_reiniciar = fonte_media.render(
        "Pressione ESPAÇO para reiniciar",
        True,
        BRANCO
    )

    tela.blit(
        texto_game_over,
        texto_game_over.get_rect(
            center=(LARGURA // 2, ALTURA // 2 - 45)
        )
    )

    tela.blit(
        texto_pontuacao,
        texto_pontuacao.get_rect(
            center=(LARGURA // 2, ALTURA // 2)
        )
    )

    tela.blit(
        texto_reiniciar,
        texto_reiniciar.get_rect(
            center=(LARGURA // 2, ALTURA // 2 + 45)
        )
    )


# ==================================================
# PRIMEIRA PARTIDA
# ==================================================

reiniciar_jogo()

# ==================================================
# LOOP PRINCIPAL
# ==================================================

executando = True

while executando:

    # ----------------------------------------------
    # EVENTOS
    # ----------------------------------------------

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            executando = False

        elif evento.type == pygame.KEYDOWN:

            if fim_de_jogo:

                if evento.key == pygame.K_SPACE:
                    reiniciar_jogo()

            else:

                nova_direcao = None

                if evento.key == pygame.K_UP:
                    nova_direcao = CIMA

                elif evento.key == pygame.K_DOWN:
                    nova_direcao = BAIXO

                elif evento.key == pygame.K_LEFT:
                    nova_direcao = ESQUERDA

                elif evento.key == pygame.K_RIGHT:
                    nova_direcao = DIREITA

                if (
                    nova_direcao is not None
                    and not direcoes_opostas(
                        nova_direcao,
                        direcao
                    )
                ):
                    proxima_direcao = nova_direcao

    # ----------------------------------------------
    # ATUALIZAÇÕES INDEPENDENTES DO MOVIMENTO
    # ----------------------------------------------

    atualizar_audio()
    atualizar_mensagem()

    if not fim_de_jogo:
        atualizar_efeito()
        atualizar_validade_comida()

    # ----------------------------------------------
    # MOVIMENTO INDEPENDENTE DO FPS
    # ----------------------------------------------

    tempo_atual = pygame.time.get_ticks()
    intervalo_atual = obter_intervalo_movimento()

    if (
        not fim_de_jogo
        and tempo_atual - ultimo_movimento >= intervalo_atual
    ):
        mover_cobra()
        ultimo_movimento = tempo_atual

    # ----------------------------------------------
    # DESENHO EM 60 FPS
    # ----------------------------------------------

    tela.fill(PRETO)

    desenhar_grade()
    desenhar_comida()
    desenhar_cobra()
    desenhar_interface()
    desenhar_game_over()

    pygame.display.flip()
    relogio.tick(FPS)

# ==================================================
# ENCERRAMENTO
# ==================================================

pygame.mixer.music.stop()
pygame.mixer.stop()
pygame.quit()
sys.exit()
