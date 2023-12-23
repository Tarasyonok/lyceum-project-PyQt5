import datetime
import sqlite3
import csv
import os

from itertools import chain
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from modules.createTask import createTask
from modules.editTask import editTask
from modules.categoriesSettings import categoriesSettings
from modules.createReminder import createReminder
from modules.alarm import alarm

from UIpy.todoUI import Ui_Todo


class todo(QMainWindow, Ui_Todo):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # uic.loadUi('UIui/todo.ui', self)
        self.setWindowIcon(QIcon('icons/to-do-list.png'))
        self.tasksList.setIconSize(QSize(20, 20))
        self.tasksList.setFont(QFont("Times", 12, QFont.Black))

        self.addBtn.clicked.connect(self.add_task)

        self.tasksList.itemDoubleClicked.connect(self.update_box)

        self.today.clicked.connect(self.load_today)
        self.tomorrow.clicked.connect(self.load_tomorrow)
        self.daily.clicked.connect(self.load_daily)
        self.week.clicked.connect(self.load_week)
        self.month.clicked.connect(self.load_month)

        self.categoriesSettingsBtn.clicked.connect(self.open_categories_settings)
        self.reminderBtn.clicked.connect(self.create_reminder)
        self.intoCsvBtn.clicked.connect(self.make_csv_plan)
        self.allDaysBtn.clicked.connect(self.show_all)

        self.deleteBtn.clicked.connect(self.delete_task)
        self.markAsDoneBtn.clicked.connect(self.btn_update_box)
        self.editBtn.clicked.connect(self.show_edit_task)
        self.viewImageBtn.clicked.connect(self.show_image)

        with open('LocalStorage.txt', 'r', encoding="utf8") as ls:
            last_come_date = ls.readline().strip()
            if last_come_date != str(datetime.datetime.now().date()):
                self.change_plans()

        self.hide_right_part()

        self.curr_plan = ''

        self.load_today()
        self.load_timer()

        self.load_images()
        self.load_font()

    def load_images(self):
        self.deleteBtn.setIcon(QIcon(r"images/bin.png"))
        self.viewImageBtn.setIcon(QIcon(r"images/view-image.png"))
        self.editBtn.setIcon(QIcon(r"images/pen.png"))

    def load_font(self):
        fontId = QFontDatabase.addApplicationFont(r"fonts/Roboto/Roboto-Regular.ttf")
        if fontId == 0:
            fontName = QFontDatabase.applicationFontFamilies(fontId)[0]
            self.font = QFont(fontName, 15)
        else:
            self.font = QFont()

        Rubik_fontId = QFontDatabase.addApplicationFont(r"fonts/Rubik_Dirt/RubikDirt-Regular.ttf")
        if fontId == 0:
            fontName = QFontDatabase.applicationFontFamilies(Rubik_fontId)[0]
            self.Rubik_font = QFont(fontName, 15)
        else:
            self.Rubik_font = QFont()

        self.tasksList.setFont(self.font)

        self.today.setFont(self.font)
        self.tomorrow.setFont(self.font)
        self.daily.setFont(self.font)
        self.week.setFont(self.font)
        self.month.setFont(self.font)

        self.categoriesSettingsBtn.setFont(self.font)
        self.reminderBtn.setFont(self.font)
        self.intoCsvBtn.setFont(self.font)
        self.allDaysBtn.setFont(self.font)

        self.addBtn.setFont(self.font)

        self.title.setFont(self.font)
        self.category.setFont(self.font)
        self.markAsDoneBtn.setFont(self.font)

        self.titleLabel.setFont(self.font)
        self.categoryLabel.setFont(self.font)
        self.repeatLabel.setFont(self.font)
        self.descriptionLabel.setFont(self.font)

        self.planLabel.setFont(self.Rubik_font)

    def keyPressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()

        if event.key() == 16777220 and self.tasksList.currentItem():
            self.show_right_part(self.tasksList.currentItem())
        if event.key() == 16777223 and self.tasksList.currentItem():
            self.show_right_part(self.tasksList.currentItem())
            self.delete_task()
            self.hide_right_part()
        if event.key() == 16777265 and self.tasksList.currentItem():
            self.show_right_part(self.tasksList.currentItem())
            self.show_edit_task()
            self.hide_right_part()
        if modifiers == Qt.ControlModifier and event.key() == 78:
            self.add_task()

    def load_timer(self):
        con = sqlite3.connect("data/database.sqlite")
        cur = con.cursor()

        now = datetime.datetime.now()

        self.timer = QTimer()
        self.curr_time = QTime(now.hour, now.minute, now.second)
        self.time = QTime(self.curr_time)
        self.timer.timeout.connect(self.time_management)
        self.timer.start(1000)

        self.reminders = cur.execute(f"""
        SELECT * from reminders
        WHERE date = '{now.date()}'
        """).fetchall()

        con.close()

    def time_management(self):
        self.time = self.time.addSecs(1)
        if self.time.hour() == 0 and self.time.minute() == 0:
            self.change_plans()
        for r in self.reminders:
            h, m = map(int, r[2].split(':'))
            if self.time.hour() == h and self.time.minute() == m:
                self.alarm_widet = alarm(self, r[2], r[3])
                self.alarm_widet.show()

                con = sqlite3.connect("data/database.sqlite")
                cur = con.cursor()

                cur.execute(f"""
                DELETE FROM reminders
                WHERE id = {r[0]}
                """)
                con.commit()
                self.reminders.remove(r)
                con.close()

    def load_tasks(self):
        con = sqlite3.connect("data/database.sqlite")
        cur = con.cursor()

        self.addBtn.show()
        if self.curr_plan == 'all':
            self.addBtn.hide()
            result1 = cur.execute(f"""
            SELECT Today.title, IFNULL(categories.color, '255 255 255')
            FROM Today
            LEFT JOIN categories
            ON Today.category = categories.id
            WHERE isDone = 0
            """).fetchall()
            result2 = cur.execute(f"""
            SELECT Tomorrow.title, IFNULL(categories.color, '255 255 255')
            FROM Tomorrow
            LEFT JOIN categories
            ON Tomorrow.category = categories.id
            """).fetchall()
            result3 = cur.execute(f"""
            SELECT Week.title, IFNULL(categories.color, '255 255 255')
            FROM Week
            LEFT JOIN categories
            ON Week.category = categories.id
            WHERE isDone = 0
            """).fetchall()
            result4 = cur.execute(f"""
            SELECT Month.title, IFNULL(categories.color, '255 255 255')
            FROM Month
            LEFT JOIN categories
            ON Month.category = categories.id
            WHERE isDone = 0
            """).fetchall()
            result = chain(result1, result2, result3, result4)

        elif self.curr_plan == 'today':
            result = cur.execute(f"""
            SELECT Today.title, IFNULL(categories.color, '255 255 255'), isDone, deadline
            FROM Today
            LEFT JOIN categories
            ON Today.category = categories.id
            """).fetchall()
        elif self.curr_plan == 'week':
            result = cur.execute(f"""
            SELECT Week.title, IFNULL(categories.color, '255 255 255'), isDone
            FROM Week
            LEFT JOIN categories
            ON Week.category = categories.id
            """).fetchall()
        elif self.curr_plan == 'month':
            result = cur.execute(f"""
            SELECT Month.title, IFNULL(categories.color, '255 255 255'), isDone
            FROM Month
            LEFT JOIN categories
            ON Month.category = categories.id
            """).fetchall()

        elif self.curr_plan == 'tomorrow':
            result1 = cur.execute(f"""
            SELECT Tomorrow.title, IFNULL(categories.color, '255 255 255')
            FROM Tomorrow
            LEFT JOIN categories
            ON Tomorrow.category = categories.id
            """).fetchall()

            result2 = cur.execute(f"""
            SELECT Daily.title, IFNULL(categories.color, '255 255 255')
            FROM Daily
            LEFT JOIN categories
            ON Daily.category = categories.id
            """).fetchall()

            result3 = cur.execute(f"""
            SELECT Today.title, IFNULL(categories.color, '255 255 255')
            FROM Today
            LEFT JOIN categories
            ON Today.category = categories.id
            WHERE Today.isDone = 0
            """).fetchall()
            result = chain(result1, result2, result3)
        elif self.curr_plan == 'daily':
            result = cur.execute(f"""
            SELECT Daily.title, IFNULL(categories.color, '255 255 255')
            FROM Daily
            LEFT JOIN categories
            ON Daily.category = categories.id
            """).fetchall()

        self.tasksList.clear()
        titles = []
        for elem in result:
            if elem[0] not in titles:
                titles.append(elem[0])
                item = QListWidgetItem()
                item.setText(elem[0])

                c1, c2, c3 = map(int, elem[1].split())
                if 1 - (0.299 * c1 + 0.587 * c2 + 0.114 * c3) / 255 < 0.5:
                    item.setForeground(QColor(0, 0, 0))
                    if self.curr_plan == 'today' or self.curr_plan == 'week' or self.curr_plan == 'month':
                        if elem[2] == 0:
                            icon = QIcon(r'images/blackCheckboxOff.png')
                        else:
                            icon = QIcon(r'images/blackCheckboxOn.png')
                        item.setIcon(icon)
                        if self.curr_plan == 'today' and elem[3]:
                            y, m, d = map(int, elem[3].split('-'))
                            if (datetime.datetime(y, m, d) - datetime.datetime.now()).days < 2:
                                item.setText('🚨 ' + elem[0])
                            elif (datetime.datetime(y, m, d) - datetime.datetime.now()).days < 5:
                                item.setText('🎯 ' + elem[0])

                else:
                    item.setForeground(QColor(255, 255, 255))
                    if self.curr_plan == 'today' or self.curr_plan == 'week' or self.curr_plan == 'month':
                        if elem[2] == 0:
                            icon = QIcon(r'images/whiteCheckboxOff.png')
                        else:
                            icon = QIcon(r'images/whiteCheckboxOn.png')
                        item.setIcon(icon)
                item.setBackground(QColor(c1, c2, c3))

                self.tasksList.addItem(item)
        con.close()

    def load_today(self):
        if self.curr_plan != 'today':
            self.hide_right_part()
        self.curr_plan = 'today'
        self.planLabel.setText("План на сегодня")
        self.load_tasks()

    def load_tomorrow(self):
        if self.curr_plan != 'tomorrow':
            self.hide_right_part()
        self.curr_plan = 'tomorrow'
        self.planLabel.setText("План на завтра")
        self.load_tasks()

    def load_daily(self):
        if self.curr_plan != 'daily':
            self.hide_right_part()
        self.curr_plan = 'daily'
        self.planLabel.setText("Ежедневные дела")
        self.load_tasks()

    def load_week(self):
        if self.curr_plan != 'week':
            self.hide_right_part()
        self.curr_plan = 'week'
        self.planLabel.setText("План на неделю")
        self.load_tasks()

    def load_month(self):
        if self.curr_plan != 'month':
            self.hide_right_part()
        self.curr_plan = 'month'
        self.planLabel.setText("План на месяц")
        self.load_tasks()

    def show_all(self):
        if self.curr_plan != 'all':
            self.hide_right_part()
        self.curr_plan = 'all'
        self.planLabel.setText("Все запланированые дела")
        self.load_tasks()

    def update_box(self, item):
        if self.curr_plan != 'today' and self.curr_plan != 'week' and self.curr_plan != 'month':
            return
        text = item.text()
        if text[0] == '🚨' or text[0] == '🎯':
            text = text[2:]

        con = sqlite3.connect("data/database.sqlite")
        cur = con.cursor()
        result = cur.execute(f"""
        SELECT {self.curr_plan}.isDone, IFNULL(categories.color, '255 255 255')
        FROM {self.curr_plan}
        LEFT JOIN categories
        ON {self.curr_plan}.category = categories.id
        WHERE {self.curr_plan}.title = '{text}'
        """).fetchone()

        c1, c2, c3 = map(int, result[1].split())

        if 1 - (0.299 * c1 + 0.587 * c2 + 0.114 * c3) / 255 < 0.5:
            if result[0] == 0:
                icon = QIcon(r'images/blackCheckboxOn.png')

            else:
                icon = QIcon(r'images/blackCheckboxOff.png')

        else:
            if result[0] == 0:
                icon = QIcon(r'images/whiteCheckboxOn.png')

            else:
                icon = QIcon(r'images/whiteCheckboxOff.png')

        item.setIcon(icon)

        if result[0] == 1:
            cur.execute(f"""UPDATE {self.curr_plan} SET isDone = 0 WHERE title = ?""", (text,))
            self.markAsDoneBtn.setText("Пометить как сделанное")
        else:
            cur.execute(f"""UPDATE {self.curr_plan} SET isDone = 1 WHERE title = ?""", (text,))
            self.markAsDoneBtn.setText("Пометить как не сделанное")
        con.commit()
        con.close()

    def btn_update_box(self):
        self.update_box(self.tasksList.currentItem())

    def add_task(self):
        self.create_task = createTask(self, self.curr_plan)
        self.create_task.show()

    def hide_right_part(self):
        self.titleLabel.hide()
        self.title.hide()

        self.categoryLabel.hide()
        self.category.hide()

        self.repeatLabel.hide()
        self.repeat.hide()

        self.deadlineLabel.hide()
        self.deadline.hide()

        self.descriptionLabel.hide()
        self.description.hide()

        self.deleteBtn.hide()
        self.markAsDoneBtn.hide()
        self.viewImageBtn.hide()
        self.editBtn.hide()

    def show_right_part(self, item):
        self.hide_right_part()
        index = self.tasksList.indexFromItem(item).row()

        con = sqlite3.connect("data/database.sqlite")
        cur = con.cursor()

        if self.curr_plan == 'all':
            info1 = cur.execute(
                """SELECT id, title, description, category, image FROM Today WHERE isDone = 0""").fetchall()
            info2 = cur.execute("""SELECT id, title, description, category, image FROM Tomorrow""").fetchall()
            info3 = cur.execute(
                """SELECT id, title, description, category, image FROM Week WHERE isDone = 0""").fetchall()
            info4 = cur.execute(
                """SELECT id, title, description, category, image FROM Month WHERE isDone = 0""").fetchall()
            info = list(chain(info1, info2, info3, info4))

        elif self.curr_plan == 'today':
            info = cur.execute(f"""SELECT * FROM Today""").fetchall()
        elif self.curr_plan == 'week':
            info = cur.execute(f"""SELECT * FROM Week""").fetchall()
        elif self.curr_plan == 'month':
            info = cur.execute(f"""SELECT * FROM Month""").fetchall()
        elif self.curr_plan == 'tomorrow':
            info1 = cur.execute(f"""SELECT * FROM Tomorrow""").fetchall()
            info2 = cur.execute(f"""SELECT * FROM Daily""").fetchall()
            info3 = cur.execute(f"""SELECT * FROM Today WHERE isDone = 0""").fetchall()
            info = list((chain(info1, info2, info3)))
        elif self.curr_plan == 'daily':
            info = cur.execute(f"""SELECT * FROM Daily""").fetchall()

        set_info = []
        titles = []
        for i in info:
            if i[1] not in titles:
                set_info.append(i)
                titles.append(i[1])

        result = set_info[index]

        if result[3]:
            cat = cur.execute(f"""
            SELECT IFNULL(title, 'Без категории') FROM Categories
            WHERE id = {result[3]}
            """).fetchone()
            if cat:
                cat = cat[0]
            else:
                cat = 'Без категории'
        else:
            cat = 'Без категории'

        self.task_id = result[0]

        self.titleLabel.show()
        self.title.clear()
        self.title.append(result[1])
        self.title.show()

        self.categoryLabel.show()
        self.category.clear()
        self.category.append(cat)
        self.category.show()
        if self.curr_plan == 'today' and result[5]:
            self.deadlineLabel.show()
            self.deadline.show()
            self.deadline.setDate(datetime.datetime.strptime(result[5], "%Y-%m-%d").date())
        if self.curr_plan == 'tomorrow' and result in info2 and result[4]:
            self.repeatLabel.show()
            self.repeat.clear()
            self.repeat.append(result[4])
            self.repeat.show()
        if self.curr_plan == 'tomorrow' and result not in info2 and result[4]:
            self.deadlineLabel.show()
            self.deadline.show()
            self.deadline.setDate(datetime.datetime.strptime(result[4], "%Y-%m-%d").date())

        if self.curr_plan == 'daily':
            self.repeatLabel.show()
            self.repeat.clear()
            self.repeat.append(result[4])
            self.repeat.show()
            self.deleteBtn.setFixedSize(100, 30)
            self.editBtn.setFixedSize(100, 30)

        self.descriptionLabel.show()
        self.description.clear()
        self.description.append(result[2])
        self.description.show()

        self.curr_image = result[-1]

        if self.curr_image:
            self.viewImageBtn.show()
        else:
            self.viewImageBtn.hide()
        self.viewImageBtn.setFixedSize(100, 30)

        if self.curr_plan != 'tomorrow' and self.curr_plan != 'all':
            self.deleteBtn.show()
            self.editBtn.show()

        if self.curr_plan == 'today' or self.curr_plan == 'week' or self.curr_plan == 'month':
            self.deleteBtn.setFixedSize(30, 30)
            self.editBtn.setFixedSize(30, 30)
            self.viewImageBtn.setFixedSize(30, 30)
            if result[4]:
                self.markAsDoneBtn.setText("Пометить как не сделанное")
            else:
                self.markAsDoneBtn.setText("Пометить как сделанное")
            self.markAsDoneBtn.show()

    def show_image(self):
        if self.curr_image:
            self.image_window = QMainWindow(self)
            self.img_container = QLabel(self.image_window)
            self.img_container.move(10, 10)
            self.img = QImage(self.curr_image)
            size = self.img.size()
            w = size.width()
            h = size.height()
            if w > h:
                h = int(700 * h / w)
                w = 700
            else:
                w = int(700 * w / h)
                h = 700

            self.pixmap = QPixmap.fromImage(self.img).scaled(w, h)
            self.img_container.setFixedSize(w, h)
            self.image_window.setFixedSize(w + 20, h + 20)

            self.img_container.setPixmap(self.pixmap)
            self.image_window.show()

    def open_categories_settings(self):
        self.categories_settings = categoriesSettings(self)
        self.categories_settings.show()

    def delete_task(self):
        if self.curr_plan == 'tomorrow' or self.curr_plan == 'all':
            return
        con = sqlite3.connect("data/database.sqlite")
        cur = con.cursor()

        cur.execute(f"""
        DELETE FROM {self.curr_plan}
        WHERE id = {self.task_id}
        """)

        con.commit()
        con.close()

        self.load_tasks()

        self.hide_right_part()

        self.statusBar().showMessage("Дело успешно удалено", 5000)

    def show_edit_task(self):
        if self.curr_plan == 'tomorrow' or self.curr_plan == 'all':
            return
        self.edit_task = editTask(self, self.curr_plan, self.task_id)
        self.edit_task.show()

    def create_reminder(self):
        self.reminder = createReminder(self)
        self.reminder.show()

    def change_plans(self):
        con = sqlite3.connect('data/database.sqlite')
        cur = con.cursor()

        result1 = cur.execute(
            """SELECT title, description, category, deadline FROM today WHERE isDone = 0""").fetchall()
        result2 = cur.execute("""SELECT title, description, category, deadline FROM tomorrow""").fetchall()
        result3 = cur.execute("""SELECT title, description, category, 0 FROM daily""").fetchall()

        result = chain(result1, result2, result3)

        cur.execute("""DELETE FROM today""")

        con.commit()

        now = datetime.datetime.now()

        titles = []
        for r in set(result):
            if r[3] and str(r[3]) != '0':
                y, m, d = map(int, r[3].split('-'))
                task_date = datetime.datetime(y, m, d)
                deadline = "'" + r[3] + "'"
            else:
                deadline = 'NULL'

            if r[2]:
                cat = r[2]
            else:
                cat = 'NULL'

            if (deadline == 'NULL' or task_date > now) and r[0] not in titles:
                try:
                    titles.append(r[0])
                    cur.execute(f"""
                    INSERT INTO today(title, description, category, isDone, deadline)
                    VALUES('{r[0]}', '{r[1]}', {cat}, 0, {deadline})
                    """)
                except Exception:
                    pass

        con.commit()

        cur.execute("""DELETE FROM tomorrow""")
        con.commit()

        if datetime.datetime.today().weekday() == 0:
            cur.execute("""DELETE FROM week""")
            con.commit()

        if datetime.datetime.today().day == 1:
            cur.execute("""DELETE FROM month""")
            con.commit()

        con.close()

    def make_csv_plan(self):
        user = os.getenv("USERPROFILE")
        filename = user + r"\Desktop\plan.csv"
        with open(filename, 'w', newline='', encoding="utf8") as csvfile:
            writer = csv.writer(
                csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            writer.writerow(['Название', 'Описание', 'Категория', 'Выполнено/Не выполнено'])

            con = sqlite3.connect('data/database.sqlite')
            cur = con.cursor()

            result = cur.execute("""
            SELECT Today.title, Today.description, IFNULL(categories.title, 'Без категории'),
            CASE WHEN Today.isDone = 1
            THEN 'Выполнено'
            ELSE 'Не выполнено'
            END
            FROM Today
            LEFT JOIN categories
            ON Today.category = categories.id
            """)

            for r in result:
                writer.writerow(r)
        self.statusBar().showMessage(f"План находится в {filename}", 5000)

    def closeEvent(self, event):
        with open('LocalStorage.txt', 'r', encoding="utf8") as ls:
            n = int(ls.readlines()[-1])
        with open('LocalStorage.txt', 'w', encoding="utf8") as ls:
            ls.write(str(datetime.datetime.now().date()))
            ls.write('\n')
            ls.write(str(n))

        try:
            self.create_task.hide()
        except Exception:
            pass
        try:
            self.edit_task.hide()
        except Exception:
            pass
        try:
            self.reminder.hide()
        except Exception:
            pass
        try:
            self.categories_settings.hide()
        except Exception:
            pass
        try:
            self.alarm_widet.hide()
        except Exception:
            pass
        event.accept()
