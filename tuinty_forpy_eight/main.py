from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import Horizontal, Grid
from textual.screen import Screen, ModalScreen
from textual.css.query import DOMQuery
from textual.color import Color
from textual.widget import Widget
from textual.widgets import Digits, Footer, Label, Markdown, Button, Static


from pathlib import Path
from random import randint, choice, choices
from pickle import dump, load
from math import log2
from argparse import ArgumentParser

USERNAME = Path('~').home().__str__().split('/')[-1]
SCR_FL_PATH = Path(__file__).parent.joinpath(f"scr_{USERNAME}.pkl")
MD_FL_PATH = Path(__file__).parent.joinpath("2048.md")
SAVE_FILE_PATH = Path(__file__).parent.joinpath(f"save_{USERNAME}.pkl")


def not_found(path: Path):
    raise FileNotFoundError(
        f"File {path.__str__()} not found, make sure you have all the required files, if you don't, try reinstalling "
        "or grab them from the github repository")


if SCR_FL_PATH.exists():
    with open(SCR_FL_PATH, 'rb') as scrfl:
        HIGH_SCORE = load(scrfl)
else:
    HIGH_SCORE = 0

parser: ArgumentParser = ArgumentParser(prog='tuinty-forpy-eight',
                                        description='A tui implementation of the "2048" game')
parser.add_argument(
    '-bg', '--background', choices=range(256), nargs=3, default=(143, 0, 255), required=False, type=int
)

parser.add_argument(
    '-tl', '--tile', choices=range(256), nargs=3, default=(237, 115, 255), required=False, type=int
)

parser.add_argument(
    '-op', '--opacity', choices=[round(x * 0.01, 2) for x in range(101)], default=0.13, required=False, type=float
)

arguments = parser.parse_args()

BACKGROUND_RGB = arguments.background
OPACITY = arguments.opacity
TILE_RGB = arguments.tile


class Help(Screen):
    BINDINGS = [("escape,space,q,question_mark", "pop_screen", "Close")]

    def compose(self) -> ComposeResult:
        yield Markdown(MD_FL_PATH.read_text() if MD_FL_PATH.exists() else not_found(MD_FL_PATH))


class QuitScreen(ModalScreen):
    def __init__(self, grid: list[str, ...], score: int):
        super().__init__()
        self.grid = grid
        self.score = score

    def compose(self) -> ComposeResult:
        yield Grid(
            Static("Do you want to save current game state?", id="question"),
            Button("Save and Quit", variant="success", id="save"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.pop_screen()
            with open(SAVE_FILE_PATH, 'wb') as savefl:
                dump([[]], savefl)
                dump(0, savefl)
            self.app.exit()
        elif event.button.id == "cancel":
            self.app.pop_screen()
        else:
            self.app.pop_screen()
            with open(SAVE_FILE_PATH, 'wb') as savefl:
                dump(self.grid, savefl)
                dump(self.score, savefl)
            self.app.exit()


class GameOver(Label):

    def show(self, score: int, high_score: int) -> None:
        self.update(
            f"Uh oh it seems like you ran out of space :(\n\n\nScore: {score}  High Score: {high_score}"
        )
        if score > high_score:
            with open(SCR_FL_PATH, 'wb') as scrfl:
                dump(score, scrfl)
            global HIGH_SCORE
            HIGH_SCORE = score
        self.add_class("visible")

    def hide(self) -> None:
        self.remove_class("visible")


class GameHeader(Widget):
    global HIGH_SCORE
    score = reactive(0)
    high_score = reactive(HIGH_SCORE)

    def compose(self):
        with Horizontal():
            yield Label(self.app.title, id="app-title")
            yield Label(id="score")
            yield Label(id="high_score")

    def watch_score(self, score: int):
        self.query_one("#score", Label).update(f"Score: {score}")

    def watch_high_score(self, high_score: int):
        self.query_one("#high_score", Label).update(f"High Score: {high_score}")


class Cell(Digits):
    def update_with_colour(self, value: str):
        opacity: float = ((log2(int(value) if value else 1)) % 10) * 0.05
        self.update(value)
        self.styles.background = Color(TILE_RGB[0], TILE_RGB[1], TILE_RGB[2], opacity)

    def __init__(self, x, y):
        super().__init__("", id=f"cell-{x}-{y}")
        self.update_with_colour("")

    def get_val(self):
        return int(self.value) if self.value else 0


class GameGrid(Widget):
    def __init__(self):
        super().__init__()
        self.styles.background = Color(BACKGROUND_RGB[0], BACKGROUND_RGB[1], BACKGROUND_RGB[2], OPACITY)

    def compose(self) -> ComposeResult:
        for x in range(4):
            for y in range(4):
                yield Cell(x, y)


class Game(Screen):
    BINDINGS = [
        Binding("question_mark,f1", "push_screen('help')", "Help", key_display="?"),
        Binding("r", "reset", "Reset board"),
        Binding("up,w", "move('up')", "Move up"),
        Binding("down,s", "move('down')", "Move down"),
        Binding("left,a", "move('left')", "Move left"),
        Binding("right,d", "move('right')", "Move right")
    ]

    def __init__(self):
        super().__init__()
        self.disabled = True

    def compose(self) -> ComposeResult:
        yield GameHeader()
        yield GameGrid()
        yield Footer()
        yield GameOver()

    def action_reset(self) -> None:
        for x in range(4):
            for y in range(4):
                self.query_one(f"#cell-{x}-{y}", Cell).update_with_colour("")
        self.query_one(GameOver).hide()
        self.query_one(GameHeader).score = 0
        global HIGH_SCORE
        self.query_one(GameHeader).high_score = HIGH_SCORE
        self.query_one(f"#cell-{randint(0, 3)}-{randint(0, 3)}", Cell).update_with_colour("2")
        self.disabled = False

    def cell(self, x, y):
        return self.query_one(f"#cell-{x}-{y}", Cell)

    def action_move(self, direction: str) -> None:

        if self.disabled:
            return

        _grid = [[self.query_one(f"#cell-{x}-{y}", Cell) for y in range(4)] for x in range(4)]
        _grid_vals = [[y.get_val() for y in x] for x in _grid]
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
                for z in range(1, 5 - x):
                    if not grid[x - 1][y].value:
                        grid[x - 1][y].update_with_colour(grid[x][y].value)
                        if x + z < 4:
                            grid[x][y].update_with_colour(grid[x + z][y].value)
                            grid[x + z][y].update_with_colour("")
                        else:
                            grid[x][y].update_with_colour("")

        while any(
                grid[x][y].get_val() and grid[x][y].get_val() == grid[x - 1][y].get_val() for x in range(1, 4) for y in
                range(4)
        ):
            for x in range(1, 4):
                for y in range(4):
                    if grid[x][y].get_val() and grid[x - 1][y].get_val() == grid[x][y].get_val():
                        scr.append(grid[x][y].get_val() * 2)
                        grid[x - 1][y].update_with_colour(str(scr[-1]))
                        grid[x][y].update_with_colour("")
                        for z in range(x, 3):
                            grid[z][y].update_with_colour(grid[z + 1][y].value)
                        grid[3][y].update_with_colour("")

        self.query_one(GameHeader).score += sum(scr)

        if self.query_one(GameHeader).score >= self.query_one(GameHeader).high_score:
            self.query_one(GameHeader).high_score = self.query_one(GameHeader).score

        empty_sqrs = [
            (x, y) for x in range(4) for y in range(4) if not self.query_one(f"#cell-{x}-{y}", Cell).value
        ]

        if empty_sqrs and _grid_vals != [[self.query_one(f"#cell-{x}-{y}", Cell).get_val() for y in range(4)] for x in
                                         range(4)]:
            randx, randy = choice(empty_sqrs)
            empty_sqrs.remove((randx, randy))
            self.query_one(f"#cell-{randx}-{randy}", Cell).update_with_colour(
                choices(("2", "4"), cum_weights=(90, 100))[0]
            )

        check = [grid[x][y].get_val() != grid[x - 1][y].get_val() for x in range(1, 4) for y in range(4)]
        grid = [[grid[x][y] for x in range(4)] for y in range(4)]
        check.extend([grid[x][y].get_val() != grid[x - 1][y].get_val() for x in range(1, 4) for y in range(4)])
        if not empty_sqrs and all(check):
            self.disabled = True
            global HIGH_SCORE
            self.query_one(GameOver).show(
                score=self.query_one(GameHeader).score, high_score=HIGH_SCORE
            )

    def on_mount(self) -> None:
        self.action_reset()
        if SAVE_FILE_PATH.exists():
            with open(SAVE_FILE_PATH, 'rb+') as savefl:
                grid = load(savefl)
                if grid[0]:
                    for x in range(4):
                        for y in range(4):
                            self.query_one(f"#cell-{x}-{y}", Cell).update_with_colour(grid[x][y])
                score = load(savefl)
                self.query_one(GameHeader).score = score
                self.query_one(GameHeader).high_score = score if score > HIGH_SCORE else HIGH_SCORE
                savefl.truncate()


class Board(App[None]):
    _CSS_PATH = Path(__file__).parent.joinpath("2048.tcss")

    if not _CSS_PATH.exists():
        not_found(_CSS_PATH)

    CSS_PATH = _CSS_PATH

    SCREENS = {"help": Help}

    TITLE = "A bad implementation of 2048"

    BINDINGS = [Binding("q", "save", "Quit")]

    def on_mount(self) -> None:
        self.push_screen(Game())

    def action_save(self):
        self.push_screen(
            QuitScreen(
                [[self.query_one(f"#cell-{x}-{y}", Cell).value for y in range(4)] for x in range(4)],
                self.query_one(GameHeader).score
            )
        )


def main():
    Board().run()


if __name__ == "__main__":
    main()
