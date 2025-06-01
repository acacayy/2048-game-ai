import tkinter as tk
import random
import numpy as np # type: ignore

GRID_LEN = 4
CELL_SIZE = 100
CELL_PADDING = 10

class Game2048:
    def __init__(self, root):
        self.root = root
        self.root.title("2048 - Manual, Bantuan AI, & Full AI")
        self.board = np.zeros((GRID_LEN, GRID_LEN), dtype=int)
        self.mode = None

        self.top_frame = tk.Frame(root)
        self.top_frame.pack()
        self.manual_btn = tk.Button(self.top_frame, text="Main Manual", command=self.start_manual)
        self.manual_btn.pack(side=tk.LEFT, padx=5)
        self.ai_help_btn = tk.Button(self.top_frame, text="Bantuan AI", command=self.start_ai_help)
        self.ai_help_btn.pack(side=tk.LEFT, padx=5)
        self.ai_btn = tk.Button(self.top_frame, text="Main AI", command=self.start_ai)
        self.ai_btn.pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(root, width=GRID_LEN * CELL_SIZE, height=GRID_LEN * CELL_SIZE)
        self.canvas.pack()
        self.root.bind("<Key>", self.on_key)

    def reset_game(self):
        self.board = np.zeros((GRID_LEN, GRID_LEN), dtype=int)
        self.add_tile()
        self.add_tile()
        self.update_gui()

    def start_manual(self):
        self.mode = 'manual'
        self.reset_game()

    def start_ai_help(self):
        self.mode = 'ai_help'
        self.reset_game()

    def start_ai(self):
        self.mode = 'ai'
        self.reset_game()
        self.root.after(500, self.run_ai)

    def add_tile(self):
        empty = list(zip(*np.where(self.board == 0)))
        if empty:
            y, x = random.choice(empty)
            self.board[y][x] = 4 if random.random() < 0.1 else 2

    def move_left(self, board):
        new_board = np.zeros_like(board)
        for i in range(GRID_LEN):
            row = board[i][board[i] != 0]
            new_row = []
            skip = False
            for j in range(len(row)):
                if skip:
                    skip = False
                    continue
                if j + 1 < len(row) and row[j] == row[j + 1]:
                    new_row.append(row[j] * 2)
                    skip = True
                else:
                    new_row.append(row[j])
            new_board[i, :len(new_row)] = new_row
        return new_board

    def move(self, direction):
        if direction == 'left':
            return self.move_left(self.board)
        elif direction == 'right':
            return np.fliplr(self.move_left(np.fliplr(self.board)))
        elif direction == 'up':
            return np.rot90(self.move_left(np.rot90(self.board, -1)))
        elif direction == 'down':
            return np.rot90(self.move_left(np.rot90(self.board, 1)), -1)
        return self.board

    def move_in_direction(self, board, direction):
        original_board = self.board
        self.board = board.copy()
        moved = self.move(direction)
        self.board = original_board
        return moved

    def on_key(self, event):
        key = event.keysym
        direction_map = {'Left': 'left', 'Right': 'right', 'Up': 'up', 'Down': 'down'}
        if key in direction_map:
            direction = direction_map[key]
            if self.mode == 'manual':
                new_board = self.move(direction)
                if not np.array_equal(self.board, new_board):
                    self.board = new_board
                    self.add_tile()
                    self.update_gui()
                    if self.is_game_over():
                        self.canvas.create_text(200, 200, text="Game Over", font=("Helvetica", 36), fill="red")
            elif self.mode == 'ai_help':
                best_dir = self.expectimax_move(self.board, depth=3)
                if best_dir:
                    self.board = self.move(best_dir)
                    self.add_tile()
                    self.update_gui()
                    if self.is_game_over_custom(self.board):
                        self.canvas.create_text(200, 200, text="Game Over", font=("Helvetica", 36), fill="red")

    def run_ai(self):
        if self.board.max() >= 2048:
            self.canvas.create_text(200, 200, text="You Win!", font=("Helvetica", 36), fill="green")
            return
        if self.mode != 'ai':
            return

        best_move = self.expectimax_move(self.board, depth=3)
        if best_move:
            self.board = self.move(best_move)
            self.add_tile()
            self.update_gui()
        self.root.after(100, self.run_ai)

    def expectimax_move(self, board, depth):
        best_score = float('-inf')
        best_direction = None
        for direction in ['left', 'right', 'up', 'down']:
            new_board = self.move_in_direction(board, direction)
            if np.array_equal(board, new_board):
                continue
            score = self.expectimax(new_board, depth - 1, False)
            if score > best_score:
                best_score = score
                best_direction = direction
        return best_direction

    def expectimax(self, board, depth, is_ai_turn):
        if depth == 0 or self.is_game_over_custom(board):
            return self.evaluate(board)

        if is_ai_turn:
            max_score = float('-inf')
            for direction in ['left', 'right', 'up', 'down']:
                new_board = self.move_in_direction(board, direction)
                if np.array_equal(board, new_board):
                    continue
                score = self.expectimax(new_board, depth - 1, False)
                max_score = max(max_score, score)
            return max_score
        else:
            empty = list(zip(*np.where(board == 0)))
            if not empty:
                return self.evaluate(board)
            scores = []
            for y, x in empty:
                for val, p in [(2, 0.9), (4, 0.1)]:
                    board_copy = board.copy()
                    board_copy[y][x] = val
                    score = self.expectimax(board_copy, depth - 1, True)
                    scores.append(score * p)
            return sum(scores) / len(scores)

    def evaluate(self, board):
        empty_tiles = np.sum(board == 0)
        max_tile = np.max(board)
        smoothness = -np.sum(np.abs(np.diff(board, axis=0))) - np.sum(np.abs(np.diff(board, axis=1)))
        return empty_tiles * 100 + max_tile + smoothness

    def is_game_over(self):
        return self.is_game_over_custom(self.board)

    def is_game_over_custom(self, board):
        if np.any(board == 0):
            return False
        for direction in ['left', 'right', 'up', 'down']:
            if not np.array_equal(board, self.move_in_direction(board, direction)):
                return False
        return True

    def get_color(self, value):
        colors = {
            0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8",
            8: "#f2b179", 16: "#f59563", 32: "#f67c5f",
            64: "#f65e3b", 128: "#edcf72", 256: "#edcc61",
            512: "#edc850", 1024: "#edc53f", 2048: "#edc22e",
        }
        return colors.get(value, "#3c3a32")

    def update_gui(self):
        self.canvas.delete("all")
        for i in range(GRID_LEN):
            for j in range(GRID_LEN):
                value = self.board[i][j]
                color = self.get_color(value)
                x0 = j * CELL_SIZE + CELL_PADDING
                y0 = i * CELL_SIZE + CELL_PADDING
                x1 = (j + 1) * CELL_SIZE - CELL_PADDING
                y1 = (i + 1) * CELL_SIZE - CELL_PADDING
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
                if value:
                    self.canvas.create_text((x0 + x1)//2, (y0 + y1)//2, text=str(value),
                                            font=("Helvetica", 24), fill="black")
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    game = Game2048(root)
    root.mainloop()
