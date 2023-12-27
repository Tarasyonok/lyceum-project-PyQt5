import sqlite3
import datetime

from itertools import chain
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from UIpy.createEditTaskUI import Ui_MainWindow


class createTask(QMainWindow, Ui_MainWindow):
    def __init__(self, parent, task_type):
        super().__init__()
        self.setupUi(self)
        # uic.loadUi('createEditTask.ui', self)
        self.setWindowIcon(QIcon('icons/to-do-list.png'))
        self.parent = parent

        self.task_type = task_type

        con = sqlite3.connect("data/database.sqlite")
        cur = con.cursor()

        categories = cur.execute("""SELECT title from categories""")

        self.categoryInput.addItem("Без категории")
        for category in categories:
            self.categoryInput.addItem(category[0])

        if self.task_type != 'daily':
            self.repeatLabel.hide()
            for btn in self.weekButtons.buttons():
                btn.hide()
                btn.clicked.connect(self.toggle_day)
        else:
            self.week = {"ПН": 1, "ВТ": 1, "СР": 1, "ЧТ": 1, "ПТ": 1, "СБ": 1, "ВС": 1}
            for btn in self.weekButtons.buttons():
                btn.clicked.connect(self.toggle_day)

        self.cancelBtn.clicked.connect(self.cancel)
        self.saveBtn.clicked.connect(self.save)
        self.loadImageBtn.clicked.connect(self.load_image)

        self.fname = None

        if self.task_type == 'daily' or self.task_type == 'week' or self.task_type == 'month':
            self.deadlineInput.hide()
            self.deadlineFrame.hide()
            self.deadlineCheckBox.hide()
        elif self.task_type == 'today':
            self.deadlineInput.setMinimumDate(QDate.currentDate())
            self.deadlineCheckBox.stateChanged.connect(self.toggle_deadline)
        else:
            self.deadlineInput.setMinimumDate(QDate.currentDate().addDays(1))
            self.deadlineCheckBox.stateChanged.connect(self.toggle_deadline)

    def toggle_deadline(self, x):
        self.deadlineInput.setEnabled(bool(x))

    def cancel(self):
        self.close()

    def toggle_day(self):
        if self.week[self.sender().text()]:
            if sum(self.week.values()) == 1:
                self.statusBar().showMessage("Должен быть выбран хотя бы один день недели.", 5000)
                return
            self.sender().setStyleSheet(f"background-color: #fff; border: 5px solid #fff;")
            self.week[self.sender().text()] = 0
        else:
            self.sender().setStyleSheet(f"background-color: #0f0; border: 5px solid #0f0;")
            self.week[self.sender().text()] = 1

    def save(self):
        title = self.titleInput.text()
        if title.strip() == '':
            self.statusBar().showMessage("Название не может быть пустым", 5000)
            return

        con = sqlite3.connect("data/database.sqlite")
        cur = con.cursor()

        category_title = self.categoryInput.currentText()
        description = self.descriptionInput.toPlainText()

        if self.task_type == 'daily':
            repeat = []

            for d in self.week:
                if self.week[d]:
                    repeat.append(d)
            repeat = ', '.join(repeat)

        if category_title == 'Без категории':
            category = 'NULL'
        else:
            category = cur.execute("""
            SELECT id FROM categories
            WHERE title = ?
            """, (category_title,)).fetchone()[0]

        titles = []

        for i in range(self.parent.tasksList.count()):
            titles.append(self.parent.tasksList.item(i).text())

        for t in titles:
            if title == t:
                self.statusBar().showMessage("Такое дело уже есть в списке", 5000)
                return

        if self.deadlineCheckBox.isChecked():
            deadline = "'" + self.deadlineInput.date().toString("yyyy-MM-dd") + "'"
        else:
            deadline = 'NULL'

        if self.fname:
            with open("LocalStorage.txt", 'r') as ls:
                n = int(ls.readlines()[-1])
                path = f"userImages/img{n}.png"
            self.image.save(path)
            path = "'" + path + "'"

            with open("LocalStorage.txt", 'w') as ls:
                ls.write(str(datetime.datetime.now().date()))
                ls.write('\n')
                ls.write(str(n + 1))

        else:
            path = 'NULL'

        if self.task_type == 'today':
            cur.execute(f"""
            INSERT INTO Today(title, description, category, isDone, deadline, image)
            VALUES('{title}', '{description}', {category}, 0, {deadline}, {path})
            """)
        if self.task_type == 'week':
            cur.execute(f"""
            INSERT INTO Week(title, description, category, isDone, image)
            VALUES('{title}', '{description}', {category}, 0, {path})
            """)
        if self.task_type == 'month':
            cur.execute(f"""
            INSERT INTO Month(title, description, category, isDone, image)
            VALUES('{title}', '{description}', {category}, 0, {path})
            """)
        elif self.task_type == 'tomorrow':
            cur.execute(f"""
            INSERT INTO Tomorrow(title, description, category, deadline, image)
            VALUES('{title}', '{description}', {category}, {deadline}, {path})
            """)
        elif self.task_type == 'daily':
            cur.execute(f"""
            INSERT INTO Daily(title, description, category, repeat, image)
            VALUES('{title}', '{description}', {category}, '{repeat}', {path})
            """)

        con.commit()
        con.close()

        self.parent.load_tasks()

        con.close()
        self.close()

    def load_image(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '',
                                                 '*.jpg *.jpeg *.png')[0]
        self.image = QImage(self.fname)
        self.statusBar().showMessage("Картинка загружена", 5000)
