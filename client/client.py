import requests
import json
from config import SERVER_HOST, SERVER_PORT

SERVER_ADDR = 'http://{}:{}'.format(SERVER_HOST, SERVER_PORT)


class User:

    def __init__(self, nickname=None, balance=None, items=None):
        self.nickname = nickname
        self.balance = balance
        self.items = items if items else set()


class Client:

    def __init__(self):
        self.user = User()
        self.token = None
        self.items_all = None
        help_action = {'?': ('help', self.send_help)}

        self._login_actions = {
            'login': ('login with nickname', self.login),
        }
        self._game_actions = {
            'logout': ('end session', self.logout),
            'buy': ('buy [item_name]', self.buy),
            'sell': ('sell [item_name]', self.sell),
            'ls': ('list my items', self.ls),
            'ls all': ('list all items', self.ls_all),
        }
        self._login_actions.update(help_action)
        self._game_actions.update(help_action)

    @property
    def actions(self):
        if not self.logged_in:
            return self._login_actions
        return self._game_actions

    @property
    def logged_in(self):
        return bool(self.token)

    def handle_input(self, user_input):
        try:
            if 'buy' in user_input or 'sell' in user_input:
                user_input = user_input.split(maxsplit=1)
                if len(user_input) > 1:
                    self.actions[user_input[0]][1](user_input[1])
                else:
                    self.actions[user_input[0]][1]()
            else:
                self.actions[user_input][1]()
        except KeyError:
            self.send_help()

    def send_help(self):
        for action, desc in self.actions.items():
            print('{:10}- {}'.format(action, desc[0]))

    def login(self):
        nickname = input('nickname: ')
        r = requests.post(SERVER_ADDR + '/login', data=nickname)
        if r.ok:
            userdata = json.loads(r.content.decode('utf-8'))
            self.user = User(userdata['nickname'], userdata['balance'], set(userdata['items']))
            self.token = r.headers['token']
            print('Welcome {}!'.format(self.user.nickname))
            self.ls()
            return True
        print('Login failed')
        return False

    def logout(self):
        r = requests.get(SERVER_ADDR + '/logout', headers={'token': self.token})
        self.token = None
        self.send_help()

    def ls(self):
        print('Balance {}'.format(self.user.balance))
        print('Inventory: {}'.format(', '.join(self.user.items)))

    def ls_all(self):
        for item_name, price in self.items_all.items():
            print('{:12}- {}'.format(item_name, price))

    def _update_user_data(self):
        r = requests.get(SERVER_ADDR + '/account_data', headers={'token': self.token}, data=self.user.nickname)
        if r.ok:
            userdata = json.loads(r.content.decode('utf-8'))
            self.user = User(userdata['nickname'], userdata['balance'], set(userdata['items']))
            return True
        return False

    def buy(self, item_name=None):
        if not item_name:
            for item in self.items_all:
                if item not in self.user.items:
                    print(item)
            item_name = input('Item name: ')
        if item_name in self.user.items:
            print('Item already owned')
            return False
        if self.user.balance < self.items_all[item_name]:
            print('Not enough currency')
            return False
        if item_name not in self.items_all:
            print('No such item')
            self.ls_all()
            return False
        r = requests.post(SERVER_ADDR + '/item_buy', headers={'token': self.token}, data=item_name)
        if not r.ok:
            print('Buying failed')
            self._update_user_data()
            return False

        self._update_user_data()
        print('Bought {} for {}'.format(item_name, self.items_all[item_name]))
        self.ls()
        return True

    def sell(self, item_name=None):
        if not item_name:
            self.ls()
            item_name = input('Item name: ')
        if item_name not in self.user.items:
            print('Item not owned')
            return False
        r = requests.post(SERVER_ADDR + '/item_sell', headers={'token': self.token}, data=item_name)
        if not r.ok:
            print('Sell failed')
            self._update_user_data()
            return False

        self._update_user_data()
        print('Sold {} for {}'.format(item_name, self.items_all[item_name]))
        self.ls()
        return True

    def get_items_all(self):
        self.items_all = json.loads(requests.get(SERVER_ADDR + '/items_all').content.decode('utf-8'))
        return self.items_all

    def run(self):
        self.send_help()
        self.get_items_all()
        while True:
            print()
            command = input('>')
            print()
            self.handle_input(command)
