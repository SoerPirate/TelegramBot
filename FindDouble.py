import os, sys
import csv

users = []

with open("members.csv", "r", encoding='UTF-8') as f:
    rows = csv.reader(f,delimiter=",",lineterminator="\n")
    for row in rows:
        user = {}
        user['username'] = row[0]
        user['user id'] = int(row[1])
        user['access_hash'] = int(row[2])
        user['name'] = row[3]
        user['group'] = row[4]
        user['group id'] = row[5]
        user['bool'] = row[6]
        users.append(user)

new_users = users
need_delete_dic = set()

for user in users:
    n = 0
    i_find = user.get('user id')
    u_id = users.index(user)
    for n_u in new_users:
        if n <= u_id:
            n+=1
        else:
            target = n_u.get('user id')
            if i_find == target:
                print('НАШЕЛ')
                need_delete_dic.add(new_users.index(n_u))

need_delete = []
for i in need_delete_dic:
    need_delete.append(i)

need_delete.sort()

need_delete.reverse()
    
print('============')
need_delete_for_user = []
for i in need_delete:
    need_delete_for_user.append(i+1)
print('хочу удалить юзеров под номерами:', need_delete_for_user)
print('============')

for n_d in need_delete:
    print('удаляю юзера №', n_d+1)
    w_del = users[n_d]
    print('его id', users[n_d].get('user id'), 'его name', users[n_d].get('name'))
    users.remove(w_del)
    
print('============')
with open("members.csv","w",encoding='UTF-8') as f:
    writer = csv.writer(f,delimiter=",",lineterminator="\n")
    for user in users:
        writer.writerow([user['username'],str(user['user id']),str(user['access_hash']),user['name'],user['group'], user['group id'], user['bool']])      
print('Готово')
