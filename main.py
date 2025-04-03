# main.py - 主入口
from tkinter import Tk
from gui import NovelManagerGUI

if __name__ == "__main__":
    root = Tk()
    app = NovelManagerGUI(root)
    root.mainloop()
