#todo
# work on the colour schemes
# implement a function to update colour along with number

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import Horizontal
from textual.screen import Screen
from textual.css.query import DOMQuery
from textual.widget import Widget
from textual.widgets import Digits, Footer, Label, Markdown

from pathlib import Path
from os import sep
from random import randint, choice
from pickle import dump, load

scr_fl_path = Path(str(Path(__file__).absolute().parent)+sep+"scr")
md_fl_path = Path(str(Path(__file__).absolute().parent)+sep+"2048.md")
def not_found():
    raise FileNotFoundError(f"File {md_fl_path} not found, make sure to clone the entire repository")

if scr_fl_path.exists():
    with open(scr_fl_path, 'rb') as scrfl:
        HIGH_SCORE = load(scrfl)
else:
    HIGH_SCORE = 0



class Help(Screen):

    BINDINGS = [("escape,space,q,question_mark", "pop_screen", "Close")]

    def compose(self) -> ComposeResult:
        yield Markdown(md_fl_path.read_text() if md_fl_path.exists() else not_found())



class GameOver(Label):

    def show(self, win:bool, score:int, high_score:int) -> None:
        if win:
            self.update(
                "W I N N E R!\n\n\n"
                f"You won with a score of {score} "
                + (
                    f"You were {high_score - score} points away from beating your high score!"
                    if high_score > score
                    else f"You beat your high score by {score - high_score}!"
                )
            )
            if score > high_score:
                with open(scr_fl_path, 'wb') as scrfl:
                    high_score = dump(score, scrfl)
                global HIGH_SCORE
                HIGH_SCORE = score
            self.add_class("visible")

        else:
            self.update(
                "Uh oh it seems like you ran out of space :(\n\n\n"
                f"Score: {score}"
            )

            self.add_class("visible")

    def hide(self) -> None:
        self.remove_class("visible")



class GameHeader(Widget):

    score = reactive(0)
    high_score = reactive(HIGH_SCORE)

    def compose(self):
        with Horizontal():
            yield Label(self.app.title, id = "app-title")
            yield Label(id = "score")
            yield Label(id = "high_score")

    def watch_score(self, score:int):
        self.query_one("#score", Label).update(f"Score: {score}")

    def watch_high_score(self, high_score:int):
        self.query_one("#high_score", Label).update(f"High Score: {high_score}")


class Cell(Digits):
    def __init__(self, x, y):
        super().__init__("", id = f"cell-{x}-{y}")

    def get_val(self):
        return int(self.value) if self.value else 0


class GameGrid(Widget):
    def compose(self) -> ComposeResult:
        for x in range(4):
            for y in range(4):
                yield Cell(x, y)



class Game(Screen):

    BINDINGS = [
        Binding("question_mark,F1", "push_screen('help')", "Help", key_display="?"),
        Binding("r", "reset", "Reset board"),
        Binding("up,w", "move('up')", "Move up"),
        Binding("down,s", "move('down')", "Move down"),
        Binding("left,a", "move('left')", "Move left"),
        Binding("right,d", "move('right')", "Move right"),
        Binding("q", "quit", "Quit")
    ]



    def compose(self) -> ComposeResult:
        yield GameHeader()
        yield GameGrid()
        yield Footer()
        yield GameOver()

    def action_reset(self) -> None:
        for x in range(4):
            for y in range(4):
                self.query_one(f"#cell-{x}-{y}", Cell).update("")
        self.query_one(GameOver).hide()
        self.query_one(GameHeader).score = 0
        self.query_one(GameHeader).high_score = HIGH_SCORE
        self.query_one(f"#cell-{randint(0, 3)}-{randint(0, 3)}", Cell).update("2")



    def cell(self, x, y):
        return self.query_one(f"#cell-{x}-{y}", Cell)


    def action_move(self, direction:str) -> None:
        _grid = [[self.query_one(f"#cell-{x}-{y}", Cell) for y in range(4)] for x in range(4)]
        scr = []

        if direction == "up":
            grid = _grid

        elif direction == "down":
            grid = _grid[::-1]

        elif direction == "right":
            grid = [[_grid[x][y] for x in range(4)] for y in range(3, -1, -1)]

        elif direction == "left":
            grid = [[_grid[x][y] for x in range(4)] for y in range(4)]

        del _grid


        for x in range(1, 4):
            for y in range(4):
                for z in range(1, 5-x):
                    if not grid[x-1][y].value:
                        grid[x-1][y].update(grid[x][y].value)
                        if x+z < 4:
                            grid[x][y].update(grid[x+z][y].value)
                            grid[x+z][y].update("")
                        else:
                            grid[x][y].update("")

        while any(
            grid[x][y].get_val() and grid[x][y].get_val() == grid[x-1][y].get_val() for x in range(1, 4) for y in range(4)
        ):
            for x in range(1, 4):
                for y in range(4):
                    if grid[x][y].get_val() and grid[x-1][y].get_val() == grid[x][y].get_val():
                        scr.append(grid[x][y].get_val()*2)
                        grid[x-1][y].update(str(scr[-1]))
                        grid[x][y].update("")
                        for z in range(x, 3):
                            grid[z][y].update(grid[z+1][y].value)
                        grid[3][y].update("")

        self.query_one(GameHeader).score += sum(scr)


        if self.query_one(GameHeader).score >= self.query_one(GameHeader).high_score:
            self.query_one(GameHeader).high_score = self.query_one(GameHeader).score

        empty_sqrs = [
            (x, y) for x in range(4) for y in range(4) if not self.query_one(f"#cell-{x}-{y}").value
            ]

        if empty_sqrs:
            randx, randy = choice(empty_sqrs)
            self.query_one(f"#cell-{randx}-{randy}", Cell).update("2")

        else:
            self.query_one(GameOver).show(
                win = False, score = self.query_one(GameHeader).score, high_score = HIGH_SCORE
                )
            self.query_one(GameGrid).disabled = True
            return


        for x in range(4):
            for y in range(4):
                if self.query_one(f"#cell-{x}-{y}", Cell).get_val() >= 2048:
                    self.query_one(GameOver).show(
                        win = True, score = self.query_one(GameHeader).score, high_score = HIGH_SCORE
                        )
                    self.query_one(GameGrid).disabled = True
                    return


    def on_mount(self) -> None:
        self.action_reset()


class Board(App[None]):

    CSS_PATH = "./2048.tcss"

    SCREENS = {"help": Help}

    TITLE = "A bad implementation of 2048"

    def on_mount(self) -> None:
        self.push_screen(Game())



if __name__ == "__main__":
    Board().run()