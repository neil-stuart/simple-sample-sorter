import curses
import main


NAME = "SIMP-SAMP-SORT"

EMPT_LINE = "".join([(" ") for i in range(main.WIDTH-1)])

KEY_NAMES = {258: "DOWN", 259: "UP", 260: "LEFT", 261: "RIGHT"}


class pane():
    def __init__(self, h, w, off_y):
        try:
            self._window = curses.newwin(h, w, off_y, 0)
        except curses.error as e:
            print(f"Error creating new window: {e}")
        self.quit = False

    def _refresh(self):
        self._window.refresh()

    def _clrline(self, line_number):
        self._window.addstr(line_number, 0, EMPT_LINE)

    def _clr_all(self):
        for i in range(self._window.getmaxyx()[0]):
            self._clrline(i)


class header_pane(pane):
    def __init__(self, h, w, off_y):
        pane.__init__(self, h, w, off_y)
        self._window.addstr(0, 0, NAME, curses.A_REVERSE)
        self._title = ''
        self._window.refresh()
        self._char = 0
        self._max_x = self._window.getmaxyx()[1]
    @property
    def char(self):
        return self._char

    @char.setter
    def char(self, char):
        self._clrline(0)
        if char != -1:
            if char in KEY_NAMES:
                self._window.addstr(
                    0, 0, NAME+"    {} - {}".format(KEY_NAMES[char], int(char)), curses.A_REVERSE)
            else:
                self._window.addstr(
                    0, 0, NAME+"    {} - {}".format(str.upper(chr(char)), int(char)), curses.A_REVERSE)
        self._refresh()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._clrline(1)
        self._window.addstr(1, 0, title[:self._max_x-1], curses.A_BOLD)
        self._refresh()


class main_pane(pane):

    '''
    Right now, only the main pane handles widgets,
        however widgets are instantiated by taking a pane object.
    '''

    def __init__(self, h, w, off_y):
        pane.__init__(self, h, w, off_y)
        self._window.border()
        self._window.keypad(True)
        self._active_widget = None
        self.widget_list = []  # Not sure if this is needed yet

    def input(self, inp):
        self._active_widget.input(inp)

    def getch(self):
        return self._window.getch()

    def get_wdgt(self, ident):
        for i in self.widget_list:
            if i.id == ident:
                return i

        return None

    @property
    def actv_wdgt(self):
        return self._active_widget

    @actv_wdgt.setter
    def actv_wdgt(self, widget):
        self._active_widget = widget
        self._active_widget.execute()


class footer_pane(pane):
    def __init__(self, h, w, off_y):
        pane.__init__(self, h, w, off_y)
        self._controls = []
        self._refresh()
        self._width = self._window.getmaxyx()[1]

    @property
    def controls(self):
        return self._controls

    @controls.setter
    def controls(self, new_controls):
        self._controls = new_controls
        self._render()

    def _render(self):
        self._clr_all()
        str = " | ".join(self._controls)

        if len(str) <= self._width:

            self._window.addstr(
                0, center(str, self._window.getmaxyx()[1]), str, curses.A_BOLD)

        else:

            i = len(self._controls)
            while len(str) >= self._width:
                str = " | ".join(self._controls[:i])
                i -= 1
            str = " | ".join(self._controls[:i])
            str2 = " | ".join(self._controls[i:])
            self._window.addstr(
                0, center(str, self._window.getmaxyx()[1]), str, curses.A_BOLD)
            self._window.addstr(
                2, center(str2, self._window.getmaxyx()[1]), str2, curses.A_BOLD)

        self._refresh()


# UTILITY

def center(string, w):
    '''Returns an integer to center a string of text
    in a curses window.

    Parameters
    ----------
    string : string
        the string that you are trying to center
    win_width : int
        width of the window
    '''
    return int(w/2)-int(len(string)/2)


def inbounds(int, list):
    if(not list):
        return False
    if(int >= 0 and int < len(list)):
        return True
    return False
