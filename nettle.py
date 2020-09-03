#!/usr/bin/python
import json
import os
import time
from datetime import datetime
from multiprocessing import Process

TO_IDENTIFIERS = ['zhangsan', 'zs', 'ALL', 'all']
CC_IDENTIFIERS = ['zhangsan', 'zs', 'Zhang San']
INTERVAL = 10 * 60 # seconds
MUTE_INTERVAL = 60 # seconds
MUTE_COMMANDS = ['mutt', 'tmux']
HOME_DIR = os.environ['HOME']
NEW_MAILS_DIR = os.path.join(HOME_DIR, 'Maildir/.inbox/new')
HISTORY_PATH = os.path.join(HOME_DIR, '.nettle_history')

last_modify = 0
MUTE_COMMANDS_STR = '|'.join(MUTE_COMMANDS)

def check_in(line, identifiers):
    for i in identifiers:
        if i in line:
            return True
    return False

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
        if 'From: ' == line[:6]:
            if check_in(line, CC_IDENTIFIERS):
                return 0, 0
        elif 'Subject: ' == line[:9]:
            break
        elif 'To: ' == line[:4] and check_in(line, TO_IDENTIFIERS):
            return 1, 0
        elif 'Cc: '== line[:4]:
            if check_in(line, CC_IDENTIFIERS):
                return 0, 1
            break
    return 0, 0

def set_number(last_modify, unread_email):
    for file_name in os.listdir(NEW_MAILS_DIR):
        mail_path = os.path.join(NEW_MAILS_DIR, file_name)
        if os.path.getmtime(mail_path) < last_modify:
            continue
        with open(mail_path, 'r') as f:
            content = f.read().split('\n')
            to, cc = get_number(content)
            if to == 1:
                unread_email['to'].append(mail_path)
            elif cc == 1:
                unread_email['cc'].append(mail_path)

def send_message(tty_list, message):
    for i in tty_list:
        os.system('echo "{}" > {}'.format(message, i))

def remove_readed(unread_email):
    unread_email['to'] = filter(os.path.exists, unread_email['to'])
    unread_email['cc'] = filter(os.path.exists, unread_email['cc'])

def should_mute():
    return os.popen(
            'ps -SU $USER|grep -P "({})"|grep -Pv "grep .*-P"'.format(
                MUTE_COMMANDS_STR
                )
            ).read()

def check(unread_email, use_mute=True):
    global last_modify

    if use_mute and should_mute():
        return 'mute'

    tty_list = get_tty_list()
    if not tty_list:
        return 'no_tty'

    remove_readed(unread_email)

    if last_modify < os.path.getmtime(NEW_MAILS_DIR):
        set_number(last_modify, unread_email)

    last_modify = time.time()
    set_history(unread_email, last_modify)

    to_number, cc_number = len(unread_email['to']), len(unread_email['cc'])
    if not unread_email['cc'] and not unread_email['to']:
        return 'none'
    message = '\a\nEmail Notify: To={}; Cc={};'.format(to_number, cc_number)
    send_message(tty_list, message)
    return 'new_email'

def set_history(unread_email, last_modify):
    with open(HISTORY_PATH, 'w') as f:
        f.write(json.dumps(dict(
                unread_email = unread_email,
                last_modify = last_modify
        )))

def get_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH) as f:
            d = json.loads(f.read())
            return d['unread_email'], d['last_modify']
    else:
        return {'cc':[], 'to':[]}, 0

def main():
    global last_modify

    if not TO_IDENTIFIERS and not CC_IDENTIFIERS:
        print 'Set IDENTIFIERS first.'
        return

    unread_email, last_modify = get_history()

    check_result = check(unread_email, False)

    if check_result == 'none':
        print '\nNo new email.'

    while True:
        current = datetime.now()
        if current.weekday() > 4:
            time.sleep(12*60*60)
            continue

        if current.hour < 9 or current.hour > 18:
            time.sleep(60*60)
            continue

        time.sleep(INTERVAL)
        check_result = check(unread_email, last_modify)
        while check_result == 'mute':
            time.sleep(MUTE_INTERVAL)
            check_result = check(unread_email, last_modify)

if __name__ == '__main__':
    pid = str(os.getpid())
    pids = os.popen('pgrep nettle -u $USER').read()
    for i in pids.split('\n'):
        if i and i != pid:
            os.system('kill {}'.format(i))
    Process(target=main).start()
    os.system("kill -KILL {}".format(pid, pid))

