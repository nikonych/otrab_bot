import sqlite3
import time

import config


class SQLighter:
    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def get_subscriptions(self, status=True):
        """Получаем всех активных подписчиков бота"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM `subscriptions` WHERE `status` = ?", (status,)).fetchall()

    def getProfileinfo(self, user_id):
        with self.connection:
            return self.cursor.execute('SELECT * FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()

    def user_ex(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def newUser(self, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))

    async def addLogs(self, user_id, payment, date):
        with self.connection:
            self.cursor.execute("INSERT INTO `logs_history` (`user_id`, `payment`, `date`, `checked`) VALUES(?,?,?,?)",
                                (user_id, payment, date, False))

    async def getLastLogs(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT `id` FROM `logs_history` WHERE `user_id` = ?', (user_id,)).fetchall()
            print(result)
            return result[-1][0]

    async def editBalance(self, user_id, balance):
        with self.connection:
            self.cursor.execute("UPDATE `users` SET `balance` = `balance` + ?, `paymet_amount` = `paymet_amount` + ? WHERE `user_id` = ?", (balance, balance, user_id))

    async def editOnlyBalance(self, user_id, balance):
        with self.connection:
            self.cursor.execute("UPDATE `users` SET `balance` = `balance` + ? WHERE `user_id` = ?", (balance, user_id))

    async def addOneLog(self, user_id):
        with self.connection:
            self.cursor.execute("UPDATE `users` SET `q_logs` = `q_logs` + ? WHERE `user_id` = ?", (1, user_id))

    async def updateLogs(self, id, payment, checked):
        with self.connection:
            self.cursor.execute("UPDATE `logs_history` SET `payment` = ?, `checked` = ? WHERE `id` = ?", (payment,checked,id))

    async def get_logs_user_id(self, id):
        with self.connection:
            result = self.cursor.execute('SELECT `user_id` FROM `logs_history` WHERE `id` = ?', (id,)).fetchall()
            print(result)
            return result[-1][0]

    async def get_user_sent_logs(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `logs_history` WHERE `user_id` = ?', (user_id,)).fetchall()
            return result

    def getAllUsersID(self):
        with self.connection:
            self.connection.row_factory = lambda cursor, row: row[0]
            c = self.connection.cursor()
            ids = c.execute('SELECT user_id FROM users').fetchall()
            return ids

    async def get_data_stats(self):
        with self.connection:
            result = {}

            # users
            result['users'] = len(self.cursor.execute('SELECT * FROM users').fetchall())

            # qty_logs
            result['qty_logs'] = self.cursor.execute('SELECT SUM(q_logs) FROM users').fetchone()[0]

            # paid
            result['paid'] = self.cursor.execute('SELECT SUM(paymet_amount) FROM users').fetchone()[0]

            # best_user
            result['best_user'] = self.cursor.execute('SELECT user_id FROM users ORDER BY q_logs DESC').fetchone()[0]

            return result
    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
