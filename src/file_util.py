import pickle
import curses
import panes
import tkinter as tk
from tkinter import filedialog
from os import listdir, walk
from os.path import isfile, join, isdir, abspath
import dcs

EXTS_DECORATORS = {".mp3":dcs.AUDIOFILE,
                    ".wav":dcs.AUDIOFILE,
                    ".aif":dcs.AUDIOFILE,
                    ".asd":dcs.AUDIOFILE,
                    ".mid":dcs.MISC}

class file_explorer():
    def __init__(self):
        root = tk.Tk()
        self.__objs = {}
        root.withdraw()
        root.attributes("-topmost", True)
        self.__root_path = filedialog.askdirectory(mustexist=True,parent=root)
        root.attributes("-topmost", False)
        self.__current_dir = ""
        self.__flagged = {}
        self.hier_label = ""
        self.build()

    def build(self):
        self.__objs[self.__root_path] = {"files":[],"dirs":[]}
        self.__flagged[self.__root_path] = []
        for root, dirs, files in walk(self.__root_path):
            for file in files:
                path = join(root, file)
                self.__objs[self.__root_path]["files"].append(e_file(path))
            for _dir in dirs:
                path = join(root, _dir)
                self.__objs[self.__root_path]["dirs"].append(e_dir(path))

    def remove(self, file):
        for i in self.__objs.keys():
            if file in self.__objs[i]:
                self.__objs[i]["files"].remove(file)
                self.__flagged[i].remove(file)

    def change_dir_prompt(self):
        root = tk.Tk()
        root.withdraw()
        self.__root_path = None

        while not self.__root_path:
            root.attributes("-topmost", True)
            self.__root_path = filedialog.askdirectory(mustexist=True,parent=root)
            root.attributes("-topmost", False)

        self.__current_dir = ""
        if self.__root_path not in self.__objs:
            self.build()

    def flag(self, file):
        file.flag()
        if file.flagged and self.current_dir:

            self.__flagged[self.__root_path].append(file)
            root = self.__root_path.split("/")
            absolute = self.abs_dir.split("/")

            for i in range(len(root)+1,len(absolute)+1):
                f = self.__get_by_path(absolute[:i])
                f.contains_flagged = True

        if not file.flagged and self.current_dir:
            #Check for contains flagged in each upper directory.
            self.__flagged[self.__root_path].remove(file)
            root = self.__root_path.split("/")
            absolute = self.abs_dir.split("/")

            for i in range(len(absolute)+1,len(root),-1):
                contains_flagged = False
                ls_flagged = [c for c in self.__flagged[self.__root_path] if c.directory == absolute[:i]]
                for b in ls_flagged:
                    if b.flagged or (isdir(b.path) and b.contains_flagged):
                        contains_flagged = True
                        break

                self.__get_by_path(absolute[:i]).contains_flagged = contains_flagged

    def ls_by_dir(self,_dir_list):
        return [i for i in self._objs if i.directory == "/".join(_dir_list)]

    def save(self):
        list = []
        try:
            with open('data/explr', 'rb') as f:
                list = pickle.load(f)
                try:
                    explr = [i for i in list if i.hier_label == self.hier_label][0]
                    list.remove(explr)
                except IndexError:
                    pass
                list.append(self)

            with open('data/explr', 'wb') as f:
                pickle.dump(list, f)

        except EOFError:
            with open('data/explr', 'wb') as f:
                pickle.dump([self], f)

    def __get_by_path(self, path_list):
        return [i for i in self._objs if i.path_list == path_list][0]

    def set_dir(self, _dir):
        self.__root_path = _dir
        self.__current_dir = ""
        if self.__root_path not in self.__objs:
            self.build()

    def back(self):
        super = self.__current_dir.split("/")[:-1]
        try:
            hover = [i for i in (self.__objs[self.__root_path]["dirs"]) if i.path == self.abs_dir][0]
            self.__current_dir = "/".join(super)
            return hover
        except IndexError:
            return False

    def enter(self, dir_name):
        self.__current_dir = join(self.__current_dir, dir_name)

    @property
    def _objs(self):
        '''returns all objects(files and dirs) in current working directory'''
        return (self.__objs[self.__root_path]["files"]+self.__objs[self.__root_path]["dirs"])

    @property
    def dirs_select(self):
        return self.__objs.keys()

    @property
    def files(self):
        '''list current files'''
        return [i for i in self.__objs[self.__root_path]["files"] if i.directory == self.abs_dir]

    @property
    def dirs(self):
        '''list current dirs'''
        return [i for i in self.__objs[self.__root_path]["dirs"] if i.directory == self.abs_dir]

    @property
    def abs_dir(self):
        if self.__current_dir:
            return join(self.__root_path, self.__current_dir)
        else:
            return self.__root_path

    @property
    def name(self):
        return self.__root_path.split("/")[-1]

    @property
    def current_dir(self):
        return self.__current_dir

    @property
    def all_flagged(self):
        _all = []
        for i in self.__flagged.keys():
            _all += self.__flagged[i]
        return _all

class vfile_hierarchy():
    def __init__(self, root_label, name):
        self.root_folder = v_dir(None, root_label)
        self.folders = []
        self.label = name
        self.hover = None

    def add_file(self, file):
        for i in self.folders:
            if i.path == file.path:
                return False
        self.folders.append(file)
        return True

    def add_real(self, e_file, parent):
        file = v_file(parent, e_file.label, e_file.path)
        for i in self.folders:
            if i.path == file.path:
                return False
        self.folders.append(file)
        return True

    def rm_file(self, file):
        self.folders.remove(file)

    def get_file(self, path):
        return [i for i in self.folders if i.path == path][0]


    def ls_files_parent(self, parent_path):
        return [i for i in self.folders if i.path[:-1] == parent_path]

    def save(self):
        list = []
        try:
            with open('data/hiers', 'rb') as f:
                list = pickle.load(f)
                try:
                    hier = [i for i in list if i.label == self.label][0]
                    list.remove(hier)
                except IndexError:
                    pass
                list.append(self)

            with open('data/hiers', 'wb') as f:
                pickle.dump(list, f)

        except EOFError:
            with open('data/hiers', 'wb') as f:
                pickle.dump(list, f)

class v_dir():
    def __init__(self, parent, label):
        if parent:
            self.parent = parent
        else:
            self.parent = None
        self.label = label
        self.path = [self]

        i = self.parent

        while(i != None):
            self.path.append(i)
            i = i.parent
        #forward path to file.
        self.path = list(reversed(self.path))
        self.path_str = "/".join([i.label for i in self.path])


class v_file():
    def __init__(self, parent, label, true_loc):
        if parent:
            self.parent = parent
        else:
            self.parent = None
        self.label = label
        self.path = [self]
        self.true_loc = true_loc
        i = self.parent

        while(i != None):
            self.path.append(i)
            i = i.parent
        #forward path to file.
        self.path = list(reversed(self.path))
        self.path_str = "/".join([i.label for i in self.path])

class e_file():
    '''Explorer file
    '''
    def __init__(self, path):
        self.path_list = path.split("/")
        self.decorator = dcs.MISC
        self.flagged = False

        for i in EXTS_DECORATORS.keys():
            if self.label.endswith(i):
                self.decorator = EXTS_DECORATORS[i]


    def flag(self):
        self.flagged = not self.flagged

    @property
    def new_loc(self):
        return self.new_loc + self.label

    @property
    def directory(self):
        return "/".join(self.path_list[:-1])

    @property
    def label(self):
        return self.path_list[-1]

    @property
    def path(self):
        return "/".join(self.path_list)

class e_dir():
    '''Explorer directory
    '''
    def __init__(self, path):
        self.path_list = path.split("/")
        self.decorator = dcs.DIRECTORY
        self.flagged = False
        self.contains_flagged = False
        self.new_loc = None

    def flag(self):
        self.flagged = not self.flagged

    @property
    def directory(self):
        return "/".join(self.path_list[:-1])

    @property
    def label(self):
        return self.path_list[-1]

    @property
    def path(self):
        return "/".join(self.path_list)


def load_hiers():
    with open("data/hiers", 'rb') as f:
        try:
            return [i for i in pickle.load(f)]
        except EOFError:
            return None

def load_explr(hier_label):
    with open("data/explr", 'rb') as f:
        try:
            return [i for i in pickle.load(f) if i.hier_label == hier_label][0]
        except (EOFError, IndexError) as e:
            return None

def del_hier(hier):
    with open('data/hiers', 'rb') as f:
        list = pickle.load(f)
        hier = [i for i in list if i.label == hier.label][0]
        list.remove(hier)

    with open('data/hiers', 'wb') as f:
        pickle.dump(list, f)
