#!/usr/bin/env python3
"""
Напечатать лог, как и когда я что выучил
"""

import datetime
import re
import json
import os.path
import functools
from csv import DictReader
from urllib.parse import urlparse

import urllib3
import click
from colorama import Fore, Style

urllib3.disable_warnings()

CONFIG_FILE = os.path.expanduser('~/.db/wiki/learning-progress-config.json')

class Chunk():
    """Фрагмент знаний"""
    def __init__(self, row, page):
        self.page = page
        self.row = row
        self.added = parse_date(row['Добавил'])
        self.readed = parse_date(row['Изучил'])
        self.delta = self.readed - self.added
    def print(self):
        """Распечатать для отладки"""
        print(' -',
              Fore.GREEN,
              self.page,
              Style.RESET_ALL,
              self.row['Что'],
              '-',
              Fore.RED + self.domain(),
              '-',
              Fore.YELLOW + self.days(),
              Style.RESET_ALL)
    def domain(self):
        """Получить домен"""
        if len(self.row['Ссылка'].strip()):
            return urlparse(self.row['Ссылка']).netloc
        return "..."

    def days(self):
        """Сколько дней заняло"""
        if self.readed == self.added:
            return '0 days'
        return re.sub(',.*', '', str(self.delta))



def url(gid):
    """Получить ссылку на страницу по gid"""
    return config()['base_url'].format(gid)


def parse_date(datestr):
    """Распарсить дату"""
    return datetime.datetime.strptime(datestr, '%d.%m.%Y')

def url_to_dictreader(turl):
    """Распарсить url как csv файл"""
    http = urllib3.PoolManager()
    res = http.request('GET', turl)
    return DictReader(res.data.decode('utf-8').splitlines())


def get_full_learning_log():
    """Получить всю историю обучения"""
    log = []
    for name, gid in config()['pages'].items():
        for row in url_to_dictreader(url(gid)):
            if len(row['Изучил'].strip()) and len(row['Что'].strip()):
                try:
                    log.append(Chunk(row, name))
                except Exception as e:
                    print("Ошибка в разделе {}", name)
                    raise e


    return sorted(log, key=lambda i: i.readed)


@click.group()
def cli():
    """Визуализация прогресса обучения"""
    pass


@cli.command()
def last_days():
    """Сделать всё"""
    log_sorted = get_full_learning_log()
    format_raw_list(list(log_sorted)[-30:])

@cli.command()
def full_log():
    """Напечатать весь лог"""
    log_sorted = get_full_learning_log()
    format_raw_list(list(log_sorted))

def print_header(text):
    """Напечатать заголовок"""
    print(Fore.CYAN, "# ", text, Style.RESET_ALL, sep='')

def format_raw_list(items):
    """Оформить список чанков красиво"""
    prev_date = None
    for itm in items:
        if prev_date != itm.readed:
            if prev_date:
                print()
            print_header(itm.readed.date())
            prev_date = itm.readed
        itm.print()

def check_config():
    """Проверка что есть файл настроек в системе"""
    if not os.path.exists(CONFIG_FILE):
        print("Файл с настройками ({}) не существует".format(CONFIG_FILE))
        exit(1)


@functools.lru_cache()
def config():
    """Получить данные из конфига"""
    return json.loads(open(CONFIG_FILE).read())

if __name__ == '__main__':
    check_config()
    cli()
