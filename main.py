# main.py — Interface Pygame : menu, jeu (1 ou 2 grilles MinMax | Alpha-Bêta), Annuler, panneau de fin réouvrable, zoom.
import threading
import time
import pygame
from board import Board, ROWS, COLS, X, O
from ai import best_move

ZOOM = 0.75                                    # taille de la fenêtre à l'écran (1.0 = taille d'origine)
W, H = 700, 820                                # taille LOGIQUE du menu (tout est dessiné à cette taille puis réduit)
MAX_DEPTH = 8

BG = (18, 24, 42)
BLUE, BLUE_DARK = (30, 80, 200), (16, 46, 135)
RED, YELLOW = (228, 52, 62), (250, 205, 50)
WHITE, GREY, GREEN = (255, 255, 255), (160, 175, 210), (70, 210, 120)
COLOR = {X: RED, O: YELLOW}
NAME = {X: "Rouge", O: "Jaune"}
ALGO_NAME = {"mm": "MinMax", "ab": "Alpha-Bêta", "both": "MinMax + Alpha-Bêta"}


class Side:
    """Une grille + l'algorithme qui la joue (en mode "Les deux" il y en a deux : MinMax et Alpha-Bêta)."""

    def __init__(self, algo):
        self.algo = algo
        self.board = Board(X)
        self.thinking = False
        self.result = None             # (token, colonne, nœuds, secondes) envoyé par le thread
        self.t0 = None                 # début du calcul en cours (pour le chrono en direct)
        self.last = None               # (nœuds, secondes) du dernier coup
        self.nodes = 0                 # total de nœuds sur la partie
        self.time = 0.0                # total de secondes de calcul sur la partie


class Game:
    def __init__(self):
        self.screen_name = "menu"
        # réglages du menu
        self.vs_computer = True
        self.depth = 4
        self.algo = "ab"               # "mm", "ab" ou "both"
        self.human_first = True
        # état de la partie
        self.sides = [Side("ab")]
        self.ai_player = O
        self.hover = -1
        self.mouse = (0, 0)
        self.token = 0                 # change à chaque nouvelle partie : ignore les anciens calculs
        self.end_hidden = False        # True : le joueur a caché le panneau de fin pour voir la grille
        # polices
        self.f_title = pygame.font.SysFont("arial", 44, bold=True)
        self.f_big = pygame.font.SysFont("arial", 30, bold=True)
        self.f_mid = pygame.font.SysFont("arial", 22, bold=True)
        self.f_small = pygame.font.SysFont("arial", 17)
        # boutons du menu
        self.b_hh = pygame.Rect(60, 150, 285, 70)
        self.b_hc = pygame.Rect(355, 150, 285, 70)
        self.b_depth = [pygame.Rect(60 + i * 72, 290, 64, 56) for i in range(MAX_DEPTH)]
        self.b_mm = pygame.Rect(60, 420, 185, 60)
        self.b_ab = pygame.Rect(257, 420, 185, 60)
        self.b_both = pygame.Rect(454, 420, 186, 60)
        self.b_human = pygame.Rect(60, 550, 285, 60)
        self.b_comp = pygame.Rect(355, 550, 285, 60)
        self.b_play = pygame.Rect(180, 680, 340, 70)
        self.layout()

    # ------------------------------------------------------------ disposition (dépend du mode)
    def both_mode(self):
        return self.vs_computer and self.algo == "both"

    def layout(self):
        """Taille logique de la fenêtre, taille des cases, position des grilles et des boutons du jeu."""
        if self.screen_name == "menu":
            self.w, self.h, self.cell, self.bx, self.by = W, H, 90, [35], 150
        elif self.both_mode():
            self.w, self.h, self.cell, self.bx, self.by = 940, 770, 60, [25, 495], 210
        else:
            self.w, self.h, self.cell, self.bx, self.by = 700, 820, 90, [35], 150
        self.b_new = pygame.Rect(self.w // 2 - 320, self.h - 62, 200, 46)
        self.b_undo = pygame.Rect(self.w // 2 - 100, self.h - 62, 200, 46)
        self.b_menu = pygame.Rect(self.w // 2 + 120, self.h - 62, 200, 46)
        self.b_result = pygame.Rect(self.w - 190, 18, 170, 38)       # rouvre le panneau de fin de partie

    def window_size(self):
        return self.w, self.h

    def end_rects(self):
        """Panneau de fin de partie (centré sur les grilles) et ses 3 boutons : rejouer, menu principal, voir la grille."""
        cx, cy = self.w // 2, self.by + ROWS * self.cell // 2
        panel = pygame.Rect(0, 0, 420, 240)
        panel.center = (cx, cy)
        b_replay = pygame.Rect(panel.x + 30, panel.y + 90, 360, 56)
        b_home = pygame.Rect(panel.x + 30, panel.y + 165, 175, 50)
        b_view = pygame.Rect(panel.x + 215, panel.y + 165, 175, 50)
        return panel, b_replay, b_home, b_view

    # ------------------------------------------------------------ navigation
    def cancel_ai(self):
        self.token += 1
        for s in self.sides:
            s.thinking = False
            s.result = None

    def new_game(self):
        self.cancel_ai()
        self.end_hidden = False
        self.ai_player = O if self.human_first else X     # l'ordinateur joue l'autre couleur
        if self.both_mode():
            algos = ["mm", "ab"]
        else:
            algos = [self.algo if self.vs_computer and self.algo != "both" else "ab"]
        self.sides = [Side(a) for a in algos]

    def start_game(self):
        self.screen_name = "game"
        self.layout()
        self.new_game()

    def back_to_menu(self):
        self.cancel_ai()
        self.screen_name = "menu"
        self.layout()

    # ------------------------------------------------------------ jeu
    def thinking(self):
        return any(s.thinking for s in self.sides)

    def game_over(self):
        """True quand la partie est finie et que plus aucun calcul ne tourne (en mode "Les deux" : les 2 ont fini)."""
        return self.screen_name == "game" and not self.thinking() and self.sides[0].board.is_over()

    def game_over_shown(self):
        """True quand le panneau de fin doit être affiché."""
        return self.game_over() and not self.end_hidden

    def human_turn(self):
        b = self.sides[0].board
        return not b.is_over() and not self.thinking() and (not self.vs_computer or b.current != self.ai_player)

    def play_column(self, col):
        if 0 <= col < COLS and self.human_turn():
            for s in self.sides:                          # le même coup humain est joué sur toutes les grilles
                s.board.play(col)

    def undo_move(self):
        """Contre l'ordinateur : revient au dernier moment où c'était à l'humain de jouer.
        Humain vs Humain : annule un seul coup. Impossible pendant un calcul."""
        if self.thinking():
            return
        mini = 0 if (self.human_first or not self.vs_computer) else 1   # si l'ordi a commencé, on garde son 1er coup
        for s in self.sides:
            b = s.board
            if len(b.moves) > mini:
                b.undo()
            if self.vs_computer:
                while b.current == self.ai_player and len(b.moves) > mini:
                    b.undo()
        self.end_hidden = False

    def col_at(self, pos):
        x, y = pos
        if not (self.by - 50 <= y < self.by + ROWS * self.cell):
            return -1
        for x0 in self.bx:
            if x0 <= x < x0 + COLS * self.cell:
                return (x - x0) // self.cell
        return -1

    def start_ai(self, side):
        """L'ordinateur réfléchit dans un thread, sur une COPIE de la grille (la fenêtre ne gèle pas)."""
        side.thinking = True
        side.t0 = t0 = time.perf_counter()
        token, snapshot = self.token, side.board.copy()
        me, depth, algo = self.ai_player, self.depth, side.algo
        check = not self.both_mode()      # en mode "Les deux" : pas de raccourci, pour comparer les vraies recherches

        def work():
            col, nodes = best_move(snapshot, me, depth, use_alphabeta=(algo == "ab"), check_immediate=check)
            if token == self.token:
                side.result = (token, col, nodes, time.perf_counter() - t0)

        threading.Thread(target=work, daemon=True).start()

    def update(self):
        if self.screen_name != "game":
            return
        for s in self.sides:
            b = s.board
            if self.vs_computer and not b.is_over() and b.current == self.ai_player and not s.thinking:
                self.start_ai(s)
            if s.result is not None:
                token, col, nodes, sec = s.result
                s.result = None
                if token == self.token:
                    s.thinking = False
                    s.last = (nodes, sec)
                    s.nodes += nodes
                    s.time += sec
                    b.play(col)

    # ------------------------------------------------------------ événements (positions déjà en coordonnées logiques)
    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.mouse = e.pos
            self.hover = self.col_at(e.pos)
        elif self.screen_name == "menu":
            self.handle_menu(e)
        else:
            self.handle_game(e)

    def handle_menu(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            p = e.pos
            if self.b_hh.collidepoint(p):
                self.vs_computer = False
            elif self.b_hc.collidepoint(p):
                self.vs_computer = True
            elif self.b_play.collidepoint(p):
                self.start_game()
            elif self.vs_computer:
                if self.b_mm.collidepoint(p):
                    self.algo = "mm"
                elif self.b_ab.collidepoint(p):
                    self.algo = "ab"
                elif self.b_both.collidepoint(p):
                    self.algo = "both"
                elif self.b_human.collidepoint(p):
                    self.human_first = True
                elif self.b_comp.collidepoint(p):
                    self.human_first = False
                for i, r in enumerate(self.b_depth):
                    if r.collidepoint(p):
                        self.depth = i + 1
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start_game()
            elif pygame.K_1 <= e.key <= pygame.K_8 and self.vs_computer:
                self.depth = e.key - pygame.K_1 + 1

    def handle_game(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.game_over_shown():                         # boutons du panneau de fin de partie
                _, b_replay, b_home, b_view = self.end_rects()
                if b_replay.collidepoint(e.pos):
                    self.new_game()
                    return
                if b_home.collidepoint(e.pos):
                    self.back_to_menu()
                    return
                if b_view.collidepoint(e.pos):
                    self.end_hidden = True
                    return
            elif self.game_over() and self.b_result.collidepoint(e.pos):    # panneau caché : le rouvrir
                self.end_hidden = False
                return
            if self.b_new.collidepoint(e.pos):
                self.new_game()
            elif self.b_undo.collidepoint(e.pos):
                self.undo_move()
            elif self.b_menu.collidepoint(e.pos):
                self.back_to_menu()
            else:
                self.play_column(self.col_at(e.pos))
        elif e.type == pygame.KEYDOWN:
            if pygame.K_1 <= e.key <= pygame.K_7:
                self.play_column(e.key - pygame.K_1)
            elif e.key == pygame.K_r:
                self.new_game()
            elif e.key == pygame.K_u:
                self.undo_move()
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.game_over_shown():
                    self.new_game()                            # panneau visible : Entrée = rejouer
                elif self.game_over():
                    self.end_hidden = False                    # panneau caché : Entrée = le rouvrir
            elif e.key == pygame.K_ESCAPE:
                self.back_to_menu()

    # ------------------------------------------------------------ dessin
    def say(self, screen, text, font, color, x, y):
        s = font.render(text, True, color)
        screen.blit(s, s.get_rect(center=(x, y)))

    def button(self, screen, rect, label, selected=False, enabled=True, font=None):
        font = font or self.f_mid
        if not enabled:
            fill, border, txt = (24, 30, 48), (40, 48, 70), (95, 105, 135)
        elif selected:
            fill, border, txt = (55, 78, 150), YELLOW, WHITE
        elif rect.collidepoint(self.mouse):
            fill, border, txt = (65, 85, 140), (110, 130, 190), WHITE
        else:
            fill, border, txt = (45, 60, 105), (90, 110, 170), WHITE
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, border, rect, 3 if selected else 2, border_radius=12)
        self.say(screen, label, font, txt, rect.centerx, rect.centery)

    def draw_menu(self, screen):
        screen.fill(BG)
        on = self.vs_computer
        dim = (90, 100, 130)
        self.say(screen, "PUISSANCE 4", self.f_title, WHITE, W // 2, 60)
        self.say(screen, "MODE DE JEU", self.f_mid, GREY, W // 2, 120)
        self.button(screen, self.b_hh, "Humain vs Humain", not on)
        self.button(screen, self.b_hc, "Humain vs Ordinateur", on)

        self.say(screen, "PROFONDEUR DE L'ARBRE MINMAX", self.f_mid, GREY if on else dim, W // 2, 260)
        for i, r in enumerate(self.b_depth):
            self.button(screen, r, str(i + 1), on and self.depth == i + 1, on, self.f_big)
        self.say(screen, f"profondeur {self.depth}" if on else "non utilisée en Humain vs Humain",
                 self.f_small, YELLOW if on else dim, W // 2, 370)

        self.say(screen, "ALGORITHME", self.f_mid, GREY if on else dim, W // 2, 395)
        self.button(screen, self.b_mm, "MinMax", on and self.algo == "mm", on)
        self.button(screen, self.b_ab, "Alpha-Bêta", on and self.algo == "ab", on)
        self.button(screen, self.b_both, "Les deux", on and self.algo == "both", on)
        if on and self.algo == "both":
            self.say(screen, "2 grilles : MinMax et Alpha-Bêta en parallèle", self.f_small, YELLOW, W // 2, 500)

        self.say(screen, "QUI COMMENCE ?", self.f_mid, GREY if on else dim, W // 2, 525)
        self.button(screen, self.b_human, "Humain (Rouge)", on and self.human_first, on)
        self.button(screen, self.b_comp, "Ordinateur (Rouge)", on and not self.human_first, on)

        hover = self.b_play.collidepoint(self.mouse)
        pygame.draw.rect(screen, (55, 190, 110) if hover else (40, 160, 90), self.b_play, border_radius=16)
        self.say(screen, "JOUER", self.f_big, WHITE, self.b_play.centerx, self.b_play.centery)
        self.say(screen, "Entrée : jouer   |   1 à 8 : profondeur", self.f_small, (110, 125, 160), W // 2, 785)

    def status(self):
        b = self.sides[0].board
        if self.vs_computer and self.thinking():
            return "L'ordinateur réfléchit...", COLOR[self.ai_player]
        if b.winner:
            if self.vs_computer:
                return ("Vous avez gagné !" if b.winner != self.ai_player else "L'ordinateur a gagné !"), COLOR[b.winner]
            return f"Victoire du joueur {NAME[b.winner]} !", COLOR[b.winner]
        if b.is_draw():
            return "Match nul !", WHITE
        if self.vs_computer:
            return "À vous de jouer", COLOR[b.current]
        return f"Au tour du joueur {NAME[b.current]}", COLOR[b.current]

    def draw_grid(self, screen, side, x0):
        """Dessine une grille (ligne 0 du plateau = ligne du BAS à l'écran), son alignement gagnant et le pion fantôme."""
        b, cell, by = side.board, self.cell, self.by
        r1, r2 = cell // 2 - cell // 22, cell // 2 - cell // 11
        pygame.draw.rect(screen, BLUE, (x0 - 10, by - 10, COLS * cell + 20, ROWS * cell + 20), border_radius=24)
        for r in range(ROWS):
            for c in range(COLS):
                cx, cy = x0 + c * cell + cell // 2, by + (ROWS - 1 - r) * cell + cell // 2
                v = b.grid[r][c]
                pygame.draw.circle(screen, BLUE_DARK, (cx, cy), r1)
                pygame.draw.circle(screen, COLOR[v] if v else BG, (cx, cy), r2)
        for r, c in b.win_cells:                                   # alignement gagnant entouré en blanc
            cx, cy = x0 + c * cell + cell // 2, by + (ROWS - 1 - r) * cell + cell // 2
            pygame.draw.circle(screen, WHITE, (cx, cy), cell // 2 - cell // 15, max(3, cell // 18))
        if self.hover >= 0 and self.human_turn() and b.can_play(self.hover):      # pion fantôme
            ghost = pygame.Surface((cell, cell), pygame.SRCALPHA)
            pygame.draw.circle(ghost, (*COLOR[b.current], 140), (cell // 2, cell // 2), r2)
            screen.blit(ghost, (x0 + self.hover * cell, by - cell))
        for c in range(COLS):                                       # numéros de colonnes = touches 1..7
            self.say(screen, str(c + 1), self.f_small, GREY, x0 + c * cell + cell // 2, by + ROWS * cell + 24)

    def draw_panel(self, screen, side, x0):
        """Mode "Les deux" : nom de l'algorithme au-dessus, chrono en direct et totaux en dessous."""
        mid = x0 + COLS * self.cell // 2
        self.say(screen, ALGO_NAME[side.algo], self.f_big, WHITE, mid, 168)
        y = self.by + ROWS * self.cell
        if side.thinking:
            self.say(screen, f"calcul en cours... {time.perf_counter() - side.t0:.2f} s", self.f_mid, YELLOW, mid, y + 52)
        elif side.last:
            self.say(screen, f"dernier coup : {side.last[0]} nœuds, {side.last[1]:.2f} s", self.f_mid, GREEN, mid, y + 52)
        self.say(screen, f"total : {side.nodes} nœuds, {side.time:.2f} s", self.f_small, GREY, mid, y + 80)

    def draw_end_panel(self, screen):
        """Panneau de fin de partie : résultat + Rejouer / Menu principal / Voir la grille."""
        panel, b_replay, b_home, b_view = self.end_rects()
        surf = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (10, 14, 28, 225), surf.get_rect(), border_radius=20)
        pygame.draw.rect(surf, (90, 110, 170, 255), surf.get_rect(), 3, border_radius=20)
        screen.blit(surf, panel.topleft)
        txt, col = self.status()
        self.say(screen, txt, self.f_big, col, panel.centerx, panel.y + 48)
        hover = b_replay.collidepoint(self.mouse)                  # bouton principal en vert
        pygame.draw.rect(screen, (55, 190, 110) if hover else (40, 160, 90), b_replay, border_radius=14)
        self.say(screen, "Rejouer", self.f_big, WHITE, b_replay.centerx, b_replay.centery)
        self.button(screen, b_home, "Menu principal")
        self.button(screen, b_view, "Voir la grille")

    def draw_game(self, screen):
        screen.fill(BG)
        w = self.w
        self.say(screen, "PUISSANCE 4", self.f_title, WHITE, w // 2, 38)
        txt, col = self.status()
        self.say(screen, txt, self.f_big, col, w // 2, 88)

        if self.both_mode():
            self.say(screen, f"MinMax | Alpha-Bêta en parallèle  |  profondeur {self.depth}", self.f_small, GREY, w // 2, 124)
            for s, x0 in zip(self.sides, self.bx):
                self.draw_grid(screen, s, x0)
                self.draw_panel(screen, s, x0)
            mm, ab = self.sides
            if mm.last and ab.last and not self.thinking():          # comparaison une fois les deux calculs finis
                (n1, t1), (n2, t2) = mm.last, ab.last
                same = mm.board.grid == ab.board.grid
                self.say(screen, f"Alpha-Bêta : {n1 / max(n2, 1):.1f}x moins de nœuds, {t1 / max(t2, 1e-9):.1f}x plus rapide"
                                 f"  |  mêmes coups : {'oui' if same else 'NON'}",
                         self.f_mid, GREEN if same else RED, w // 2, self.h - 88)
        else:
            s = self.sides[0]
            if self.vs_computer:
                info = f"{ALGO_NAME[s.algo]}  |  profondeur {self.depth}"
                if s.last:
                    info += f"  |  dernier coup : {s.last[0]} nœuds, {s.last[1]:.2f} s"
            else:
                info = "Humain vs Humain"
            self.say(screen, info, self.f_small, GREY, w // 2, 124)
            self.draw_grid(screen, s, self.bx[0])

        self.button(screen, self.b_new, "Nouvelle (R)")
        self.button(screen, self.b_undo, "Annuler (U)",
                    enabled=not self.thinking() and len(self.sides[0].board.moves) > 0)
        self.button(screen, self.b_menu, "Menu (Échap)")
        if self.game_over_shown():                                   # panneau de fin, par-dessus les grilles
            self.draw_end_panel(screen)
        elif self.game_over():                                       # panneau caché : bouton pour le rouvrir
            self.button(screen, self.b_result, "Résultat (Entrée)", selected=True, font=self.f_small)

    def draw(self, screen):
        if self.screen_name == "menu":
            self.draw_menu(screen)
        else:
            self.draw_game(screen)


def fit_scale(size, desktop):
    """Zoom de la fenêtre : ZOOM, mais jamais plus grand que l'écran."""
    (w, h), (dw, dh) = size, desktop
    return min(ZOOM, (dw - 40) / w, (dh - 100) / h)


def main():
    pygame.init()
    try:
        desktop = pygame.display.get_desktop_sizes()[0]
    except Exception:
        desktop = (1920, 1080)
    game = Game()
    size = game.window_size()
    scale = fit_scale(size, desktop)
    screen = pygame.display.set_mode((int(size[0] * scale), int(size[1] * scale)))
    canvas = pygame.Surface(size)                            # on dessine à taille logique, puis on réduit à l'écran
    pygame.display.set_caption("Puissance 4 — MinMax / Alpha-Bêta")
    clock = pygame.time.Clock()
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                continue
            if e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                pos = (int(e.pos[0] / scale), int(e.pos[1] / scale))        # écran -> coordonnées logiques
                e = pygame.event.Event(e.type, {**e.dict, "pos": pos})
            game.handle_event(e)
        size = game.window_size()
        if size != canvas.get_size():                        # menu <-> jeu <-> mode "Les deux"
            scale = fit_scale(size, desktop)
            screen = pygame.display.set_mode((int(size[0] * scale), int(size[1] * scale)))
            canvas = pygame.Surface(size)
        game.update()
        game.draw(canvas)
        screen.blit(pygame.transform.smoothscale(canvas, screen.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()