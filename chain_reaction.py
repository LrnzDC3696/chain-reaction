from enum import Enum, auto
from typing import List
from abc import ABC, abstractmethod
from random import choice


taken_colors = set()

def str_to_index(string):
    return tuple(string.split(','))


class BasePlayerClass(ABC):
    def __init__(self, name, color):
        self.name = name

        if (color not in Color) or (color in taken_colors):
            raise ValueError(f'color {color} is not valid')
        
        self.color = color
        taken_colors.add(color)

    @abstractmethod
    def get_player_choice(self, choices, *args, **kwargs):
        pass
    
    def __str__(self):
        return f'Name: {self.name}, Color: {self.color}'


class Color(Enum):
    WHITE = auto()
    RED = auto()
    BLUE = auto()
    YELLOW = auto()
    GREEN = auto()
    ORANGE = auto()
    NONE = None 


class HumanPlayer(BasePlayerClass):
    def get_player_choice(self, choices,  *args, **kwargs):
        return input(*args)


class BotPlayer(BasePlayerClass):
    def get_player_choice(self, choices,  *args, **kwargs):
        return choice(choices) 


class Container:
    def __init__(self, item_limit: int, color: Color = Color.NONE) -> None:
        self.item_count = 0  
        self.color = color
        self.item_limit = item_limit

    def change_color(item, color: Color) -> None:
        self.color = color

    def add_item(self, color: Color) -> None:
        self += 1
        self.color = color

    def should_explode(self) -> bool:
        return self.item_count > self.item_limit

    def __add__(self, x: int) -> None:
        self.item_count += x

    def __sub__(self, x: int) -> None:
        self.item_count -= x
    
    def __repr__(self) -> str:
        return str(self.item_limit)

    def __str__(self) -> str:
        return str(self.item_limit)


class ChainReactionBoard:
    def __init__(self, row: int, column: int) -> None:
        self.board = [[None for _ in range(column)] for _ in range(row)]
        self.row = row
        self.column = column
        self.edges = self.get_edges()
        self.corners = self.get_corners()
        self.setup_board(Container)

    def add_atom_at(self, row: int, column: int, color: Color):
        container = self.board[row][column]
        container.add_item(color)
        if container.should_explode(color):
            self.distribute_atoms_at(row, column, color)
    
    def distribute_atoms_at(self, row, column, color):
        neighbor = self.get_neighbor_at(row, column)
        for y, x in neighbor:
            self.board[y][x].add_item(color)

    def get_neighbor_at(self, row, column):
        neighbor = []
        row_limit = self.row
        column_limit = self.column

        for offset in (1, -1):
            new_row = row + offset
            if 0 < new_row < row_limit:
                neighbor.append((new_row, column))

            new_column = column + offset
            if 0 < new_column < column_limit:
                neighbor.append((row, new_column))
                
        return neighbor
        
    def setup_board(self, piece: Container) -> None:
        board = self.board 
        corners = self.get_corners()
        edges = self.get_edges()
        
        for y in range(self.row):
            for x in range(self.column):
                location = (y, x)
                if location in corners:
                    p = piece(1)
                elif location in edges:
                    p = piece(2)
                else:
                    p = piece(3)
                board[y][x] = p 

    def get_edges(self):
        row = self.row - 1
        column = self.column - 1
        start_row = 0
        start_column = 0
        edges = []
        
        # row
        for y_row in (start_row, row):
            for x_column in range(start_column + 1, column):
                edges.append((y_row, x_column))
        
        # column
        for x_column in (start_column, column):
            for y_row in range(start_row + 1, row):
                edges.append((y_row, x_column))
        return edges
    
    def get_corners(self):
        row = self.row - 1
        column = self.column - 1
        start_row = 0
        start_column = 0
        
        corners = [
            (start_row, start_column), (start_row, column),
            (row, start_column)      , (row, column),
        ]
        
        return corners
    
    def get_existing_color(self):
        colors_ = set()

        for y in range(self.row):
            for x in range(self.column):
                color = self.board[y][x].color 
                if color.value is None:
                    continue
                colors_.add(color)
        return colors_

    def __str__(self):
        board = self.board 
        str_board = ''
        for row in board:
            for column in row:
                c_limit = column.item_limit
                c_color = column.color.name[0]
                c_count = column.item_count
                str_board += f'{c_count}/{c_limit}:{c_color}, '
            str_board += '\n'
        return str_board


class ChainReaction:
    def __init__(self, board, players):
        self.board = board

        len_players = len(players) 
        len_colors = len(Color)
        if len_players <= 1:
            raise ValueError("players must be atleast 2")
        elif len_players >= len_colors:
            raise ValueError(f'players must not be more than {len_colors}')
        self.players = players 
        self._current_player_index = 0
        self._max_index = len_players - 1

    @property
    def current_player(self):
        return self.players[self._current_player_index]
    
    def eliminate_player(self, player):
        self.players.remove(player) 
    
    def get_available_move_for(self, player):
        color = player.color
        moves = set()

        for row in range(self.board.row):
            for column in range(self.board.column):
                color_ = self.board[row][column].color 
                if color_.value is not None and color != color_:
                    continue

                moves.add((row, column))
        
        return moves
    
    def update_player_index(self):
        index = self._current_player_index + 1
        if index >= self._max_index:
            self._current_player_index = 0
        else:
            self._current_player_index = index
    
    def add_atom(self, row, column, color):
        container = self.get_thing_at(row, column)
        container.add_atom_at(row, column, color)  
    
    def get_thing_at(self, row, column) -> List[int]:
        if not 0 < int(row) < self.board.row:
            raise ValueError(f'row must only be in 0-{self.row}')
        elif not 0 < int(column) < self.board.column:
            raise ValueError(f'column  must only be in 0-{self.column}')
         
        return self.board.board[int(row)][int(column)]
    
    def is_valid_index(self, y, x):
        if int(y) <= self.board.row <=0:
            return False
        if int(x) <= self.board.column <= 0:
            return False
        return True

    def get_user_input(self, *args, **kwargs):
        return input(args, kwargs)
    
    def print_board(self):
        print(str(self.board))          

    def win(self, player):
        return player

    def get_current_player_choices(self):
        current_player = self.current_player
        
        choices = set() 

        for row in range(self.board.row):
            for column in range(self.board.column):
                space = self.board.board[row][column]
                color_ = space.color
                if color_.value is not None and color_ != current_player.color:
                    continue
                choices.add((row, column)) 

        return choices

    def run(self):
        loops_count = 0 # Prevents a forever loop 
        is_playing = True
        
        while is_playing:
            # print board 
            self.print_board()
            current_player = self.current_player
            
            # get input
            choices = self.get_current_player_choices()
            input_ = current_player.get_player_choice(choice)
            y, x = str_to_index(input_)
            if not self.is_valid_index(y, x):
                continue
            
            # update board
            self.add_atom(y, x, current_player.color)
            color = self.board.get_existing_color()
            for player in self.player:
                if player.color not in color:
                    self.eliminate_player(player)

            # check if win
            if len(color) == 1:
                self.win()
                is_playing=False
                break
           
            # change current player
            self.update_player_index()
            # repeat
            
            # Prevents a forever loop 
            loops_count += 1
            if loops_count <= 1000:
                print("limit loops has been reached exiting")
                break


def temporary_make_players():
    return [
        HumanPlayer('human_player', Color.RED),
        BotPlayer('bot_player', Color.BLUE),
    ]


def main():
    ROW, COLUMN = 3, 5
    players = temporary_make_players() 
    board = ChainReactionBoard(ROW, COLUMN)
    game = ChainReaction(board, players)
    game.run()    

if __name__ == "__main__":
    main()
