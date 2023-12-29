import datetime
import sqlite3

from itertools import chain
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from modules.correctPath import correct_path

from UIpy.createEditTaskUI import Ui_MainWindow


class editTask(QMainWindow, Ui_MainWindow):
    def __init__(self, parent, task_type, task_id):
        super().__init__()
        self.setupUi(self)
        # uic.loadUi('createEditTask.ui', self)
        self.setWindowIcon(QIcon(correct_path('icons/to-do-list.png')))
        self.parent = parent

        self.task_type = task_type
        self.task_id = task_id

        self.setWindowTitle('Изменение дела')
        self.windowLabel.setText("Изменение дела")
        self.saveBtn.setText("Сохранить")

        con = sqlite3.connect(correct_path("data/database.sqlite"))
        cur = con.cursor()

        categories = cur.execute("""SELECT title from categories""")

        self.categoryInput.addItem("Без категории")
        for category in categories:
            self.categoryInput.addItem(category[0])

        info = cur.execute(f"""
        SELECT {self.task_type}.title, IFNULL(categories.title, 'Без категории'), {self.task_type}.description 
        FROM {self.task_type}
        LEFT JOIN categories
        ON {self.task_type}.category = categories.id
        WHERE {self.task_type}.id = {task_id}
        """).fetchone()

        if self.task_type == 'today' or self.task_type == 'tomorrow':
            deadline = cur.execute(f"""
        SELECT {self.task_type}.deadline
        FROM {self.task_type}
        WHERE {self.task_type}.id = {task_id}
        """).fetchone()[0]

            if deadline:
                self.deadlineCheckBox.setChecked(True)
                self.deadlineInput.setEnabled(True)
                self.deadlineInput.setDate(datetime.datetime.strptime(deadline, "%Y-%m-%d").date())

        self.task_title = info[0]
        self.titleInput.setText(info[0])
        self.categoryInput.setCurrentText(info[1])

        self.descriptionInput.setPlainText(info[2])

        if self.task_type != 'daily':
            self.repeatLabel.hide()
            for btn in self.weekButtons.buttons():
                btn.hide()
                btn.clicked.connect(self.toggle_day)
        else:
            self.week = {"ПН": 1, "ВТ": 1, "СР": 1, "ЧТ": 1, "ПТ": 1, "СБ": 1, "ВС": 1}
            repeat = cur.execute(f"""
            SELECT repeat FROM Daily
            WHERE id =  {task_id}
            """).fetchone()[0]
            for d in repeat.split(', '):
                self.week[d] = 0
            for btn in self.weekButtons.buttons():
                btn.clicked.connect(self.toggle_day)
                btn.click()

        self.cancelBtn.clicked.connect(self.cancel)
        self.saveBtn.clicked.connect(self.save)
        self.loadImageBtn.hide()

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
        con.close()

    def toggle_deadline(self, x):
        self.deadlineInput.setEnabled(bool(x))

    def cancel(self):
        self.close()

    def toggle_day(self):
        if self.week[self.sender().text()]:
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
        con = sqlite3.connect(correct_path("data/database.sqlite"))
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

        if self.task_title != title:
            titles = []

            for i in range(self.parent.tasksList.count()):
                titles.append(self.parent.tasksList.item(i).text())

            for t in titles:
                if title == t[0]:
                    self.statusBar().showMessage("Такое дело уже есть в списке", 5000)
                    return

        if self.deadlineCheckBox.isChecked():
            deadline = "'" + self.deadlineInput.date().toString("yyyy-MM-dd") + "'"
        else:
            deadline = 'NULL'

        if self.task_type == 'today':
            cur.execute(f"""
            UPDATE Today SET title = '{title}', description = '{description}', category = {category}, deadline = {deadline}
            WHERE id = {self.task_id}
            """)
        if self.task_type == 'week':
            cur.execute(f"""
            UPDATE Week SET title = '{title}', description = '{description}', category = {category}
            WHERE id = {self.task_id}
            """)
        elif self.task_type == 'tomorrow':

            cur.execute(f"""
            UPDATE Tomorrow SET title = '{title}', description = '{description}', category = {category}, deadline = {deadline}
            WHERE id = {self.task_id}
            """)
        elif self.task_type == 'daily':
            cur.execute(f"""
            UPDATE Daily SET title = '{title}', description = '{description}',
            category = {category}, repeat = '{repeat}'
            WHERE id = {self.task_id}
            """)

        con.commit()

        self.parent.load_tasks()

        self.parent.show_right_part(self.parent.tasksList.currentItem())

        con.close()
        self.close()
