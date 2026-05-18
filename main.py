import tkinter as tk
from gui import NovelApp


def main():
    root = tk.Tk()
    app = NovelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()