import sys
import sqlite3

from itertools import chain
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from modules.todo import todo


def except_hook(cls, exception, traceback):
    sys.excepthook(cls, exception, traceback)


app = QApplication(sys.argv)
w = todo()
w.show()
sys.excepthook = except_hook
sys.exit(app.exec())
