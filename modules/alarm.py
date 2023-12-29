import datetime
import os
import sqlite3

from PyQt5 import QtMultimedia
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from UIpy.alarmUI import Ui_MainWindow

from modules.correctPath import correct_path


class alarm(QMainWindow, Ui_MainWindow):
    def __init__(self, parent, time, description):
        super().__init__()
        self.setupUi(self)
        # uic.loadUi('alarm.ui', self)
        self.setWindowIcon(QIcon(correct_path('icons/clock.png')))
        self.parent = parent
        self.time.setText(time)
        self.setWindowTitle(time)
        self.description.setText(description)
        if description.strip() == '':
            self.description.hide()

        self.quiting = False

        # CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
        # filename = os.path.join(CURRENT_DIR, )
        self.player = QtMultimedia.QMediaPlayer()
        # url = QUrl.fromLocalFile(filename)
        url = QUrl.fromLocalFile(correct_path("sounds/sound.mp3"))

        self.player.setMedia(QtMultimedia.QMediaContent(url))
        self.player.play()
        self.closeBtn.clicked.connect(self.closeEvent)
        self.repeatBtn.clicked.connect(self.repeat_alarm)

        self.player.stateChanged.connect(self.repeat_alarm)

    def closeEvent(self, event):
        self.quiting = True
        self.player.stop()
        self.close()

    def repeat_alarm(self):
        if self.quiting:
            return
        con = sqlite3.connect(correct_path("data/database.sqlite"))
        cur = con.cursor()

        ten = (datetime.datetime.now() + datetime.timedelta(minutes=10)).time()
        cur.execute(f"""
        INSERT INTO reminders(date, time, description)
        VALUES('{datetime.datetime.now().date()}', '{str(ten)[:5]}', '{self.description.toPlainText()}')
        """)
        con.commit()
        con.close()

        self.parent.statusBar().showMessage("Напоминание перенесено на 10 минут", 5000)

        self.close()
