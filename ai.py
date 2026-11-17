# ai.py — Cerveau de l'ordinateur : heuristique B du cours (score par fenêtre), MinMax et Alpha-Bêta.
from board import ROWS, COLS, EMPTY, X, O, opponent

WIN = 1_000_000                       # valeur d'une victoire : bien plus grande que toute valeur heuristique
INF = float("inf") #Représente l'infini mathématique
COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]  # ordre d'exploration : centre d'abord (améliore l'élagage alpha-bêta)
#plus les bons coups sont essayes plus tot plus alpha monte vite


# ---------------------------------------------------------------- Heuristique B : score par fenêtre
def _build_windows():
    """Toutes les fenêtres de 4 cases alignées : 24 horizontales + 21 verticales + 24 diagonales = 69."""
    wins = []
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = [(r + i * dr, c + i * dc) for i in range(4)]#Crée la liste des 4 coordonnées de la fenêtre
                if all(0 <= rr < ROWS and 0 <= cc < COLS for rr, cc in cells):
                    wins.append(cells)
    return wins


WINDOWS = _build_windows()
assert len(WINDOWS) == 69


def evaluate(board, me):
    """Estime une position NON terminale du point de vue de `me` (positif = bon pour `me`).
    Poids symétriques (±5, ±2) et bonus central ±3
    Les alignements de 4 complets ne sont PAS notés ici : c'est la recherche qui renvoie ±WIN."""
    opp = opponent(me)
    g = board.grid # Récupère la grille du plateau
    score = 0
    for r in range(ROWS):                       # bonus central : +3 par pion à moi, -3 par pion adverse (colonne d)
        v = g[r][COLS // 2] # ...on regarde la case au centre exact (colonne 3)
        if v == me:
            score += 3
        elif v == opp:
            score -= 3
    for cells in WINDOWS:  # On parcourt les 69 fenêtres une par une
        mine = theirs = 0 # Dans chaque fenêtre, on compte nos pions et ceux de l'adversaire
        for r, c in cells:
            v = g[r][c]
            if v == me:
                mine += 1
            elif v == opp:
                theirs += 1
        if theirs == 0:                         # fenêtre encore utilisable par moi (les autres cases sont vides)
            if mine == 3:
                score += 5                      # 3 + 1 vide
            elif mine == 2:
                score += 2                      # 2 + 2 vides
        elif mine == 0:                         # fenêtre utilisable par l'adversaire
            if theirs == 3:
                score -= 5
            elif theirs == 2:
                score -= 2
        # fenêtre mixte (les deux couleurs) : "morte", elle vaut 0 ; fenêtre à 1 pion : 0
    return score


# ---------------------------------------------------------------- Valeur d'une position terminale
def terminal_value(board, me, depth):
    """Victoire = WIN + depth (gagner vite vaut plus), défaite = -WIN - depth (perdre tard vaut mieux), nul = 0."""
    if board.winner == me:
        return WIN + depth
    if board.winner == EMPTY:
        return 0
    return -WIN - depth


# ---------------------------------------------------------------- MinMax
def minmax(board, depth, maximizing, me, stats):
    """MAX = `me` (l'ordinateur), MIN = son adversaire. Profondeur limitée, feuilles évaluées par evaluate()."""
    stats["nodes"] += 1
    if board.is_over():
        return terminal_value(board, me, depth)
    if depth == 0:
        return evaluate(board, me)
    if maximizing:
        best = -INF
        for c in COLUMN_ORDER:
            if board.can_play(c):
                board.play(c)
                best = max(best, minmax(board, depth - 1, False, me, stats))
                board.undo()
        return best
    best = INF
    for c in COLUMN_ORDER:
        if board.can_play(c):
            board.play(c)
            best = min(best, minmax(board, depth - 1, True, me, stats))
            board.undo()
    return best


# ---------------------------------------------------------------- Alpha-Bêta
def alphabeta(board, depth, alpha, beta, maximizing, me, stats):
    """Même valeur que minmax(), avec élagage.
    alpha = meilleure valeur que MAX peut déjà garantir, beta = meilleure valeur que MIN peut déjà garantir.
    On coupe dès que beta <= alpha : la suite de la branche ne peut plus changer le choix de MAX."""
    stats["nodes"] += 1
    if board.is_over():
        return terminal_value(board, me, depth)
    if depth == 0:
        return evaluate(board, me)
    if maximizing:
        best = -INF
        for c in COLUMN_ORDER:
            if board.can_play(c):
                board.play(c)
                best = max(best, alphabeta(board, depth - 1, alpha, beta, False, me, stats))
                board.undo()
                alpha = max(alpha, best)
                if beta <= alpha:
                    break                       # coupure
        return best
    best = INF
    for c in COLUMN_ORDER:
        if board.can_play(c):
            board.play(c)
            best = min(best, alphabeta(board, depth - 1, alpha, beta, True, me, stats))
            board.undo()
            beta = min(beta, best)
            if beta <= alpha:
                break                           # coupure
    return best


# ---------------------------------------------------------------- Choix du coup
def best_move(board, me, depth, use_alphabeta=True, check_immediate=True):
    """Retourne (meilleure colonne, nombre de nœuds explorés) pour le joueur `me` (qui doit être au trait).
    check_immediate : conseil du cours, on joue une victoire immédiate / on bloque celle de l'adversaire
    avant de lancer la recherche."""
    stats = {"nodes": 0}
    opp = opponent(me)
    if check_immediate:
        for c in COLUMN_ORDER:                  # 1) je peux gagner tout de suite
            if board.would_win(c, me):
                return c, 0
        for c in COLUMN_ORDER:                  # 2) l'adversaire gagnerait au prochain coup : je bloque
            if board.would_win(c, opp):
                return c, 0
    best_score, best_col = -INF, None
    alpha = -INF
    for c in COLUMN_ORDER:
        if not board.can_play(c):
            continue
        board.play(c)
        if use_alphabeta:
            score = alphabeta(board, depth - 1, alpha, INF, False, me, stats)
        else:
            score = minmax(board, depth - 1, False, me, stats)
        board.undo()
        if score > best_score:                  # égalité : on garde la colonne la plus centrale
            best_score, best_col = score, c
        alpha = max(alpha, best_score)
    return best_col, stats["nodes"]