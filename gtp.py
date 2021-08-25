# -*- coding: utf-8 -*-

from sys import stderr, stdout, stdin
from board import Board, PASS, RESIGN, BLACK, WHITE, INVLD
from network import Network
from mcts import Search
from config import BOARD_SIZE, KOMI, INPUT_CHANNELS, PAST_MOVES
from time_control import TimeControl

class GTP_ENGINE:
    def __init__(self, args):
        self.args = args
        self.board = Board(BOARD_SIZE, KOMI)
        self.network = Network(BOARD_SIZE)
        self.time_control = TimeControl()
        self.network.trainable(False)
        self.board_history = [self.board.copy()]

        if self.args.weights != None:
            self.network.load_pt(self.args.weights)

    def clear_board(self):
        self.board.reset(self.board.board_size, self.board.komi)
        self.board_history = [self.board.copy()]

    def genmove(self, color):
        # Genrate next move and play it.
        c = self.board.to_move
        if color == "black" or color == "b"  or color == "B":
            c = BLACK
        elif color == "white" or color == "w" or color == "W":
            c = WHITE

        self.board.to_move = c
        search = Search(self.board, self.network, self.time_control)
        move = search.think(self.args.playouts, self.args.verbose)
        self.board.play(move)

        return self.board.vertex_to_text(move)
        

    def play(self, color, move):
        c = INVLD
        if color == "black" or color == "b"  or color == "B":
            c = BLACK
        elif color == "white" or color == "w" or color == "W":
            c = WHITE

        x = ord(move[0]) - (ord('A') if ord(move[0]) < ord('a') else ord('a'))
        y = int(move[1:]) - 1
        if x >= 8:
            x -= 1
        if c != INVLD:
            self.board.to_move = c
            if self.board.play(self.board.get_vertex(x,y)):
                self.board_history.append(self.board.copy())
                return True
        return False

    def undo(self):
        if len(self.board_history) > 1:
            self.board_history.pop()
            self.board = self.board_history[-1].copy()

    def boardsize(self, bsize):
        self.board.reset(bsize, self.board.komi)
        self.board_history = [self.board.copy()]

    def komi(self, k):
        self.board.komi = k

    def time_settings(self, main_time, byo_time, byo_stones):
        self.time_control.time_settings(int(main_time), int(byo_time), int(byo_stones))

    def time_left(self, color, time, stones):
        c = INVLD
        if color == "black" or color == "b"  or color == "B":
            c = BLACK
        elif color == "white" or color == "w" or color == "W":
            c = WHITE
        if c == INVLD:
            return False
        self.time_control.time_left(c, int(time), int(stones))
        return True

    def showboard(self):
        return self.board.showboard()

class GTP_LOOP:
    COMMANDS_LIST = {
        "quit", "name", "version", "protocol_version", "list_commands",
        "play", "genmove", "undo", "clear_board", "boardsize", "komi",
        "time_settings", "time_left"
    }
    def __init__(self, args):
        self.engine = GTP_ENGINE(args)
        self.loop()
        
    def loop(self):
        while True:
            cmd = stdin.readline().split()
            if len(cmd) == 0:
                continue

            main = cmd[0]
            if main == "quit":
                self.success_print("")
                break
            self.process(cmd)

    def process(self, cmd):
        main = cmd[0]
        
        if main == "name":
            self.success_print("dlgo")
        elif main == "version":
            self.success_print("alpha")
        elif main == "protocol_version":
            self.success_print("2")
        elif main == "list_commands":
            clist = str()
            for c in self.COMMANDS_LIST:
                clist += (c + "\n")
            self.success_print(clist)
        elif main == "clear_board":
            # reset the board
            self.engine.clear_board();
            self.success_print("")
        elif main == "play" and len(cmd) >= 3:
            # play color move
            if self.engine.play(cmd[1], cmd[2]):
                self.success_print("")
            else:
                self.fail_print("")
        elif main == "undo":
            # undo move
            self.engine.undo();
            self.success_print("")
        elif main == "genmove" and len(cmd) >= 2:
            # genrate next move
            self.success_print(self.engine.genmove(cmd[1]))
        elif main == "boardsize" and len(cmd) >= 2:
            # set board size and reset the board
            self.engine.boardsize(int(cmd[1]))
            self.success_print("")
        elif main == "komi" and len(cmd) >= 2:
            # set komi
            self.engine.komi(float(cmd[1]))
            self.success_print("")
        elif main == "showboard":
            # display the board
            stderr.write(self.engine.showboard())
            stderr.flush()
            self.success_print("")
        elif main == "time_settings":
            self.engine.time_settings(cmd[1], cmd[2], cmd[3])
            self.success_print("")
        elif main == "time_left":
            if self.engine.time_left(cmd[1], cmd[2], cmd[3]):
                self.success_print("")
            else:
                self.fail_print("")
        else:
            self.fail_print("Unknown command")
            
    def success_print(self, res):
        stdout.write("= {}\n\n".format(res))
        stdout.flush()

    def fail_print(self, res):
        stdout.write("? {}\n\n".format(res))
        stdout.flush()
