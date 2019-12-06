import secrets
import sqlite3
from config import DB_NAME, LOGIN_REWARD

SESSION_DB = DB_NAME


# Authorization
# check token
class AuthException(Exception):
    pass


def authorize(token):
    conn = sqlite3.connect(SESSION_DB)
    nick = conn.execute('SELECT nickname FROM session WHERE token=?', (token,)).fetchone()
    if not nick:
        raise Exception('No active session')
    user = User(nick[0])
    return user


# authenticate user(login)
def authenticate(username):
    user = User(username)
    return user


def end_session(token):
    with sqlite3.connect(SESSION_DB) as c:
        c.execute('DELETE FROM session WHERE token=?', (token,))


def get_or_create_user_db(nick):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('INSERT OR IGNORE INTO accounts VALUES (?,?)', (nick, 0))
    conn.commit()
    user = conn.execute('SELECT * from accounts WHERE nickname=?', (nick,))
    return user.fetchone()


def inc_balance(nick, amount):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('UPDATE accounts SET balance = balance + ? WHERE nickname=?', (amount, nick))
    conn.commit()
    balance = conn.execute('SELECT balance from accounts where nickname=?', (nick,))
    return balance.fetchone()[0]


class User:
    def __init__(self, nick):
        nickname, balance = get_or_create_user_db(nick)
        self.nickname = nickname
        self.balance = balance

    @property
    def items(self):
        item_list = sqlite3.connect(DB_NAME).execute('SELECT item_name FROM ownership WHERE nickname=?',
                                                     (self.nickname,)).fetchall()
        return [column[0] for column in item_list]

    def buy_item(self, item_name):
        with sqlite3.connect(DB_NAME) as c:
            item_price = c.execute('SELECT price from items where item_name=?', (item_name,)).fetchone()[0]
            c.execute('INSERT INTO ownership VALUES (?, ?)', (self.nickname, item_name))
            c.execute('UPDATE accounts set balance=balance-? where nickname=?', (item_price, self.nickname))
        self.balance = c.execute('SELECT balance from accounts where nickname=?', (self.nickname,)).fetchone()[0]

    def sell_item(self, item_name):
        with sqlite3.connect(DB_NAME) as c:
            item_price = c.execute('select price from items where item_name=?', (item_name,)).fetchone()[0]
            c.execute('delete from ownership where nickname=? and item_name=?', (self.nickname, item_name))
            c.execute('update accounts set balance=balance+? where nickname=?', (item_price, self.nickname))
        self.balance = c.execute('SELECT balance from accounts where nickname=?', (self.nickname,)).fetchone()[0]

    def award(self):
        self.set_balance(self.balance + LOGIN_REWARD)

    def set_balance(self, value):
        with sqlite3.connect(DB_NAME) as c:
            c.execute('UPDATE accounts SET balance = ? WHERE nickname=?', (value, self.nickname))
        self.balance = c.execute('SELECT balance from accounts where nickname=?', (self.nickname,)).fetchone()[0]
        return self.balance
