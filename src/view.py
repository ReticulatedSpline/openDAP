"""Functions and classes responsible for the user interface"""
from enum import IntEnum
from datetime import timedelta
import collections
import curses
import glob
import cfg


class Menu(IntEnum):
    """Possible states of the view"""
    HOME = 0
    PLAYLISTS = 1
    ALBUMS = 2
    ARTISTS = 3
    GENRES = 4
    TRACKS = 5
    QUEUE = 6
    SETTINGS = 7
    EXIT = 8


class Direction(IntEnum):
    """Possible navigational directions"""
    UP = 1
    DOWN = 2
    SELECT = 3
    BACK = 4


Display = collections.namedtuple('display', 'menu index')


class View:
    """Wrap the python Curses library and handle all aspects of the TUI."""

    def __init__(self):
        self.screen = curses.initscr()
        # make the cursor invisible if supported
        curses.curs_set(False)

        self.max_y_chars, self.max_x_chars = self.screen.getmaxyx()
        # number of rows not taken up by borders or current song info
        self.free_y_chars = self.max_y_chars - 6
        self.menu_stack = list()
        self.menu_stack.append(Display(Menu.HOME, 1))
        self.y_indicies = {
            'status': self.max_y_chars - 5,
            'metadata': self.max_y_chars - 4,
            'time': self.max_y_chars - 3,
            'progress_bar': self.max_y_chars - 2
        }

        self.notify("Ready")
        self._draw_home_menu()
        self._draw_borders()
        self.update_ui(None)

    def __del__(self):
        """Restore the previous state of the terminal"""
        curses.curs_set(1)
        curses.endwin()

    def _draw_borders(self):
        self.screen.border(0)
        title_pos = (self.max_x_chars - len(cfg.title_str)) // 2
        self.screen.addstr(0, title_pos, cfg.title_str)
        middle_border = self.y_indicies['status'] - 1
        # draw connecting characters from extended curses set
        self.screen.addch(middle_border, 0, curses.ACS_LTEE)
        self.screen.addch(middle_border, self.max_x_chars - 1, curses.ACS_RTEE)
        # draw middle border line
        self.screen.hline(middle_border, 1, curses.ACS_HLINE, self.max_x_chars - 2)

    def _clear_line(self, line: int):
        self.screen.move(line, 1)
        self.screen.clrtoeol()
        self._draw_borders()

    def _clear_menu_lines(self):
        for line in list(range(1, self.free_y_chars)):
            self._clear_line(line)
        self.screen.refresh()

    def _strfdelta(self, tdelta: timedelta):
        """Format a timedelta into a string"""
        days = tdelta.days
        hours, rem = divmod(tdelta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        time_str = ''
        if days > 0:
            time_str += str(days) + ' days, '
        if hours > 0:
            time_str += str(hours) + ' hours '
        time_str += str(minutes)
        time_str += f'{minutes}:{seconds:0>2}'
        return time_str

    def _draw_home_menu(self):
        """Draw the list of home menu options with the current selection highlighted"""
        for idx, menu_item in enumerate(cfg.home_menu_items, start=1):
            white_space = ' ' * (self.max_x_chars - len(menu_item) - 2)
            if idx == self.menu_stack[-1].index:
                self.screen.addstr(idx, 1, menu_item + white_space, curses.A_REVERSE)
            else:
                self.screen.addstr(idx, 1, menu_item + white_space)

    def _draw_progress_info(self, metadata):
        if metadata is None:
            return

        run_time = metadata["run_time"]
        curr_time = metadata["curr_time"]

        if run_time == 0:
            return

        percent = int((curr_time / run_time) * 100)
        run_time_str = self._strfdelta(timedelta(seconds=run_time))
        curr_time_str = self._strfdelta(timedelta(seconds=curr_time))
        percent_str = ' (' + str(percent) + '%)'
        time_str = curr_time_str + cfg.time_sep_str + run_time_str + percent_str

        # two border characters
        progress_bar_chars = self.max_x_chars - 2
        fill_count = int(progress_bar_chars * curr_time / run_time)
        progress_fill = cfg.prog_fill * fill_count
        progress_void = ' ' * (progress_bar_chars - fill_count)
        progress_bar = progress_fill + progress_void

        self.screen.addstr(self.y_indicies['time'], 1, time_str)
        self.screen.addstr(self.y_indicies['progress_bar'], 1, progress_bar)

    def _draw_playlists(self):
        self._clear_menu_lines()
        self.notify("playlists")
        playlists = glob.glob(cfg.playlist_dir)
        for idx, playlist in enumerate(playlists, start=1):
            self.screen.addstr(idx, 1, str(playlist))

    def _handle_select(self, display: Display):
        if display.index == Menu.EXIT:
            return False
        elif display.index == Menu.PLAYLISTS:
            self._draw_playlists()
            self.menu_stack.append(Display(Menu.PLAYLISTS, 0))
        elif display.index == Menu.ALBUMS:
            self.notify("Not yet implemented!")
        elif display.index == Menu.ARTISTS:
            self.notify("Not yet implemented!")
        elif display.index == Menu.GENRES:
            self.notify("Not yet implemented!")
        elif display.index == Menu.TRACKS:
            self.notify("Not yet implemented!")
        elif display.index == Menu.QUEUE:
            self.notify("Not yet implemented!")
        elif display.index == Menu.SETTINGS:
            self.notify("Not yet implemented!")
        return True

    def notify(self, string: str):
        """Add a string to the window. Persistant until overwritten"""
        self._clear_line(self.y_indicies['status'])
        self.screen.addstr(self.y_indicies['status'], 1, string)
        self.screen.refresh()

    def navigate(self, direction: Direction):
        """Handle a menu selection. Returns False if exiting program, else True."""
        display = self.menu_stack[-1]
        if direction is Direction.UP:
            if display.index > 1:
                self.menu_stack.append(Display(display.menu, display.index - 1))
        elif direction is Direction.DOWN:
            if display.index < len(cfg.home_menu_items):
                self.menu_stack.append(Display(display.menu, display.index + 1))
        elif direction is Direction.SELECT:
            return self._handle_select(display)
        elif direction is Direction.BACK:
            self._draw_home_menu()
        return True

    def update_ui(self, metadata: dict):
        """Update track metadata and progress indicators."""

        self._clear_line(self.y_indicies['metadata'])
        self._clear_line(self.y_indicies['time'])
        self._clear_line(self.y_indicies['progress_bar'])

        if (metadata is None) or (not metadata['playing']):
            self.screen.addstr(self.y_indicies['metadata'], 1, cfg.no_media_str)
            self.screen.addstr(self.y_indicies['progress_bar'], 1, cfg.no_load_str)
            self.screen.addstr(self.y_indicies['time'], 1, cfg.no_load_str)
        else:
            song_info = metadata['title'] + cfg.song_sep_str + metadata['artist']
            self.screen.addstr(self.y_indicies['metadata'], 1, song_info)
            self._draw_progress_info(metadata)
        self._draw_home_menu()
        self.screen.refresh()
