#!/usr/bin/python

import os
import time
from datetime import datetime
from multiprocessing import Process

# Zhang San: zhangsan@xx.com, zs@xx.com

NAME = 'Zhang San'.lower().split(' ')
SHORT_NAME = ''.join([i[0] for i in NAME])
NAME = ''.join(NAME)
INTERVAL = 30 * 60# seconds

NEW_MAILS_DIR = os.path.join(os.environ['HOME'] , 'Maildir/.inbox/new')

def check_in(line):
    return NAME in line or SHORT_NAME in line

def get_tty_list():
    who_result = os.popen('who|grep $USER').read().split('\n')
    return ['/dev/' + i[i.index('pts/'):].split()[0] for i in who_result if i]

def get_number(content):
    i, l = 0, len(content)

    while i < l:
        line = content[i]
        i += 1

        if not line:
            continue

        while line[-1] == ',':
            line += content[i]
            i += 1

        if 'Subject: ' == line[:9]:
            break
        elif 'To: ' == line[:4] and check_in(line):
            return 1, 0
        elif 'Cc: '== line[:4]:
            if check_in(line):
                return 0, 1
            break
    return 0, 0

def set_number(last_modify, unread_mail):
    for file_name in os.listdir(NEW_MAILS_DIR):
        mail_path = os.path.join(NEW_MAILS_DIR, file_name)
        if os.path.getmtime(mail_path) < last_modify - INTERVAL:
            continue
        with open(mail_path, 'r') as f:
            content = f.read().split('\n')
            to, cc = get_number(content)
            if to == 1:
                unread_mail['to'].add(mail_path)
            elif cc == 1:
                unread_mail['cc'].add(mail_path)

def send_message(tty_list, message):
    for i in tty_list:
        os.system('echo "{}" > {}'.format(message, i))

def remove_readed(unread_mail):
    unread_mail['to'] = set(filter(os.path.exists, unread_mail['to']))
    unread_mail['cc'] = set(filter(os.path.exists, unread_mail['cc']))

def check(unread_mail, last_modify):
    remove_readed(unread_mail)
    tty_list = get_tty_list()
    if not tty_list:
        return

    if last_modify < os.path.getmtime(NEW_MAILS_DIR):
        set_number(last_modify, unread_mail)

    to_number, cc_number = len(unread_mail['to']), len(unread_mail['cc'])
    if not (unread_mail['cc'] | unread_mail['to']):
        return False

    message = '\a\nEmail Notify: To={}; Cc={};'.format(to_number, cc_number)
    send_message(tty_list, message)
    return True

def main():
    if not NAME:
        print 'Set NAME first.'
        return

    current = datetime.now()
    unread_mail = {'cc':set(), 'to':set()}
    last_modify = 0

    if not check(unread_mail, last_modify):
        print '\nNo new email.'

    while True:
        if 7 < current.hour < 19:
            time.sleep(INTERVAL)
            check(unread_mail, last_modify)
            last_modify = time.time()
        else:
            time.sleep(60*60)

if __name__ == '__main__':
    pids = os.popen('pgrep nettle -u $USER').read()
    pids = [i for i in  pids.split('\n') if i][:-1]
    for i in sorted(pids):
        os.system('kill {}'.format(i))
    Process(target=main).start()
    os.system("kill -KILL {}".format(os.getpid(), os.getpid()))
