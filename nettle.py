#!/usr/bin/python

import os
import time
from datetime import datetime
from multiprocessing import Process

email = 'zyh'
new_mails_dir = os.environ['HOME'] + '/Maildir/.inbox/new'


def check():
    who_result = os.popen('who|grep $USER').read().split('\n')
    tty_list = ['/dev/' + i[i.index('pts/'):].split()[0] for i in who_result if i]
    if not tty_list:
        return
    cc_number = 0
    to_number = 0
    for file_name in os.listdir(new_mails_dir):
        mail_path = os.path.join(new_mails_dir, file_name)
        with open(mail_path, 'r') as f:
            content = f.read()
            if '\nTo: ' in content:
                to_index = content.index('\nTo: ') + 5
                if email in content[to_index:][:content[to_index :].index('\n')]:
                    to_number += 1
            if '\nCc: ' in content:
                cc_index = content.index('\nCc: ') + 5
                if email in content[cc_index:][:content[cc_index :].index('\n')]:
                    cc_number += 1
    if not (cc_number | to_number):
        return
    message = 'Email Notify: To={}; Cc={};'.format(to_number, cc_number)
    for i in tty_list:
        os.system('echo "\n{}" > {}'.format(message, i))

def main():
    if not email:
        print 'Set email first.'
        return
    current = datetime.now()
    while True:
        if 8 < current.hour < 21:
            check()
            # per 30 min check
            time.sleep(30*60)
        else:
            time.sleep(60*60)

if __name__ == '__main__':
    Process(target=main).start()
    os.system("kill -KILL {}".format(os.getpid(), os.getpid()))
