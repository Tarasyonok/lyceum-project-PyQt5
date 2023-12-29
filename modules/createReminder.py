import sqlite3
import os
import datetime

from itertools import chain
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtMultimedia

from modules.alarm import alarm
from modules.correctPath import correct_path

from UIpy.reminderUI import Ui_MainWindow


class createReminder(QMainWindow, Ui_MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        # uic.loadUi('reminder.ui', self)
        self.setWindowIcon(QIcon(correct_path('icons/to-do-list.png')))
        self.parent = parent

        self.timeInput.setTime(datetime.datetime.now().time())

        self.cancelBtn.clicked.connect(self.close)
        self.addBtn.clicked.connect(self.add)

    def add(self):
        date = self.dateInput.selectedDate().toString('yyyy-MM-dd')
        time = self.timeInput.time().toString('hh:mm')
        description = self.descriptionInput.toPlainText()

        con = sqlite3.connect(correct_path("data/database.sqlite"))
        cur = con.cursor()

        result = cur.execute(f"""
        SELECT * FROM reminders
        WHERE date = '{date}' AND time = '{time}'
        """).fetchall()

        if len(result) != 0:
            return

        cur.execute(f"""
        INSERT INTO reminders(date, time, description)
        VALUES('{date}', '{time}', '{description}')
        """)
        con.commit()

        now = datetime.datetime.now()
        self.parent.reminders = cur.execute(f"""
        SELECT * from reminders
        WHERE date = '{now.date()}'
        """).fetchall()
        con.close()

        self.parent.statusBar().showMessage("Напоминание усаешно поставлено", 5000)
        self.close()
