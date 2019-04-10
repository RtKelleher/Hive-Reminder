#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This script queries The Hive API for open cases and generates a email reminder
for users who exceed seven days since opened"""
from __future__ import print_function
import email.message
import datetime
import smtplib
import time
from thehive4py.api import TheHiveApi
from thehive4py.query import Eq
#Configuration
server_address = ''
api_credentials = ''
smtp_server = ''
ignore_list = []
domain = ''

def main():
    """Returns global dictionary data object

    Calls The Hives API then checks if a result was returned.
    If a result was returned, check the results and time since the result was created.
    """
    data = {}
    api = TheHiveApi(server_address, api_credentials)
    r = api.find_cases(
        query=Eq('status', 'Open'),
        range='all',
        sort=[]
        )
    if r.status_code == 200:
        i = 0
        data = {}
        while i < len(r.json()):
            check_date = datetime.date.today() - datetime.timedelta(days=7)
            if (r.json()[i]['createdAt']/1000) < time.mktime(check_date.timetuple()):
                tasks = api.get_case_tasks(r.json()[i]['id'])
                inc, cnt = 0, 0
                while inc < len(tasks.json()):
                    if (tasks.json()[inc]['status'] == ('Waiting')) or (
                            tasks.json()[inc]['status'] == ('InProgress')):
                        cnt += 1
                    inc += 1
                data[(i)] = {
                    'id' : r.json()[i]['id'],
                    'owner' : r.json()[i]['owner'],
                    'createdAt' : (
                        time.strftime(
                            '%m/%d/%Y %H:%M:%S',
                            time.gmtime(r.json()[i]['createdAt']/1000.))),
                    'totalTasks' : len(tasks.json()),
                    'pendingTasks' : cnt
                    }
            i += 1
    build(data)

def build(data):
    """Creates email for each key in data object

    Builds msg.html for each key in dictionary.
    """
    for key in data:
        if data[key]['owner'] not in ignore_list:
            msg = email.message.Message()
            msg.add_header('Content-Type', 'text/html')
            msg['Subject'] = 'The Hive Tasking Reminder'
            msg['From'] = 'SIRP-Reminders@' + domain
            msg['To'] = data[key]['owner'] + '@' + domain
            with open('msg.html', 'r') as f:
                message = f.read()
            fmessage = message.format(
                Name=str(data[key]['owner'].split('.')[0]).capitalize(),
                Case=str(data[key]['id'])
                )
            print(msg['From'])
            print(msg['To'])
            msg.set_payload(fmessage)
            smtp = smtplib.SMTP(smtp_server)
            smtp.starttls()
            smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
            smtp.quit()

main()
exit()
