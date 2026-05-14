from models.player import Player
from models.team import Team
from rl_api.websocket_client import RLWebsocketClient
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

import os

def rank_style(rank: str | None) -> str:
    if not rank:
        return "white"

    rank = rank.lower()

    if "supersonic" in rank:
        return "bold bright_magenta"
    if "grand champion" in rank:
        return "bold magenta"
    if "champion" in rank:
        return "bold purple"
    if "diamond" in rank:
        return "bold cyan"
    if "platinum" in rank:
        return "bold blue"
    if "gold" in rank:
        return "bold yellow"
    if "silver" in rank:
        return "white"
    if "bronze" in rank:
        return "red"

    return "white"

def clear_terminal() -> None:
    os.system("cls" if os.name == "nt" else "clear")

class Game:
    def __init__(self) -> None:
        self.teams: dict[int, Team] = {}
        self.client: RLWebsocketClient = RLWebsocketClient()
        self.roster: tuple[Player, ...] = ()
        self.mode: str | None = None

    def _build_teams(self) -> None:
        self.teams.clear()

        is_freeplay = self.get_mode() == "freeplay"

        for player in self.roster:
            team_num = 0 if is_freeplay else player.team_num
            team = self.teams.setdefault(team_num, Team())
            team.players.append(player)


    def get_mode(self) -> None:
        self.mode = {
            1: "freeplay",
            2: "1v1",
            4: "2v2",
            6: "3v3",
            8: "4v4",
        }.get(len(self.roster), "unknown")

    def query_tracker(self) -> None:
        for team in self.teams.values():
            for player in team.players:
                if not player.is_trackable:
                    continue

                try:
                    player.extract_ranked(self.mode)
                except Exception as exc:
                    player.error = str(exc)

    def update_from_roster(self) -> None:
        self._build_teams()
        self.query_tracker()

    def run(self) -> None:
        for roster in self.client.yield_roster():
            self.roster = roster
            self.get_mode()
            self.update_from_roster()
            self.print_lobby()

    def _add_player_mode_to_table(self, table: Table, player: Player, mode: str) -> None:
        rating = player.ratings.get(mode, {})

        mmr = rating.get("mmr", "N/A")
        rank = rating.get("rank", "N/A")
        division = rating.get("division", "")

        platform = player.platform or "N/A"

        if player.error and not rating:
            table.add_row(
                player.name,
                platform,
                "[bold red]ERROR[/bold red]",
                f"[red]{player.error}[/red]",
                "N/A",
            )
            return

        table.add_row(
            player.name,
            platform,
            f"[{rank_style(rank)}]{rank}[/{rank_style(rank)}]",
            division,
            str(mmr),
        )

    def _add_player_all_modes_to_table(self, table: Table, player: Player) -> None:
        platform = player.platform or "N/A"

        if player.error and not player.ratings:
            table.add_row(
                player.name,
                platform,
                "N/A",
                "[bold red]ERROR[/bold red]",
                f"[red]{player.error}[/red]",
                "N/A",
            )
            return

        if not player.ratings:
            table.add_row(
                player.name,
                platform,
                "N/A",
                "No data",
                "",
                "N/A",
            )
            return

        first_line = True

        for mode in ("1v1", "2v2", "3v3", "4v4"):
            rating = player.ratings.get(mode)

            if rating is None:
                continue

            mmr = rating.get("mmr", "N/A")
            rank = rating.get("rank", "N/A")
            division = rating.get("division", "")

            name = player.name if first_line else ""
            first_line = False

            table.add_row(
                name,
                platform,
                mode,
                f"[{rank_style(rank)}]{rank}[/{rank_style(rank)}]",
                division,
                str(mmr),
            )

    def print_lobby(self) -> None:
        console.clear()

        mode = self.mode or "unknown"

        title = (
            f"[bold cyan]Rocket League Lobby MMR Tracker[/bold cyan]\n"
            f"[white]Mode:[/white] [bold yellow]{mode}[/bold yellow]"
        )

        console.print(
            Panel(
                title,
                border_style="cyan",
                box=box.ROUNDED,
            )
        )

        for team_num, team in sorted(self.teams.items()):
            team_color = "blue" if team_num == 0 else "orange3"
            team_name = "Blue Team" if team_num == 0 else "Orange Team"

            if mode == "freeplay":
                table = Table(
                    title=f"[bold {team_color}]{team_name}[/bold {team_color}]",
                    box=box.ROUNDED,
                    border_style=team_color,
                    header_style="bold white",
                )

                table.add_column("Player", style="bold white")
                table.add_column("Platform", style="dim")
                table.add_column("Mode", style="yellow")
                table.add_column("Rank")
                table.add_column("Division")
                table.add_column("MMR", justify="right", style="bold green")

                for player in team.players:
                    self._add_player_all_modes_to_table(table, player)

            else:
                table = Table(
                    title=f"[bold {team_color}]{team_name}[/bold {team_color}]",
                    box=box.ROUNDED,
                    border_style=team_color,
                    header_style="bold white",
                )

                table.add_column("Player", style="bold white")
                table.add_column("Platform", style="dim")
                table.add_column("Rank")
                table.add_column("Division")
                table.add_column("MMR", justify="right", style="bold green")

                for player in team.players:
                    self._add_player_mode_to_table(table, player, mode)

            console.print(table)
            console.print()


if __name__ == "__main__":
    game = Game()
    game.run()
