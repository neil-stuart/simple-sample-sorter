import curses
import main
import panes
from enum import Enum
from file_util import (vfile_hierarchy,
                       v_dir,
                       load_hiers,
                       load_explr,
                       del_hier,
                       file_explorer)
import names
import w_id
from os.path import isdir, join
import dcs
from time import sleep

class widget():
    def __init__(self, pane, label, ident):
        self._pane = pane
        self._pane.widget_list.append(self)
        self._height, self._width = pane._window.getmaxyx()
        self._window = pane._window
        self.label = label
        self.id = ident
        self.controls = []
        self._inp_funcs = {}

    def _render(self):
        pass

    def _clr_all(self):
        for i in range(self._window.getmaxyx()[0])[1:-1]:
            self._clrline(i)

    def _clrline(self, line_number):
        # Protects border on main pane.
        self._window.addstr(line_number, 1, panes.EMPT_LINE[:-1])

    def input(self, inp):
        try:
            self._inp_funcs[inp]()
        except KeyError:
            pass

    def execute(self):
        '''
        this function is called once when set to active widget
        '''
        self._render()

    def _f_esc(self):
        self._pane.actv_wdgt = self._pane.get_wdgt(w_id.QUIT)

    def getstr(self, msg):
        curses.echo(), curses.curs_set(1)

        self._clr_all()

        self._window.addstr(1, 1, msg)
        self._window.refresh()

        inp = self._window.getstr(2, 1, 20).decode(encoding="utf-8")

        self._clr_all()

        curses.curs_set(0), curses.noecho()
        return inp


class w_prompt_yn(widget):
    def __init__(self, pane, label, ident):
        widget.__init__(self, pane, label, ident)

        self.parent = None
        self.opts = ["Yes", "No"]
        self._y_n = False

        self.controls = [names.UP,
                         names.DOWN,
                         names.RIGHT_ENTER]

        self._inp_funcs = {259: self._f_up,
                           258: self._f_dwn,
                           261: self._f_entr}

    def _f_up(self):
        self._y_n = True
        self._render()

    def _f_dwn(self):
        self._y_n = False
        self._render()

    def _f_entr(self):
        pass

    def _render(self):
        mid_line = int(self._window.getmaxyx()[0]/2)
        max_x = self._window.getmaxyx()[1]
        offset = -3

        self._clrline(mid_line+offset)
        self._clrline(mid_line+offset+1)
        self._clrline(mid_line+offset+2)

        self._window.addstr(mid_line+offset, center(self.str, max_x), self.str)
        if self._y_n:
            self._window.addstr(mid_line+offset+1, center(self.opts[0], max_x),
                                self.opts[0], curses.A_REVERSE)
            self._window.addstr(mid_line+offset+2, center(self.opts[1], max_x),
                                self.opts[1])
        elif not self._y_n:
            self._window.addstr(mid_line+offset+1, center(self.opts[0], max_x),
                                self.opts[0])
            self._window.addstr(mid_line+offset+2, center(self.opts[1], max_x),
                                self.opts[1], curses.A_REVERSE)


class w_list(widget):
    def __init__(self, pane, label, ident):
        widget.__init__(self, pane, label, ident)
        self._objects = []
        self._hover = None
        self.controls = [names.UP,
                         names.DOWN,
                         names.RIGHT_ENTER]

        self._inp_funcs = {261: self._f_fwd,
                           259: self._f_up,
                           258: self._f_dwn}

    def add(self, object):
        self._hover = object
        self._objects.append(object)
        self._render()

    def remove(self, object):
        self._hover = self._objects[self._objects.index(object)-1]
        self._objects.remove(object)
        self._render()

    def move_curs(self, amount):
        # positive is down, negative is up.
        try:
            pos = self._objects.index(self._hover)
        except Exception:  # If there is no current option.
            pos = -1

        if(inbounds(pos+amount, self._objects)):
            self._hover = self._objects[pos+amount]
            self._render()

    def get_displayable(self):
        '''Returns a list of objects that can be displayed on the screen
        i.e cuts off objects in list that are beyond the screen border.

        Returns
        -------
        list
            displayable objects
        '''
        hoverpos = self._objects.index(self._hover)
        obj_len = len(self._objects)
        y_max = self._window.getmaxyx()[0]-2  # -2 as border counts as a line
        midline = int(y_max/2)
        if obj_len >= y_max:
            if hoverpos >= midline:
                displayable = self._objects[hoverpos -
                                            midline:hoverpos+midline+1]
            else:
                displayable = self._objects[0:y_max]
        else:
            displayable = self._objects

        return displayable

    def _render(self):
        self._clr_all()
        if self._objects:
            for i in self._objects:
                self._window.addstr(self._objects.index(i)+1, 1, i.label)
            self._window.addstr(self._objects.index(
                self._hover)+1, 1, self._hover.label, curses.A_REVERSE)

    def _f_up(self):
        self.move_curs(-1)

    def _f_dwn(self):
        self.move_curs(1)

    def _f_fwd(self):
        pass

class w_alert(widget):
    def __init__(self, pane, label, ident):
        widget.__init__(self, pane, label, ident)
        self.msg = None
        self.parent = None
        self.str = names.CONTINUE
        self.controls = [names.RIGHT_ENTER]
        self._inp_funcs = {261: self._f_fwd}

    def _f_fwd(self):
        self._pane.actv_wdgt = self.parent

    def _render(self):
        mid_line = int(self._window.getmaxyx()[0]/2)
        max_x = self._window.getmaxyx()[1]
        offset = -2

        self._clrline(mid_line+offset)
        self._clrline(mid_line+offset+1)

        self._window.addstr(mid_line+offset, center(self.msg, max_x), self.msg)
        self._window.addstr(
            mid_line+offset+1, center(self.str, max_x), self.str, curses.A_REVERSE)


class w_vflist(w_list):
    '''Virtual file explorer,
    lists to-be hierarchy.
    '''

    def __init__(self, pane, label, ident, file_hier=None):
        w_list.__init__(self, pane, label, ident)
        if file_hier:
            self._file_hier = file_hier
        else:
            self._file_hier = None
        self._file_explr = None
        self._current_folder = None
        self.label = "File List"
        self.controls = [names.UP,
                         names.DOWN,
                         names.LEFT_BACK,
                         names.RIGHT_ENTER,
                         names.N_NEW_FILE,
                         names.D_DELETE,
                         names.TAB_SAMPLE_VIEW,
                         names.M_MOVE_FLAGGED,
                         names.ESC]

        self._inp_funcs = {259: self._f_up,
                           258: self._f_dwn,
                           260: self._f_bck,
                           261: self._f_fwd,
                           9: self._f_tab,
                           ord('n'): self._f_n,
                           ord('d'): self._f_d,
                           27: self._f_esc,
                           ord('m'): self._f_m}

    def execute(self):
        if not self._file_explr:
            self.explr = self._pane.get_wdgt(w_id.EXPLORER)._file_expl
        self._render()

    def _render(self):

        self._clr_all()
        self.label = self.file_hier.label+" - " + \
            "/".join([i.label for i in self._current_folder.path])

        if self._objects:
            objs = self.get_displayable()
            for i in objs:
                self._window.addstr(objs.index(i)+1, 1, str(i.label))

            self._window.addstr(objs.index(self._hover)+1, 1,
                                self._hover.label, curses.A_REVERSE)

    def newfile(self):

        inp = self.getstr(names.NEW_FOLDER_PROMPT)
        file = v_dir(self._current_folder.path[-1], inp)

        if self.file_hier.add_file(file):
            self._objects = self.file_hier.ls_files_parent(
                self._current_folder.path)
            self._hover = file
            self._file_hier.save()
            self._render()
        else:
            self._render()
            alert = self._pane.get_wdgt(w_id.ALERT)
            alert.msg = names.ALRT_TAKEN
            alert.parent = self
            self._pane.actv_wdgt = alert

    def _f_tab(self):
        explr = self._pane.get_wdgt(w_id.EXPLORER)
        self._pane.actv_wdgt = explr

    def _f_fwd(self):
        if self._hover:
            self._objects = self.file_hier.ls_files_parent(self._hover.path)
            self._current_folder = self._hover
            if self._objects:
                self._hover = self._objects[0]
            else:
                self._hover = None
            self._render()

    def _f_bck(self):
        if(self._current_folder != self.file_hier.root_folder):
            self._hover = self._current_folder
            self._objects = self.file_hier.ls_files_parent(
                self._current_folder.parent.path)
            self._current_folder = self._current_folder.parent
            self._render()

    def _f_n(self):
        self.newfile()

    def _f_d(self):
        if self._hover:
            index = self._objects.index(self._hover)
            self.file_hier.rm_file(self._hover)
            self._objects = self.file_hier.ls_files_parent(
                self._current_folder.path)
            if self._objects:
                try:
                    self._hover = self._objects[index]
                except IndexError:
                    self._hover = self._objects[-1]
            else:
                self._hover = None
            self._render()

    def _f_esc(self):
        w_exit = self._pane.get_wdgt(w_id.EXIT)
        w_exit.parent = self
        self._pane.actv_wdgt = w_exit

    def _f_m(self):
        if self._file_explr:
            for file in self._file_explr.all_flagged:
                self.file_hier.add_real(file, self._current_folder)
                self._file_explr.remove(file)
        self._objects = self.file_hier.ls_files_parent(
            self._current_folder.path)
        self._hover = self._objects[0]
        self._render()

    @property
    def file_hier(self):
        return self._file_hier

    @file_hier.setter
    def file_hier(self, file_hier):
        self._file_hier = file_hier
        self.label = self._file_hier.root_folder.label
        rootfolder = self._file_hier.root_folder
        self._current_folder = self._file_hier.root_folder
        self._objects = self._file_hier.ls_files_parent(rootfolder.path)
        if self._objects:
            self._hover = self._objects[0]
        else:
            self._hover = None
        self._render()


class w_wlist(w_list):
    '''Widget list, displays widgets.
    '''

    def __init__(self, pane, label, ident, widgets=None):
        w_list.__init__(self, pane, label, ident)

        if widgets:
            self._objects = widgets
            self._hover = self._objects[0]
        else:
            self._objects = []
            self._hover = None

    def _render(self):
        self._clr_all()
        if self._objects:
            objs = self.get_displayable()
            for i in objs:
                self._window.addstr(objs.index(i)+1, 1, str(i.label))
            self._window.addstr(objs.index(
                self._hover)+1, 1, self._hover.label, curses.A_REVERSE)

    def _f_fwd(self):
        self._clr_all()
        self._pane.actv_wdgt = self._hover

    def add(self, objects):
        if len(objects) == 1:
            self._objects.append(objects[0])
        else:
            for i in objects:
                self._objects.append(i)
        self._hover = objects[0]


class w_hlist(w_list):
    '''Hierarchy list, displays saved hierarchies.
    '''

    def __init__(self, pane, label, ident):
        w_list.__init__(self, pane, label, ident)
        self._objects = None
        if self._objects:
            self._hover = self._objects[0]

        self.controls = [names.UP,
                         names.DOWN,
                         names.RIGHT_ENTER,
                         names.N_NEW_HIER,
                         names.ESC,
                         names.D_DELETE]

        self._inp_funcs = {261: self._f_fwd,
                           259: self._f_up,
                           258: self._f_dwn,
                           ord('n'): self._f_n,
                           27: self._f_esc,
                           ord('d'): self._f_d,
                           ord('f'): self._f_f}

        self.file_list = None

    def execute(self):
        self._objects = load_hiers()
        if self._objects:
            self._hover = self._objects[0]
        self.file_list = self._pane.get_wdgt(w_id.VFILE_EXPLR)
        self._render()

    def _f_f(self):
        pass

    def _f_d(self):
        prompt = self._pane.get_wdgt(w_id.DEL_HIER)
        prompt.hier = self._hover
        self._pane.actv_wdgt = prompt

    def _f_n(self):
        self.create_hier()

    def _f_fwd(self):
        self.file_list.file_hier = self._hover
        self._pane.actv_wdgt = self.file_list
        self._objects = []

    def create_hier(self):

        name = self.getstr(names.HIER_NAME_PROMPT)

        if(self._objects and (name in [i.label for i in self._objects])):
            alert = self._pane.get_wdgt(w_id.ALERT)
            alert.msg = names.ALRT_DUPLICATE
            alert.parent = self
            self._pane.actv_wdgt = alert
        else:
            root = self.getstr(names.ROOT_FOLDER_PROMPT)
            hier = vfile_hierarchy(root, name)
            hier.save()
            self._objects = load_hiers()
            self._hover = self._objects[0]
            self._render()

    def _f_esc(self):
        w_exit = self._pane.get_wdgt(w_id.EXIT)
        w_exit.parent = self
        self._pane.actv_wdgt = w_exit


class w_explr(w_list):
    '''File explorer, allows you to explore
    your sample library for sorting.
    '''

    def __init__(self, pane, label, ident):
        w_list.__init__(self, pane, label, ident)
        self._file_expl = None
        self.controls = [names.RIGHT_ENTER,
                         names.TAB_HIER_VIEW,
                         names.F_FLAG,
                         names.M_MOVE_FLAGGED,
                         names.S_SAVE_PROGRESS,
                         names.A_FLAG_ALL,
                         names.ESC]

        self._inp_funcs = {259: self._f_up,
                           258: self._f_dwn,
                           260: self._f_bck,
                           261: self._f_fwd,
                           9: self._f_tab,
                           27: self._f_esc,
                           ord('f'): self._f_f,
                           ord('m'): self._f_m,
                           ord('s'): self._f_s,
                           ord('a'): self._f_a}

    def create_explr(self):
        self._file_expl = file_explorer()
        self._file_expl.hier_label = self._pane.get_wdgt(w_id.VFILE_EXPLR).file_hier.label
        self._file_expl.save()
        self._objects = self._file_expl.dirs+self._file_expl.files
        if self._objects:
            self._hover = self._objects[0]
        else:
            self._hover = None

    def execute(self):
        hier_label = self._pane.get_wdgt(w_id.VFILE_EXPLR).file_hier.label
        if not self._file_expl:
            explr = load_explr(hier_label)
            if explr:
                self._file_expl = explr
                self._objects = self._file_expl.dirs+self._file_expl.files
                if self._objects:
                    self._hover = self._objects[0]
                else:
                    self._hover = None
            else:
                self.create_explr()
        else:
            self._objects = self._file_expl.dirs+self._file_expl.files
            if self._objects:
                self._hover = self._objects[0]
            else:
                self._hover = None

        self._render()

    def saved_indicator(self):
        str = "Progress Saved"
        self._window.addstr(int(self._height*0.4),center(str, self._width),str,curses.A_REVERSE)
        self._window.refresh()
        sleep(0.8)

        self._render()

    def _f_s(self):
        self._file_expl.save() # save button, used to save whenever a file was flagged but took too long
                               # implement periodic autosave eventually?
        self.saved_indicator()

    def _f_f(self):
        self._file_expl.flag(self._hover)
        self._render()

    def _f_m(self):
        self._pane.actv_wdgt = self._pane.get_wdgt(w_id.VFILE_EXPLR)

    def _render(self):
        self._clr_all()
        self.label = "/" + self._file_expl.current_dir
        if self._objects:

            objs = self.get_displayable()
            for i in objs:
                self._window.addstr(objs.index(i)+1, 1, self._format(i))

            self._window.addstr(objs.index(self._hover)+1, 1,
                                self._format(self._hover), curses.A_REVERSE)

    def _format(self, e_file):
        '''Returns a filename to be printed to the screen
        containing any decorators needed.

        Parameters
        ----------
        filedir : string
            full directory to file
        '''
        filename = e_file.label
        if e_file.flagged:
            string = "F| " + e_file.decorator + f" {filename}"
        elif isdir(e_file.path) and e_file.contains_flagged:
            string = dcs.ACTIVE+"| " + e_file.decorator + f" {filename}"
        else:
            string = " | " + e_file.decorator + f" {filename}"

        return string

    def _f_tab(self):
        VFILES = self._pane.get_wdgt(w_id.VFILE_EXPLR)
        VFILES._file_explr = self._file_expl
        self._pane.actv_wdgt = VFILES

    def _f_fwd(self):
        if(isdir(self._hover.path)):
            self._file_expl.enter(self._hover.label)
            self._objects = self._file_expl.dirs+self._file_expl.files

            if self._objects:
                self._hover = self._objects[0]
            else:
                self._hover = None

            self._render()

    def _f_bck(self):
        hover = self._file_expl.back()
        if hover:
            self._hover = hover
            self._objects = self._file_expl.dirs+self._file_expl.files
            self._render()
        elif hover == False:
            self._pane.actv_wdgt = self._pane.get_wdgt(w_id.DIR_SELECT)

    def _f_esc(self):
        w_exit = self._pane.get_wdgt(w_id.EXIT)
        w_exit.parent = self
        self._pane.actv_wdgt = w_exit

    def _f_a(self):
        for file in self._file_expl.files:
            self._file_expl.flag(file)
        self._render()

class w_dir_select(w_list):
    '''Select directories from list.
    '''

    def __init__(self, pane, label, ident, file_expl):
        w_list.__init__(self, pane, label, ident)
        self.label = "Directory Selector"
        self.file_expl = file_expl
        try:
            self._objects = self.file_expl.dirs_select
        except AttributeError:
            pass
        self.controls = [names.UP,
                         names.DOWN,
                         names.RIGHT_ENTER,
                         names.TAB_HIER_VIEW,
                         names.ESC,
                         names.N_NEW_DIR]

        self._inp_funcs = {259: self._f_up,
                           258: self._f_dwn,
                           261: self._f_fwd,
                           9: self._f_tab,
                           27: self._f_esc,
                           ord('n'): self._f_n}

    def execute(self):
        self._objects = [str(i) for i in self.file_expl._file_expl.dirs_select]
        if self._objects:
            self._hover = self._objects[0]

        self._render()

    def _render(self):
        self._clr_all()

        if self._objects:
            objs = self.get_displayable()
            for i in objs:
                self._window.addstr(objs.index(i)+1, 1, i)

            self._window.addstr(objs.index(self._hover)+1, 1,
                                self._hover, curses.A_REVERSE)

    def _f_n(self):
        self.file_expl._file_expl.change_dir_prompt()
        self._objects = [str(i) for i in self.file_expl._file_expl.dirs_select]
        self._render()

    def _f_fwd(self):
        if self._hover:
            self.file_expl._file_expl.set_dir(self._hover)
            self._pane.actv_wdgt = self._pane.get_wdgt(w_id.EXPLORER)

    def _f_tab(self):
        self._pane.actv_wdgt = self._pane.get_wdgt(w_id.VFILE_EXPLR)

    def _f_esc(self):
        w_exit = self._pane.get_wdgt(w_id.EXIT)
        w_exit.parent = self
        self._pane.actv_wdgt = w_exit


class w_prompt_quit(w_prompt_yn):
    def __init__(self, pane, label, ident):
        w_prompt_yn.__init__(self, pane, label, ident)
        self.str = names.QUIT_PROMPT

    def _f_entr(self):
        if self._y_n:
            self._pane.quit = True
        else:
            self._clr_all()
            self._pane.actv_wdgt = self.parent


class w_prompt_return(w_prompt_yn):
    def __init__(self, pane, label, ident):
        w_prompt_yn.__init__(self, pane, label, ident)
        self.str = names.RT_MAIN_MENU_PROMPT

    def _f_entr(self):
        if self._y_n:
            self._clr_all()
            self._pane.actv_wdgt = self._pane.get_wdgt(w_id.MAIN_MENU)
        else:
            self._clr_all()
            self._pane.actv_wdgt = self.parent


class w_prompt_hdelete(w_prompt_yn):
    def __init__(self, pane, label, ident):
        w_prompt_yn.__init__(self, pane, label, ident)
        self.hier = None

    def execute(self):
        self.str = names.DEL_HIER_PROMPT.format(self.hier.label)
        self._render()

    def _f_entr(self):
        if self._y_n:
            self._clr_all()
            del_hier(self.hier)
            self._pane.actv_wdgt = self._pane.get_wdgt(w_id.HIER_LIST)
        else:
            self._clr_all()
            self._pane.actv_wdgt = self._pane.get_wdgt(w_id.HIER_LIST)


# Utility funcs

def inbounds(int, list):
    if(not list):
        return False
    if(int >= 0 and int < len(list)):
        return True
    return False


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
