import ui
from math import inf
from random import choice
import time

# ============================================================
# CORE GAME LOGIC
# ============================================================

def make_empty_board():
    return [[0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]]

def winningPlayer(board, player):
    lines = [
        board[0], board[1], board[2],
        [board[0][0], board[1][0], board[2][0]],
        [board[0][1], board[1][1], board[2][1]],
        [board[0][2], board[1][2], board[2][2]],
        [board[0][0], board[1][1], board[2][2]],
        [board[0][2], board[1][1], board[2][0]],
    ]
    return [player, player, player] in lines

def blanks(board):
    return [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

def boardFull(board):
    return len(blanks(board)) == 0

def setMove(board, x, y, player):
    board[x][y] = player

def getScore(board):
    if winningPlayer(board, 1):
        return 10
    if winningPlayer(board, -1):
        return -10
    return 0

# ============================================================
# MINIMAX
# ============================================================

def minimax(board, depth, player, stats=None):
    if stats:
        stats['nodes'] += 1

    if depth == 0 or winningPlayer(board, 1) or winningPlayer(board, -1) or boardFull(board):
        return -1, -1, getScore(board)

    best = -inf if player == 1 else inf
    best_move = (-1, -1)

    for (x, y) in blanks(board):
        setMove(board, x, y, player)
        _, _, score = minimax(board, depth - 1, -player, stats)
        setMove(board, x, y, 0)

        if player == 1:
            if score > best:
                best = score
                best_move = (x, y)
        else:
            if score < best:
                best = score
                best_move = (x, y)

    return best_move[0], best_move[1], best

# ============================================================
# ALPHA-BETA MINIMAX
# ============================================================

def abminimax(board, depth, alpha, beta, player, stats=None):
    if stats:
        stats['nodes'] += 1

    if depth == 0 or winningPlayer(board, 1) or winningPlayer(board, -1) or boardFull(board):
        return -1, -1, getScore(board)

    best_move = (-1, -1)

    for (x, y) in blanks(board):
        setMove(board, x, y, player)
        _, _, score = abminimax(board, depth - 1, alpha, beta, -player, stats)
        setMove(board, x, y, 0)

        if player == 1:
            if score > alpha:
                alpha = score
                best_move = (x, y)
        else:
            if score < beta:
                beta = score
                best_move = (x, y)

        if alpha >= beta:
            if stats:
                stats['pruned'] += 1
            break

    return best_move[0], best_move[1], alpha if player == 1 else beta

# ============================================================
# HELPER MOVES
# ============================================================

def find_winning_move(board, p):
    for (x, y) in blanks(board):
        setMove(board, x, y, p)
        win = winningPlayer(board, p)
        setMove(board, x, y, 0)
        if win:
            return x, y
    return None

def pick_heuristic_move(board):
    if board[1][1] == 0:
        return 1, 1
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    open_corners = [c for c in corners if board[c[0]][c[1]] == 0]
    if open_corners:
        return choice(open_corners)
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    open_sides = [s for s in sides if board[s[0]][s[1]] == 0]
    if open_sides:
        return choice(open_sides)
    return None

# ============================================================
# UI VIEW
# ============================================================

class TicTacToeView(ui.View):

    def __init__(self):
        super().__init__()
        self.name = "Tic-Tac-Toe"

        # game state
        self.board = make_empty_board()
        self.human = 1     # X
        self.comp = -1     # O
        self.game_over = False
        self.difficulty = "Hard"
        self.hint_active = False

        # performance
        self.total_minimax_time = 0.0
        self.total_alphabeta_time = 0.0
        self.total_moves = 0
        self.move_logs = []   # for Hard mode

        # animations
        self._thinking = False
        self._think_step = 0

        # theme
        self.night_mode = False
        self.update_theme()

        # ============================
        # UI ELEMENTS
        # ============================

        # Title
        self.title_label = ui.Label(
            text="TIC-TAC-TOE",
            alignment=ui.ALIGN_CENTER,
            font=("<System-Bold>", 26)
        )
        self.add_subview(self.title_label)

        # Night mode button
        self.night_btn = ui.Button(
            title="🌙",
            action=self.toggle_night
        )
        self.add_subview(self.night_btn)

        # Player selection
        self.player_label = ui.Label(
            text="YOU PLAY:",
            font=("<System>", 13)
        )
        self.add_subview(self.player_label)

        self.you_seg = ui.SegmentedControl(
            segments=[" X", " O"],
            action=self.change_player
        )
        self.you_seg.selected_index = 0
        self.add_subview(self.you_seg)

        # Difficulty
        self.diff_label = ui.Label(
            text="DIFFICULTY:",
            font=("<System>", 13)
        )
        self.add_subview(self.diff_label)

        self.diff_seg = ui.SegmentedControl(
            segments=["Easy", "Medium", "Hard"]
        )
        self.diff_seg.selected_index = 2
        self.add_subview(self.diff_seg)

        # Button row
        self.new_btn = ui.Button(title="NEW GAME", action=self.new_game)
        self.hint_btn = ui.Button(title="HINT", action=self.show_hint)
        self.reset_btn = ui.Button(title="RESET", action=self.reset_board)

        for b in (self.new_btn, self.hint_btn, self.reset_btn):
            self.add_subview(b)

        # Status label
        self.status_label = ui.Label(
            text="Choose settings, then tap NEW GAME",
            alignment=ui.ALIGN_CENTER,
            font=("<System-Medium>", 15),
            number_of_lines=2
        )
        self.add_subview(self.status_label)

        # Grid buttons
        self.btns = [[None] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                b = ui.Button(title=" ")
                b.font = ("<System-Bold>", 42)
                b.corner_radius = 12
                b.border_width = 2
                b.action = self.make_tap(i, j)
                self.btns[i][j] = b
                self.add_subview(b)

        # Apply theme at the end so colors are correct
        self.apply_theme()

    # ============================================================
    # THEME
    # ============================================================

    def update_theme(self):
        if self.night_mode:
            self.bg_color = "#1a1a2e"
            self.text_color = "#e4e4e4"
            self.label_color = "#b5b5b5"
            self.board_bg = "#0e1621"
            self.board_border = "#2d3561"
            self.pill_bg = "#34495e"
            self.pill_text = "#f0f0f0"
            self.night_btn_bg = "#2c3e50"
        else:
            self.bg_color = "#f5f7fa"
            self.text_color = "#2c3e50"
            self.label_color = "#7f8c8d"
            self.board_bg = "white"
            self.board_border = "#bdc3c7"
            self.pill_bg = "#3498db"
            self.pill_text = "white"
            self.night_btn_bg = "#ecf0f1"

    def style_pill_button(self, btn, bg=None):
        btn.corner_radius = 18
        btn.border_width = 0
        btn.background_color = bg if bg is not None else self.pill_bg
        btn.tint_color = self.pill_text
        btn.font = ("<System-Bold>", 14)
        btn.alpha = 1.0

    def apply_theme(self):
        self.background_color = self.bg_color
        self.title_label.text_color = self.text_color
        self.status_label.text_color = self.text_color
        self.player_label.text_color = self.label_color
        self.diff_label.text_color = self.label_color

        # style main pill buttons
        for b in (self.new_btn, self.hint_btn, self.reset_btn):
            self.style_pill_button(b)

        # style night button as a light pill
        self.style_pill_button(self.night_btn, bg=self.night_btn_bg)
        self.night_btn.tint_color = "#f1c40f" if self.night_mode else "#2c3e50"

        # grid colors
        for i in range(3):
            for j in range(3):
                b = self.btns[i][j]
                if self.board[i][j] == 0:
                    b.background_color = self.board_bg
                    b.border_color = self.board_border
                b.tint_color = self.text_color

    def toggle_night(self, sender):
        self.night_mode = not self.night_mode
        self.update_theme()
        self.apply_theme()

    # ============================================================
    # LAYOUT
    # ============================================================

    def layout(self):
        W, H = self.width, self.height
        pad = 12

        # Title + night
        self.title_label.frame = (pad, pad + 4, W - pad * 2 - 40, 30)
        self.night_btn.frame = (W - pad - 40, pad + 4, 38, 34)

        # YOU PLAY
        y = pad + 48
        self.player_label.frame = (pad, y, W - pad * 2, 20)
        self.you_seg.frame = (pad, y + 22, W - pad * 2, 30)

        # DIFFICULTY
        y += 66
        self.diff_label.frame = (pad, y, W - pad * 2, 20)
        self.diff_seg.frame = (pad, y + 22, W - pad * 2, 30)

        # Buttons row
        y += 68
        bw = (W - pad * 4) / 3.0
        self.new_btn.frame = (pad, y, bw, 40)
        self.hint_btn.frame = (pad * 2 + bw, y, bw, 40)
        self.reset_btn.frame = (pad * 3 + bw * 2, y, bw, 40)

        # Status
        y += 52
        self.status_label.frame = (pad, y, W - pad * 2, 50)

        # Grid
        y += 70
        grid_size = min(W - pad * 2, H - y - pad * 2)
        cell = grid_size / 3.0
        x0 = (W - grid_size) / 2.0

        for i in range(3):
            for j in range(3):
                self.btns[i][j].frame = (
                    x0 + j * cell,
                    y + i * cell,
                    cell - 6,
                    cell - 6
                )

    # ============================================================
    # PLAYER & GAME CONTROL
    # ============================================================

    def change_player(self, sender):
        if sender.selected_index == 0:
            self.human = 1
            self.comp = -1
        else:
            self.human = -1
            self.comp = 1

    def reset_board(self, sender=None):
        self.board = make_empty_board()
        self.game_over = False
        self.hint_active = False
        self.total_minimax_time = 0.0
        self.total_alphabeta_time = 0.0
        self.total_moves = 0
        self.move_logs = []

        for i in range(3):
            for j in range(3):
                b = self.btns[i][j]
                b.title = " "
                b.enabled = True
                b.alpha = 1.0
                b.background_color = self.board_bg
                b.border_color = self.board_border

        self.status_label.text = "Board reset."

    def new_game(self, sender=None):
        self.reset_board()
        self.difficulty = ["Easy", "Medium", "Hard"][self.diff_seg.selected_index]

        if self.human == 1:
            self.status_label.text = "You start (X)."
        else:
            self.status_label.text = "AI starts."
            ui.delay(self.computer_turn, 0.4)

    # ============================================================
    # INPUT HANDLING
    # ============================================================

    def make_tap(self, x, y):
        def tap(sender):
            self.on_click(x, y)
        return tap

    def on_click(self, x, y):
        if self.game_over:
            return
        if self.board[x][y] != 0:
            return

        # clear old hint highlight if active
        if self.hint_active:
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == 0:
                        b = self.btns[i][j]
                        b.background_color = self.board_bg
                        b.border_color = self.board_border
                        b.border_width = 2
            self.hint_active = False

        setMove(self.board, x, y, self.human)
        self.update_buttons()
        self.animate_pop(self.btns[x][y])

        if self.check_end():
            return

        self.start_thinking()
        ui.delay(self.computer_turn, 0.4)

    # ============================================================
    # UPDATE GRID
    # ============================================================

    def update_buttons(self):
        icons = {1: "❌", -1: "⭕", 0: " "}
        for i in range(3):
            for j in range(3):
                v = self.board[i][j]
                b = self.btns[i][j]
                b.title = icons[v]
                if v == 0:
                    b.background_color = self.board_bg
                    b.border_color = self.board_border
                else:
                    if v == self.human:
                        b.background_color = "#d4efdf"
                        b.border_color = "#27ae60"
                    else:
                        b.background_color = "#fadbd8"
                        b.border_color = "#e74c3c"

    # ============================================================
    # AI TURN
    # ============================================================

    def computer_turn(self):
        self.stop_thinking()
        if self.game_over:
            return

        empty = blanks(self.board)
        if not empty:
            self.check_end()
            return

        if self.difficulty == "Easy":
            row, col = choice(empty)

        elif self.difficulty == "Medium":
            move = find_winning_move(self.board, self.comp)
            if not move:
                move = find_winning_move(self.board, self.human)
            if not move:
                move = pick_heuristic_move(self.board)
            if not move:
                move = choice(empty)
            row, col = move

        else:  # Hard
            mm_stats = {'nodes': 0, 'pruned': 0}
            ab_stats = {'nodes': 0, 'pruned': 0}

            t = time.time()
            minimax(self.board, len(empty), self.comp, mm_stats)
            mm_t = time.time() - t

            t = time.time()
            ax, ay, _ = abminimax(self.board, len(empty), -inf, inf, self.comp, ab_stats)
            ab_t = time.time() - t

            row, col = ax, ay
            if row == -1:
                row, col = choice(empty)

            self.total_minimax_time += mm_t
            self.total_alphabeta_time += ab_t
            self.total_moves += 1

            self.move_logs.append(
                f"#{self.total_moves}  Move=({row},{col})  "
                f"AB={ab_t*1000:.2f} ms  MM={mm_t*1000:.2f} ms  "
                f"visited={ab_stats['nodes']}  pruned={ab_stats['pruned']}"
            )

        setMove(self.board, row, col, self.comp)
        self.update_buttons()
        self.animate_pop(self.btns[row][col])
        self.check_end()

    # ============================================================
    # HINT
    # ============================================================

    def show_hint(self, sender=None):
        if self.game_over:
            return

        empty = blanks(self.board)
        if not empty:
            return

        # clear previous hint
        if self.hint_active:
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == 0:
                        b = self.btns[i][j]
                        b.background_color = self.board_bg
                        b.border_color = self.board_border
                        b.border_width = 2

        if self.difficulty == "Easy":
            hx, hy = choice(empty)

        elif self.difficulty == "Medium":
            m = find_winning_move(self.board, self.human)
            if not m:
                m = find_winning_move(self.board, self.comp)
            if not m:
                m = pick_heuristic_move(self.board)
            if not m:
                m = choice(empty)
            hx, hy = m

        else:  # Hard
            hx, hy, _ = abminimax(self.board, len(empty), -inf, inf, self.human)
            if hx == -1:
                hx, hy = choice(empty)

        btn = self.btns[hx][hy]
        btn.background_color = "#fff3cd"
        btn.border_color = "#f39c12"
        btn.border_width = 3
        self.hint_active = True
        self.pulse(btn)

    # ============================================================
    # END CHECK
    # ============================================================

    def check_end(self):
        if winningPlayer(self.board, self.human):
            self.status_label.text = "You win!"
            self.game_over = True
            self.show_summary("You Won")
            return True

        if winningPlayer(self.board, self.comp):
            self.status_label.text = "AI wins!"
            self.game_over = True
            self.show_summary("AI Won")
            return True

        if boardFull(self.board):
            self.status_label.text = "Draw!"
            self.game_over = True
            self.show_summary("Draw")
            return True

        return False

    # ============================================================
    # ANIMATIONS
    # ============================================================

    def animate_pop(self, btn):
        x, y, w, h = btn.frame

        def shrink():
            btn.frame = (x + w * 0.1, y + h * 0.1, w * 0.8, h * 0.8)

        def expand():
            btn.frame = (x, y, w, h)

        ui.animate(shrink, 0.1, completion=lambda: ui.animate(expand, 0.12))

    def pulse(self, btn):
        def dim():
            btn.alpha = 0.4
        def bright():
            btn.alpha = 1.0
        ui.animate(dim, 0.15, completion=lambda: ui.animate(bright, 0.15))

    def start_thinking(self):
        self._thinking = True
        self._think_step = 0
        self._cycle()

    def _cycle(self):
        if not self._thinking:
            return
        dots = "." * (self._think_step % 4)
        self.status_label.text = "AI is thinking" + dots
        self._think_step += 1
        ui.delay(self._cycle, 0.3)

    def stop_thinking(self):
        self._thinking = False

    # ============================================================
    # SUMMARY POPUP WITH LOG  (ATTACHED TO SELF)
    # ============================================================

    def show_summary(self, title):
        # use this view as the "window"
        W, H = self.width, self.height

        overlay = ui.View(
            frame=self.bounds,
            background_color=(0, 0, 0, 0.45)
        )

        popup_w = W * 0.82
        popup_h = H * 0.60

        popup = ui.View(
            frame=(W/2 - popup_w/2, H/2 - popup_h/2, popup_w, popup_h),
            background_color="white",
            corner_radius=18,
            border_width=0,
            shadow_color="black",
            shadow_opacity=0.35,
            shadow_radius=12
        )

        # initial tiny scale for bounce
        popup.transform = ui.Transform.scale(0.01, 0.01)

        # Title
        lbl = ui.Label(
            text=title + " — Summary",
            alignment=ui.ALIGN_CENTER,
            font=("<System-Bold>", 17),
            text_color="#2c3e50"
        )
        lbl.frame = (0, 10, popup.width, 30)
        popup.add_subview(lbl)

        # Scroll area
        scroll = ui.ScrollView(
            frame=(10, 50, popup.width - 20, popup.height - 90),
            background_color="white",
            shows_vertical_scroll_indicator=True
        )

        lines = []
        if self.total_moves > 0:
            avg_mm = (self.total_minimax_time / self.total_moves) * 1000
            avg_ab = (self.total_alphabeta_time / self.total_moves) * 1000
            lines.append(f"Total moves (Hard): {self.total_moves}")
            lines.append(f"Total Minimax time: {self.total_minimax_time*1000:.2f} ms")
            lines.append(f"Total Alpha-Beta time: {self.total_alphabeta_time*1000:.2f} ms")
            lines.append(f"Avg Minimax per move: {avg_mm:.2f} ms")
            lines.append(f"Avg Alpha-Beta per move: {avg_ab:.2f} ms")
            lines.append("")
            lines.append("Move Logs:")
            lines.extend(self.move_logs)
        else:
            lines.append("No performance data (use Hard difficulty for logs).")

        txt = "\n".join(lines)

        txtview = ui.TextView(
            editable=False,
            selectable=True,
            text=txt,
            font=("<System>", 14),
            text_color="#2c3e50",
            background_color="white"
        )
        txtview.size_to_fit()
        txtview.width = scroll.width
        scroll.add_subview(txtview)
        scroll.content_size = (scroll.width, txtview.height + 20)

        popup.add_subview(scroll)

        # Close button
        close_btn = ui.Button(
            title="CLOSE",
            tint_color="white",
            background_color="#e74c3c",
            corner_radius=12
        )
        close_btn.frame = (popup.width/2 - 60, popup.height - 40, 120, 30)
        popup.add_subview(close_btn)

        # wire up close
        def close_action(sender):
            self.close_popup(overlay, popup)
        close_btn.action = close_action

        self.add_subview(overlay)
        self.add_subview(popup)

        # bounce animation
        def b1():
            popup.transform = ui.Transform.scale(1.15, 1.15)
        def b2():
            popup.transform = ui.Transform.scale(0.92, 0.92)
        def b3():
            popup.transform = ui.Transform.scale(1.0, 1.0)

        ui.animate(b1, 0.18,
                   completion=lambda: ui.animate(
                       b2, 0.15,
                       completion=lambda: ui.animate(b3, 0.15)
                   ))

    def close_popup(self, overlay, popup):
        def fade():
            overlay.alpha = 0
            popup.alpha = 0
            popup.transform = ui.Transform.scale(0.8, 0.8)

        def remove():
            self.remove_subview(popup)
            self.remove_subview(overlay)

        ui.animate(fade, 0.25, completion=lambda: remove())

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    v = TicTacToeView()
    v.present("sheet", animated=True)