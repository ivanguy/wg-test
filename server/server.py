#!/usr/bin/env python3
import secrets
import sqlite3
from config import DB_NAME, SERVER_PORT, SERVER_HOST, SESSION_DB
from server.libs.bottle import run, post, get, request, response, abort
from server.auth import authorize, authenticate, end_session, User, AuthException


def load_items():
    from config import items as items_dict
    with sqlite3.connect(DB_NAME) as c:
        c.execute('delete from items')
        c.execute('insert into items values ' + ','.join(str(_) for _ in items_dict.items()))


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create tables
    c.execute('CREATE TABLE IF NOT EXISTS accounts (nickname TEXT PRIMARY KEY, balance INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS items (item_name TEXT PRIMARY KEY UNIQUE, price INTEGER)')
    c.execute('''CREATE TABLE IF NOT EXISTS ownership (
        nickname TEXT,
        item_name TEXT,
        FOREIGN KEY (nickname)  REFERENCES accounts (nickname),
        FOREIGN KEY (item_name) REFERENCES items (item_name)
        UNIQUE (nickname, item_name)
        )''')
    c.execute('DROP TABLE IF EXISTS session')
    c.execute('''CREATE TABLE IF NOT EXISTS session (
        nickname TEXT UNIQUE,
        token TEXT,
        FOREIGN KEY (nickname) REFERENCES accounts (nickname)
        )''')
    conn.commit()
    conn.close()


# Middleware
def login_required(endpoint):
    def wrapped(*args, **kwargs):
        try:
            request.user = authorize(request.get_header('token'))
        except AuthException as e:
            abort(402, str(e))
        return endpoint(*args, **kwargs)

    return wrapped


# Endpoints
# -- auth
@post('/login')
def login():
    nickname = request.body.read().decode('utf-8')
    try:
        user = authenticate(nickname)
    except AuthException:
        return abort(402, 'Login Failed')
    user.award()
    token = secrets.token_urlsafe()

    conn = sqlite3.connect(SESSION_DB)
    conn.execute('INSERT OR REPLACE INTO session VALUES (?,?)', (nickname, token))
    conn.commit()

    response.add_header('token', token)
    print(f'{nickname} has entered the chat')
    return {'nickname': user.nickname, 'balance': user.balance, 'items': user.items}


@get('/logout')
@login_required
def logout():
    end_session(request.get_header('token'))


# -- items
@get('/items_all')
def items_all():
    items = sqlite3.connect(DB_NAME).execute('SELECT * from items').fetchall()
    return dict(items)


@get('/account_data')
@login_required
def my_items():
    return {'nickname': request.user.nickname, 'balance': request.user.balance, 'items': request.user.items}


@post('/item_buy')
@login_required
def buy_item():
    item_name = request.body.read().decode('utf-8')
    c = sqlite3.connect(DB_NAME).cursor()
    item_name, price = c.execute('select item_name, price from items where item_name=?', (item_name,)).fetchone()
    if not item_name:
        abort(404, 'Item not found')
    if item_name in request.user.items:
        abort(403, 'Item already owned')
    if request.user.balance < price:
        abort(400, 'Not enough funds')
    request.user.buy_item(item_name)

    return str(request.user.balance)


@post('/item_sell')
@login_required
def sell_item():
    item_name = request.body.read().decode('utf-8')
    if item_name not in request.user.items:
        abort(400, 'Item not owned')
    request.user.sell_item(item_name)

    return str(request.user.balance)


def run_server(debug=False):
    init_db()
    load_items()
    if debug:
        run(host=SERVER_HOST, port=SERVER_PORT, debug=True, reloader=True)
    else:
        run(host=SERVER_HOST, port=SERVER_PORT, debug=False, reloader=False)
