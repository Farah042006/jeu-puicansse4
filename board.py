# board.py — Règles du Puissance 4 : plateau 6 lignes x 7 colonnes, gravité, détection de victoire.
# Le premier qui aligne 4 pions gagne. Grille pleine sans alignement = match nul

ROWS, COLS = 6, 7
EMPTY, X, O = 0, 1, 2  # X = premier joueur (Rouge), O = second joueur (Jaune) — notation du cours

def opponent(p):#Retourne l’adversaire de p. Elle sert à passer la main après un coup et à ai.py
    return O if p == X else X

class Board:
    """grid[r][c] : r = 0 est la ligne du BAS (ligne 1 du cours), c = 0 est la colonne a."""

    def __init__(self, start=X):
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]
        self.heights = [0] * COLS          # l’indice de la prochaine ligne libre de la colonne.
        self.moves = []                    # pile des colonnes jouées (sert à annuler un coup)
        self.current = start               # joueur dont c'est le tour
        self.winner = EMPTY                # X ou O dès qu'un alignement de 4 existe
        self.win_cells = []                # les cases de l'alignement gagnant (pour l'affichage)

    def copy(self):
        """Copie indépendante (utilisée par le thread de l'ordinateur)."""
        b = Board.__new__(Board) # Il travaille  sur un double du plateau, et le vrai plateau n’est jamais touché.
        b.grid = [row[:] for row in self.grid] #Copie chaque ligne
        b.heights = self.heights[:]
        b.moves = self.moves[:]
        b.current = self.current
        b.winner = self.winner
        b.win_cells = self.win_cells[:]
        return b

    def can_play(self, c):
        return 0 <= c < COLS and self.heights[c] < ROWS

    def is_full(self):
        return len(self.moves) == ROWS * COLS

    def is_over(self):
        return self.winner != EMPTY or self.is_full()

    def is_draw(self):
        return self.winner == EMPTY and self.is_full() #Match nul

    def play(self, c):
        """Joue dans la colonne c. Retourne la ligne où le pion tombe, ou -1 si le coup est impossible."""
        if self.is_over() or not self.can_play(c):
            return -1
        r = self.heights[c]                # le pion tombe sur la première case libre en partant du bas
        self.grid[r][c] = self.current
        self.heights[c] += 1
        self.moves.append(c) #mémorise le coup
        cells = self._alignment(r, c, self.current)#tester l'alignement
        if cells:
            self.winner = self.current
            self.win_cells = cells
        self.current = opponent(self.current)#change the player
        return r

    def undo(self):
        """Annule le dernier coup (utilisé par MinMax : on joue, on explore, on annule)."""
        if not self.moves: #Rien à annuler sur un plateau vide
            return
        c = self.moves.pop()#Dépile la dernière colonne, baisse sa hauteur : r est la ligne du pion à retirer.
        self.heights[c] -= 1
        r = self.heights[c]
        self.current = self.grid[r][c]     # c'est de nouveau au joueur qui avait posé ce pion
        self.grid[r][c] = EMPTY  #Vide la case et efface la victoire éventuelle
        self.winner = EMPTY                # un alignement ne peut venir que du tout dernier coup
        self.win_cells = []

    def _alignment(self, r, c, p):
        """Si le pion de p en (r, c) forme un alignement d'au moins 4, retourne ses cases, sinon None."""
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):      # horizontale, verticale, 2 diagonales
            line = [(r, c)]#On part du pion lui-même.
            for sign in (1, -1):#Les directions opposées sont traitées par sign
                rr, cc = r + sign * dr, c + sign * dc
                while 0 <= rr < ROWS and 0 <= cc < COLS and self.grid[rr][cc] == p:
                    line.append((rr, cc))
                    rr += sign * dr
                    cc += sign * dc
            if len(line) >= 4:
                return line
        return None

    def would_win(self, c, p):
        """True si le joueur p gagnerait immédiatement en jouant la colonne c (sans modifier le plateau)."""
        if not self.can_play(c):#si le joueur p joue dans la colonne c, est-ce qu’il gagne tout de suite ?
            return False
        r = self.heights[c]
        self.grid[r][c] = p
        res = self._alignment(r, c, p) is not None
        self.grid[r][c] = EMPTY
        return res


















