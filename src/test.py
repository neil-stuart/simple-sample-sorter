from os import walk
from os.path import join, isdir

from tkinter import filedialog
import tkinter as tk 
# for root, dirs, files in walk("C:\\Users\\neils\\Desktop\\Recovered-Linux\\Presets & Samples"):
#         ok = True
#         for file in files:
#             if ok:
#                 path = join(root, file)
#                 print(f"FILE: {path} isdir = " + str(isdir(path)))
#                 split = path.split("\\")
#                 print(f"FILE: {split} isdir = " + str(isdir(path)))
#                 joined = "\\".join(split)
#                 print(f"FILE: {joined} isdir = " + str(isdir(path)))
#                 ok = False

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
file_path = filedialog.askopenfilename(parent=root)
root.attributes("-topmost", False)