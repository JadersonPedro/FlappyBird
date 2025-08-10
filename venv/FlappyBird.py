"""
Flappy Bird 
Melhorias aplicadas:
 - Estrutura em classes: Passaro, Cano, Chao, Assets, Game
 - Config centralizado com dataclass
 - Carregamento de assets centralizado (evita duplicação)
 - Constantes nomeadas (sem "números mágicos")
 - Game loop encapsulado em Game.run(); suporte a reiniciar sem sair do programa
 - Docstrings e comentários explicativos
 - Tipagem básica e pequenas melhorias de lógica

"""

import os
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# -----------------------------
# Configurações e constantes
# -----------------------------

@dataclass(frozen=True)
class Config:
    TELA_LARGURA: int = 500
    TELA_ALTURA: int = 800
    FPS: int = 30

    # Física do pássaro
    IMPULSO_PULO: float = -10.5
    GRAVIDADE_TERMO: float = 1.5  # usado na fórmula de deslocamento
    DESLOCAMENTO_MAX: float = 16

    # Rotação / animação do pássaro
    ROTACAO_MAXIMA: int = 25
    VELOCIDADE_ROTACAO: int = 20
    TEMPO_ANIMACAO: int = 5
    ANGULO_MIN_ASA: int = -80

    # Cano
    DISTANCIA_CANO: int = 200
    VELOCIDADE_CANO: int = 5
    CANO_ALTURA_MIN: int = 50
    CANO_ALTURA_MAX: int = 450

    # Chão
    VELOCIDADE_CHAO: int = 5

    # Imagens
    IMGS_DIR: str = "imgs"


CFG = Config()

# -----------------------------
# Assets (centraliza carregamento)
# -----------------------------

class Assets:
    """Carrega e guarda imagens e fontes para reutilização."""

    def __init__(self, imgs_dir: str):
        self.imgs_dir = imgs_dir
        self._cache = {}
        pygame.font.init()
        self.font_pontos = pygame.font.SysFont('arial', 40)

        # carregar imagens principais
        self.pipe = self._carregar('pipe.png')
        self.base = self._carregar('base.png')
        self.bg = self._carregar('bg.png')
        self.bird1 = self._carregar('bird1.png')
        self.bird2 = self._carregar('bird2.png')
        self.bird3 = self._carregar('bird3.png')

    def _carregar(self, filename: str, scale2x: bool = True) -> pygame.Surface:
        caminho = os.path.join(self.imgs_dir, filename)
        if caminho in self._cache:
            return self._cache[caminho]
        surf = pygame.image.load(caminho).convert_alpha()
        if scale2x:
            surf = pygame.transform.scale2x(surf)
        self._cache[caminho] = surf
        return surf

    @property
    def imagens_passaro(self) -> List[pygame.Surface]:
        return [self.bird1, self.bird2, self.bird3]


# -----------------------------
# Entidades do jogo
# -----------------------------

class Passaro:
    """Representa o jogador (pássaro)."""

    def __init__(self, x: int, y: int, assets: Assets):
        self.x = x
        self.y = y
        self.assets = assets

        # estado físico
        self.angulo = 0
        self.velocidade = 0.0
        self.altura_inicio_pulo = y
        self.tempo = 0

        # animação
        self.contagem_imagem = 0
        self.imagem = self.assets.imagens_passaro[0]

    def pular(self):
        """Executa o impulso do pulo."""
        self.velocidade = CFG.IMPULSO_PULO
        self.tempo = 0
        self.altura_inicio_pulo = self.y

    def mover(self):
        """Atualiza posição e ângulo conforme física simplificada."""
        self.tempo += 1
        deslocamento = CFG.GRAVIDADE_TERMO * (self.tempo ** 2) + self.velocidade * self.tempo

        # limitar deslocamento (evita "teleporte" muito grande)
        if deslocamento > CFG.DESLOCAMENTO_MAX:
            deslocamento = CFG.DESLOCAMENTO_MAX
        if deslocamento < 0:
            deslocamento -= 2  # pequeno ajuste para subidas mais nítidas

        self.y += deslocamento

        # rotação do pássaro (mais bonito visualmente)
        if deslocamento < 0 or self.y < (self.altura_inicio_pulo + 50):
            if self.angulo < CFG.ROTACAO_MAXIMA:
                self.angulo = CFG.ROTACAO_MAXIMA
        else:
            if self.angulo > CFG.ANGULO_MIN_ASA:
                self.angulo -= CFG.VELOCIDADE_ROTACAO

    def desenhar(self, tela: pygame.Surface):
        """Desenha o pássaro com animação e rotação."""
        self.contagem_imagem += 1

        imgs = self.assets.imagens_passaro
        t = CFG.TEMPO_ANIMACAO
        ciclo = self.contagem_imagem

        if ciclo < t:
            self.imagem = imgs[0]
        elif ciclo < t * 2:
            self.imagem = imgs[1]
        elif ciclo < t * 3:
            self.imagem = imgs[2]
        elif ciclo < t * 4:
            self.imagem = imgs[1]
        else:
            self.imagem = imgs[0]
            self.contagem_imagem = 0

        # quando está caindo bastante, não bater asas
        if self.angulo <= CFG.ANGULO_MIN_ASA:
            self.imagem = imgs[1]
            self.contagem_imagem = t * 2

        # rotacionar mantendo o centro visual
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        pos_centro = self.imagem.get_rect(topleft=(self.x, self.y)).center
        rect = imagem_rotacionada.get_rect(center=pos_centro)
        tela.blit(imagem_rotacionada, rect.topleft)

    def get_mask(self) -> pygame.Mask:
        return pygame.mask.from_surface(self.imagem)


class Cano:
    """Cano com topo e base e lógica de colisão."""

    def __init__(self, x: int, assets: Assets):
        self.x = x
        self.assets = assets
        self.altura = 0
        self.pos_topo = 0
        self.pos_base = 0
        self.CANO_TOPO = pygame.transform.flip(self.assets.pipe, False, True)
        self.CANO_BASE = self.assets.pipe
        self.passou = False
        self.definir_altura()

    def definir_altura(self):
        self.altura = random.randrange(CFG.CANO_ALTURA_MIN, CFG.CANO_ALTURA_MAX)
        self.pos_topo = self.altura - self.CANO_TOPO.get_height()
        self.pos_base = self.altura + CFG.DISTANCIA_CANO

    def mover(self):
        self.x -= CFG.VELOCIDADE_CANO

    def desenhar(self, tela: pygame.Surface):
        tela.blit(self.CANO_TOPO, (self.x, self.pos_topo))
        tela.blit(self.CANO_BASE, (self.x, self.pos_base))

    def colidir(self, passaro: Passaro) -> bool:
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.CANO_BASE)

        distancia_topo = (self.x - passaro.x, self.pos_topo - round(passaro.y))
        distancia_base = (self.x - passaro.x, self.pos_base - round(passaro.y))

        topo_ponto = passaro_mask.overlap(topo_mask, distancia_topo)
        base_ponto = passaro_mask.overlap(base_mask, distancia_base)

        return bool(topo_ponto or base_ponto)


class Chao:
    """Chão que se move horizontalmente (looping)."""

    def __init__(self, y: int, assets: Assets):
        self.y = y
        self.assets = assets
        self.VELOCIDADE = CFG.VELOCIDADE_CHAO
        self.LARGURA = self.assets.base.get_width()
        self.IMAGEM = self.assets.base
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela: pygame.Surface):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))


# -----------------------------
# Funções utilitárias
# -----------------------------

def desenhar_tela(tela: pygame.Surface, assets: Assets, passaros: List[Passaro], canos: List[Cano], chao: Chao, pontos: int):
    """Desenha toda a cena atual na tela."""
    tela.blit(assets.bg, (0, 0))

    for passaro in passaros:
        passaro.desenhar(tela)

    for cano in canos:
        cano.desenhar(tela)

    texto = assets.font_pontos.render(f"Pontuação: {pontos}", True, (255, 255, 255))
    tela.blit(texto, (CFG.TELA_LARGURA - 10 - texto.get_width(), 10))

    chao.desenhar(tela)
    pygame.display.update()


# -----------------------------
# Game controller
# -----------------------------

class Game:
    """Encapsula o loop do jogo e o estado para facilitar reinício e testes."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy - Rework")
        self.tela = pygame.display.set_mode((CFG.TELA_LARGURA, CFG.TELA_ALTURA))
        self.clock = pygame.time.Clock()
        self.assets = Assets(CFG.IMGS_DIR)
        self.reset()

    def reset(self):
        """Prepara um novo estado de jogo (reinício rápido)."""
        self.passaros: List[Passaro] = [Passaro(230, 350, self.assets)]
        self.chao = Chao(730, self.assets)
        self.canos: List[Cano] = [Cano(700, self.assets)]
        self.pontos = 0
        self.rodando = True

    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    for p in self.passaros:
                        p.pular()
                elif evento.key == pygame.K_r:
                    # tecla R reinicia o jogo
                    self.reset()

    def atualizar_estado(self):
        # mover elementos
        for p in self.passaros:
            p.mover()
        self.chao.mover()

        adicionar_cano = False
        remover = []

        for cano in self.canos:
            for i, p in enumerate(list(self.passaros)):
                if cano.colidir(p):
                    # remover pássaro que colidiu
                    if p in self.passaros:
                        self.passaros.remove(p)
                if not cano.passou and p.x > cano.x:
                    cano.passou = True
                    adicionar_cano = True

            cano.mover()
            if cano.x + cano.CANO_TOPO.get_width() < 0:
                remover.append(cano)

        if adicionar_cano:
            self.pontos += 1
            self.canos.append(Cano(CFG.TELA_LARGURA + 100, self.assets))

        for cano in remover:
            if cano in self.canos:
                self.canos.remove(cano)

        # verificar colisão com chão/teto
        for p in list(self.passaros):
            if (p.y + p.imagem.get_height()) > self.chao.y or p.y < 0:
                if p in self.passaros:
                    self.passaros.remove(p)

        # se não houver pássaros, marcar fim de rodada
        if not self.passaros:
            # pausa pequena e reset automático pode ser substituído por tela de Game Over
            self.rodando = False

    def run(self):
        """Loop principal do jogo. Retorna quando o jogador fecha a janela."""
        while True:
            # permitir reiniciar o jogo após fim sem fechar a janela
            self.rodando = True
            while self.rodando:
                self.clock.tick(CFG.FPS)
                self.processar_eventos()
                self.atualizar_estado()
                desenhar_tela(self.tela, self.assets, self.passaros, self.canos, self.chao, self.pontos)

            # Game over: apresentar mensagem e esperar ação do usuário
            self.mostrar_game_over()

            # esperar evento do usuário: R para reiniciar, ESC ou fechar para sair
            espera = True
            while espera:
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        pygame.quit()
                        return
                    elif evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_r:
                            self.reset()
                            espera = False
                        elif evento.key == pygame.K_ESCAPE:
                            pygame.quit()
                            return

    def mostrar_game_over(self):
        """Desenha uma tela simples de Game Over com instruções."""
        # desenhar última imagem do jogo como fundo
        self.tela.blit(self.assets.bg, (0, 0))
        texto_final = self.assets.font_pontos.render("Game Over", True, (255, 0, 0))
        texto_instr = self.assets.font_pontos.render("Pressione R para reiniciar ou Esc para sair", True, (255, 255, 255))
        score_text = self.assets.font_pontos.render(f"Pontuação: {self.pontos}", True, (255, 255, 255))

        self.tela.blit(texto_final, ((CFG.TELA_LARGURA - texto_final.get_width()) // 2, 200))
        self.tela.blit(score_text, ((CFG.TELA_LARGURA - score_text.get_width()) // 2, 300))
        self.tela.blit(texto_instr, ((CFG.TELA_LARGURA - texto_instr.get_width()) // 2, 380))
        pygame.display.update()


# -----------------------------
# Entrypoint
# -----------------------------

def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
