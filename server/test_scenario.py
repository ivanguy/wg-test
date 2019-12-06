#!/usr/bin/env python3
import requests

s = 'http://localhost:8080'
r = requests.post(s + '/login', data='tester')
print(r)
userdata = r.content.decode('utf-8')
print(userdata)
token = r.headers['token']
print(token)

print('/buy_item')
r = requests.post(s + '/item_buy', headers={'token': token}, data='uzi')
print(r)
print(r.content.decode('utf-8'))
r = requests.get(s + '/items_my', headers={'token': token})
print('my items:\n' + r.content.decode('utf-8'))
r = requests.get(s + '/items_all', headers={'token': token})
print('all items:\n' + r.content.decode('utf-8'))

print('/sell_item')
r = requests.post(s + '/item_sell', headers={'token': token}, data='uzi')
print(r)
print(r.content.decode('utf-8'))
r = requests.get(s + '/logout', headers={'token': token})
print(r)
r = requests.get(s + '/items_my', headers={'token': token})
print('my items:\n' + r.content.decode('utf-8'))
