from telethon.sync import TelegramClient
from telethon import utils
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon import connection
from telethon.tl.types import InputPeerUser # spam
from telethon.errors.rpcerrorlist import PeerFloodError # spam
from telethon import functions, types # spam (перепарсить hash юзера)
import os, sys
import configparser
import csv
import time
import binascii
import subprocess
import http.client
import random
import datetime

# задержка (для текстовых сообщений)
SLEEP_TIME = 25

# стартовый ip
conn = http.client.HTTPConnection("ifconfig.me")
conn.request("GET", "/ip")
current_ip = conn.getresponse().read()
print(current_ip, '\n')

# все vpn адреса
vpn_adresses = []
with open('vpn_adresses.csv', "r", encoding='UTF-8') as f:
    rows = csv.reader(f,delimiter=",",lineterminator="\n")
    for row in rows:
        vpn_adresses.append(row)
print(vpn_adresses, '\n')

# текущий vpn - имя и номер
current_vpn_adress = ''
current_vpn_num = 0

# текущий статус vpn
current_vpn_status = False

# текущий user
user_num = 1

# tg сессия
client = ''

# текущий статус авторизации в tg
current_tg_login = False

# выбор команды в консоли для работы (парсер, спамер и т.д.)
command = False

# получать текущий месяц автоматом
current_month = 6


''' БАННЕРЫ ДЛЯ ПЕРЕХОДОВ МЕЖДУ ПУНКТАМИ МЕНЮ '''
def banner():
    print(f"""
░░░░░░░░░ ПОДКЛЮЧАЕМ VPN + ЛОГИНИМСЯ В TG ░░░░░░░░
        """)

def banner_p():
    print(f"""
░░░░░░░░░ ПАРСЕР ░░░░░░░░
        """)

def banner_s():      
    print(f"""
░░░░░░░░░ РАССЫЛКА СООБЩЕНИЙ ░░░░░░░░
        """)
    
''' ПОДКЛЮЧЕНИЕ К VPN '''
def vpn_onn(current_ip, current_vpn_adress, current_vpn_num, current_vpn_status):
    if current_vpn_num < len(vpn_adresses):
        current_vpn_adress_1 = str(vpn_adresses[current_vpn_num])
        current_vpn_adress = current_vpn_adress_1[2:-2]
        current_vpn_num+=1
        print(str(current_vpn_adress), '\n')
        try:
            subprocess.run('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command connect ' + str(current_vpn_adress)) 
            print('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command connect ' + str(current_vpn_adress) + '\n')
            print("включили vpn\n")
        except KeyError:
            print("vpn отлетел, остановись!\n")

        print("ждем {} секунд...".format(SLEEP_TIME))
        print('')
        time.sleep(25)     

        conn = http.client.HTTPConnection("ifconfig.me")
        conn.request("GET", "/ip")
        vpn_ip = conn.getresponse().read()
        print(vpn_ip)

        if current_ip == vpn_ip:
            print("vpn НЕ подключен, остановись!\n") # вызываем себя же
            subprocess.run('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command disconnect ' + current_vpn_adress)  
            print("ждем {} секунд...".format(SLEEP_TIME))
            print('')
            time.sleep(10)
            return vpn_onn(current_ip, current_vpn_adress, current_vpn_num, current_vpn_status)
        else:
            current_ip = vpn_ip
            current_vpn_status = True
            print('vpn включен, можно работать\n')
            return current_ip, current_vpn_adress, current_vpn_num, current_vpn_status
    else:
        print('vpn адреса закончились')
        subprocess.run('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command disconnect ' + current_vpn_adress)
        sys.exit(1)

''' АВТОРИЗАЦИЯ В TG '''
def tg_login(user_num, client, current_vpn_adress):
    print('пытаюсь залогиниться в телеге')
    cpass = configparser.RawConfigParser()
    cpass.read('config.data')

    try:
        api_id = cpass[str(user_num)]['id']
        api_hash = cpass[str(user_num)]['hash']
        phone = cpass[str(user_num)]['phone']
        tg_name = cpass[str(user_num)]['tg_name']
        print(tg_name, phone, api_id, api_hash)
        
        client = TelegramClient(phone, api_id, api_hash)
    except KeyError:
        print('прошли всех юзеров')
        subprocess.run('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command disconnect ' + current_vpn_adress)
        print('выключаю vpn')
        sys.exit(1)
        
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone)
        client.sign_in(phone, input('Возможно этот акк умер [ИЛИ] это первый логин с данного акка, Enter the code: '))

    print('залогинился в tg\n')
    user_num+=1
    
    return user_num, client, tg_name

''' ПАРСЕР '''
def pars(command):
    # получаем диалоги
    banner_p()
    chats = []
    last_date = None
    chunk_size = 200
    groups=[]
     
    result = client(GetDialogsRequest(
                 offset_date=last_date,
                 offset_id=0,
                 offset_peer=InputPeerEmpty(),
                 limit=chunk_size,
                 hash = 0
             ))
    chats.extend(result.chats)
     
    for chat in chats:
        try:
            if chat.megagroup== True:
                groups.append(chat)
        except:
            continue

    all_participants = []

    print('Вот все доступные чаты для парсинга:')
    for g in groups:
        print('[X] ' + g.title)

    print('')

    for g in groups:
        print('Берем \"' + g.title + '\" ?')
        if input() == 'y':
            target_group=g  
            print('Выкачиваю юзеров из: ' + g.title + '\n')
            time.sleep(1)
            all_participants = client.get_participants(target_group, aggressive=True)   
            print('Открываю файл для записи\n')
            print('Отбираю ненужных юзеров\n')
            time.sleep(1)

            off = 0
            danger_man = 0
            last_m = 0
            month = 0
            current_month = 7    # месяц для отбора давности офлайна
                    
            with open("members.csv","a",encoding='UTF-8') as f:
                writer = csv.writer(f,delimiter=",",lineterminator="\n")

                for user in all_participants:
                    if user.username:
                        username= user.username
                    else:
                        username= "anonymous"
                       
                    if user.first_name:
                        first_name= user.first_name
                    else:
                        first_name= ""
                    if user.last_name:
                        last_name= user.last_name
                    else:
                        last_name= ""
                    name= (first_name + ' ' + last_name).strip()
                                                                          
                    if (user.restricted == True or user.deleted == True or user.bot == True or user.support == True or user.scam == True):
                        print('Danger man : ', name, user.id)
                        danger_man+=1
                        continue

                    user_stat = str(user.status)
                    
                    if user_stat == 'UserStatusLastMonth()':
                        print('LastMonth : ', name, user.id)
                        last_m +=1
                        continue
                    
                    if 'Offline' in user_stat:
                        month = int(user_stat[53:54])
                        if month != current_month:
                            print('Offline : ', name, user.id)
                            off+=1
                            continue

                    writer.writerow([username, user.id, user.access_hash, name, target_group.title, target_group.id, 'yes','','',''])

            print('')
            print('Исключил: danger', danger_man, 'last month', last_m, 'offline', off)
            print('')
            print('Сохраняю в файл\n')

        else:
            print('')

    print('парсинг окончен!')
    command = False
    return command

''' РАССЫЛКА СООБЩЕНИЙ '''
def spam(command, client, current_vpn_adress, current_ip, current_vpn_num, current_vpn_status, user_num, tg_name):
    banner_s()

    need_change_account = False

    # fake pars
    print('fake pars BEGIN\n')
    
    chats = []
    last_date = None
    chunk_size = 200
    groups=[]
     
    result = client(GetDialogsRequest(
                 offset_date=last_date,
                 offset_id=0,
                 offset_peer=InputPeerEmpty(),
                 limit=chunk_size,
                 hash = 0
             ))
    chats.extend(result.chats)
     
    for chat in chats:
        try:
            if chat.megagroup== True:
                groups.append(chat)
        except:
            continue
        
    all_participants = []
    for g in groups:
        all_participants = client.get_participants(g, aggressive=True)

    print('fake pars END\n')
            
    users = []
    with open("members.csv", encoding='UTF-8') as f:
        rows = csv.reader(f,delimiter=",",lineterminator="\n")
        try:
            for row in rows:
                user = {}
                user['username'] = row[0]
                user['id'] = int(row[1])
                user['access_hash'] = int(row[2])
                user['name'] = row[3]
                user['group'] = row[4]
                user['group id'] = row[5]
                user['bool'] = row[6]
                # кто спамил       
                user['tg_name'] = row[7]
                user['current_vpn_adress'] = row[8]
                user['date'] = row[9]
                users.append(user)
        except KeyError:
            print('файл с людьми пустой KeyError')
        except LookupError:
            print('файл с людьми пустой LookupError')
            command = False
            return command, client, current_vpn_adress, current_ip, current_vpn_num, current_vpn_status, user_num
     
    message = "всю жизнь я пытаюсь выразить что-то между пьяным воем бомжа и вмещающем мудрость земли афоризмом"     
    print('')
    
    error = ''
    n = 0
    n_n = 2        # сколько сообщений отправлять
    for user in users:
        if n < n_n:
            if user['bool'] == 'yes': 
                try:                    
                    print(user['access_hash'])
                    print('')
                    entity = client.get_entity(user['id'])
                    result_array = str(entity).split(", ")
                    print('получил entity')
                    print(result_array)
                    
                    x = 0
                    for r in result_array:
                        if x == 16:
                            new_access_hash_full = r
                            new_access_hash = new_access_hash_full[12:]
                            x+=1
                        else:
                            x+=1

                    print('новый hash\n')
                    print(new_access_hash) 
                    
                    receiver = InputPeerUser(user['id'],int(new_access_hash)) 
                    client.send_message(receiver, message.format(user['id']))

                    print("пишу сообщение юзеру:", user['name'])
                    
                    print("пауза, чтобы tg не ругался {} секунд".format(SLEEP_TIME))
                    time.sleep(30)
                    # помечаем что этому юзеру отослали смс
                    user['bool'] = 'no'
                    # кто спамил
                    user['tg_name'] = tg_name
                    user['current_vpn_adress'] = current_vpn_adress
                    user['date'] = str(datetime.datetime.now())
                    # успешно отправили смс
                    n+=1        
                except PeerFloodError:
                    print("[!] Флуд телеги, проверься ботом @spam_bot")
                    need_change_account = True
                    break
                except Exception as e:
                    print("[!] Error:", e)
                    break

            else:
                print('пропускаем юзера [', user['name'], '] уже спамили или он в нашем стоп-листе')
        else:
            print('лимит сообщений, надо менять акк и vpn')
            need_change_account = True
            break

    with open("members.csv","w",encoding='UTF-8') as f:
        writer = csv.writer(f,delimiter=",",lineterminator="\n")

        for user in users:
            writer.writerow([user['username'],str(user['id']),str(user['access_hash']),user['name'],user['group'], user['group id'], user['bool'], user['tg_name'], user['current_vpn_adress'], user['date']])

    print('Сохранили результат спама в табличку')

    if n != n_n:          
        print('это был конец файла, надо еще парсить')
        print('отправлено', n, 'из', n_n, 'сообщений')
        
        client.disconnect()
        print('отключились от tg\n')

        print("ждем {} секунд...".format(SLEEP_TIME))
        print('')
        time.sleep(10)
        
        print('after disconnect tg')
        print(user_num, client)
        
        subprocess.run('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command disconnect ' + current_vpn_adress)
        print("отключили vpn\n")
        command = False
        return command, client, current_vpn_adress, current_ip, current_vpn_num, current_vpn_status, user_num
    
    if need_change_account == True:
        # дисконект + функц впн\акк + рекурсия спама
        print('отправлено', n, 'из', n_n, 'сообщений\n')
        print('вот теперь меняю акк и vpn')
        
        client.disconnect()
        print('отключились от tg\n')

        print("ждем {} секунд...".format(SLEEP_TIME))
        print('')
        time.sleep(10)

        subprocess.run('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command disconnect ' + current_vpn_adress)
        print("отключили vpn\n")

        print("ждем {} секунд...".format(SLEEP_TIME))
        print('')
        time.sleep(10)
        
        current_ip, current_vpn_adress, current_vpn_num, current_vpn_status, user_num, client, tg_name = change_profile(current_ip, current_vpn_adress, current_vpn_num, current_vpn_status, user_num, client)
        
        return spam(command, client, current_vpn_adress, current_ip, current_vpn_num, current_vpn_status, user_num, tg_name)

''' ПОДКЛЮЧЕНИЕ К VPN И ЛОГИН В TG '''   
def change_profile(current_ip, current_vpn_adress, current_vpn_num, current_vpn_status, user_num, client):
    banner()
    # вызываем def vpn_onn чтобы найти vpn
    print('пробую подключить vpn')
    current_ip, current_vpn_adress, current_vpn_num, current_vpn_status = vpn_onn(current_ip, current_vpn_adress, current_vpn_num, current_vpn_status)

    # наши данные после включения vpn
    print(current_ip, '\n')
    print(current_vpn_adress, '\n')
    print(current_vpn_num, '\n')
    print(current_vpn_status, '\n')

    # если мы под vpn то идем дальше
    if current_vpn_status == True:
        print('before login tg')
        print(user_num, client)
        # вызываем def tg_login
        user_num, client, tg_name = tg_login(user_num, client, current_vpn_adress)
        # под кем мы залогинены
        print(user_num, client)
    else:
        print('нельзя работать без vpn')
        sys.exit(1)

    return current_ip, current_vpn_adress, current_vpn_num, current_vpn_status, user_num, client, tg_name

''' ГЛАВНОЕ МЕНЮ '''
banner()

user_num = int(input('введи номер акка TG: '))

current_ip, current_vpn_adress, current_vpn_num, current_vpn_status, user_num, client, tg_name = change_profile(current_ip, current_vpn_adress, current_vpn_num, current_vpn_status, user_num, client)
    
while command == False:
    print(f"""
    доступные команды:   
    pars
    spam
    exit 
    """)
    
    current_command = input('введите команду: ')
    
    if current_command == 'pars':
        command = True
        command = pars(command)
    elif current_command == 'spam':
        command = True
        command, client, current_vpn_adress, current_ip, current_vpn_num, current_vpn_status, user_num = spam(command, client, current_vpn_adress, current_ip, current_vpn_num, current_vpn_status, user_num, tg_name)
    elif current_command == 'exit':
        command = True
        print('завершение работы')
        client.disconnect()
        time.sleep(2)
        subprocess.run('"c:\Program Files\OpenVPN\\bin\openvpn-gui.exe" --command disconnect ' + current_vpn_adress)
        sys.exit(1)












