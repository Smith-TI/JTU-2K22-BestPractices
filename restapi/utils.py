from datetime import datetime
import logger
from time import time
import urllib.request
import concurrent.futures

from restapi.constants import LOG_FILES_READER_TIMEOUT


def normalize(expense) -> list:
    '''Normalize the balances for a user'''
    starttime = int(time.time() * 1000.0)
    user_balances = expense.users.all()
    dues = {}
    for user_balance in user_balances:
        dues[user_balance.user] = dues.get(user_balance.user, 0) + user_balance.amount_lent \
            - user_balance.amount_owed
    dues = [(k, v) for k, v in sorted(dues.items(), key=lambda item: item[1])]
    start = 0
    end = len(dues) - 1
    balances = []
    while start < end:
        amount = min(abs(dues[start][1]), abs(dues[end][1]))
        user_balance = {"from_user": dues[start][0].id,
                        "to_user": dues[end][0].id, "amount": amount}
        balances.append(user_balance)
        dues[start] = (dues[start][0], dues[start][1] + amount)
        dues[end] = (dues[end][0], dues[end][1] - amount)
        if dues[start][1] == 0:
            start += 1
        else:
            end -= 1
    endtime = int(time.time() * 1000.0)
    logger.info(f'Normalized expense in {endtime - starttime}ms')
    return balances


def sort_logs_by_time_stamp(logs) -> list:
    '''Sort logs by Time Stamp'''
    data = []
    for log in logs:
        data.append(log.split(" "))
    data = sorted(data, key=lambda elem: elem[1])
    return data


def response_format(raw_data) -> list:
    '''Format a response'''
    response = []
    for timestamp, data in raw_data.items():
        entry = {'timestamp': timestamp}
        logs = []
        data = {k: data[k] for k in sorted(data.keys())}
        for exception, count in data.items():
            logs.append({'exception': exception, 'count': count})
        entry['logs'] = logs
        response.append(entry)
    return response


def aggregate_logs(cleaned_logs) -> dict:
    '''Aggregate cleaned logs'''
    data = {}
    for log in cleaned_logs:
        [key, text] = log
        value = data.get(key, {})
        value[text] = value.get(text, 0)+1
        data[key] = value
    return data


def clean_up_logs(logs) -> list:
    '''Clean up logs'''
    result = []
    for log in logs:
        [_, timestamp, text] = log
        text = text.rstrip()
        timestamp = datetime.utcfromtimestamp(int(int(timestamp)/1000))
        hours, minutes = timestamp.hour, timestamp.minute
        key = ''

        if minutes >= 45:
            if hours == 23:
                key = "{:02d}:45-00:00".format(hours)
            else:
                key = "{:02d}:45-{:02d}:00".format(hours, hours+1)
        elif minutes >= 30:
            key = "{:02d}:30-{:02d}:45".format(hours, hours)
        elif minutes >= 15:
            key = "{:02d}:15-{:02d}:30".format(hours, hours)
        else:
            key = "{:02d}:00-{:02d}:15".format(hours, hours)

        result.append([key, text])
        print(key)

    return result


def multi_threaded_url_reader(urls) -> list:
    """Read multiple files through HTTP"""
    result = []

    def download(url):
        with urllib.request.urlopen(url, timeout=LOG_FILES_READER_TIMEOUT) as conn:
            data = conn.read()
            data = data.decode('utf-8')
            result.extend(data.split("\n"))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download, urls)

    result = sorted(result, key=lambda elem: elem[1])
    return result
