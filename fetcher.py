#!/usr/bin/python3

import datetime
import json
import logging
import os
import re
import sys
import urllib.request as url

import database_lib.database as db

try:
    from bs4 import BeautifulSoup
except ImportError as e:
    print(e, "Hint: use pip3 install beautifulsoup4 html5lib lxml")
    sys.exit(1)

__VERSION__ = '0.1'

##################
# PARAMETER BLOCK
##################

# Log params:
LOG_DIR = './'
LOG_FNAME = 'test.log'

# DB params:
DB_CONTYPE = 'network'
DB_HOST = '192.168.1.104'
DB_PORT = '5432'
DB_NAME = 'account_stat'
DB_USER = 'wargaming'
DB_PASSWD = 'W@rGam1ing!'

# Tables:
W_ACCOUNTS = 'w_accounts'
W_STAT = 'w_statistics'
W_SEC_BAT = 'w_second_battery'
W_MAIN_BAT = 'w_main_battery'
W_RAMM = 'w_ramming'
W_AIRCR = 'w_aircraft'
W_TORP = 'w_torpedoes'

# Main params:
APP_ID = '450cbeb1caaee4965ee516cdeb38d8f1'
BASE_URL = 'https://api.worldofwarships.ru/wows/'
ACC_FIELDS = 'nickname'\
             '%2C+hidden_profile'\
             '%2C+private'\
             '%2C+created_at'\
             '%2C+last_battle_time'\
             '%2C+statistics.pvp.xp'\
             '%2C+statistics.pvp.battles'\
             '%2C+statistics.pvp.survived_battles'\
             '%2C+statistics.pvp.draws'\
             '%2C+statistics.pvp.survived_wins'\
             '%2C+statistics.pvp.frags'\
             '%2C+statistics.pvp.damage_scouting'\
             '%2C+statistics.pvp.wins'\
             '%2C+statistics.pvp.damage_dealt'\


#####################
# FUNCTION & CLASSES
#####################


class StatGetter(object):
    def __init__(self, db, log):
        self.log = log
        self.db = db

    def get_acc_ids(self, first_id, last_id):
        self.db.do_query("SELECT id FROM %s "\
                         "WHERE id >= '%s' "\
                         "AND id <= '%s'" % (
                             W_ACCOUNTS, first_id, last_id))
        res = self.db.cursor.fetchall()
        if res and res[0]:
            return res
        else:
            return False


class StatFetcher(object):
    def __init__(self, app_id, acc_id, log):
        self.log = log
        self.start_time = datetime.datetime.now()
        self.acc_id = acc_id
        self.ACC_URL = BASE_URL+'account/info/'\
                                '?application_id='+app_id+''\
                                '&account_id='+acc_id+''\
                                '&fields='+ACC_FIELDS

    def get_acc_stat(self):
        request_time = datetime.datetime.now()
        try:
            response = url.urlopen(self.ACC_URL)
        except Exception as e:
            self.log.error(e)
            return False

        resp_time = datetime.datetime.now() - request_time
        # self.log.info('Response from WoWSH acc received in %s'
        #              % resp_time)

        raw_string = response.read().decode('utf-8')
        json_data = json.loads(raw_string)
        try:
            stat_dict = json_data['data'][self.acc_id]
            return stat_dict
        except Exception as e:
            self.log.error("%s" % json_data)
            exit(1)


class StatAccount(object):
    def __init__(self, app_id, acc_id, log, db):
        self.fetcher = StatFetcher(app_id, acc_id, log)
        self.log = log
        self.stat = {}
        self.db = db
        self.acc_id = acc_id
        self.now = datetime.datetime.now()

    def get_info(self):
        self.stat = self.fetcher.get_acc_stat()
        # print(self.stat)

    def __store_w_acc(self):
        self.db.do_query("SELECT * FROM %s "\
                         "WHERE id = '%s'" % (W_ACCOUNTS, self.acc_id))
        res = self.db.cursor.fetchone()

        if self.stat['hidden_profile'] or self.stat['private']:
            hidden = True
        else:
            hidden = False

        # print(res)
        if res:
            self.db.do_query("UPDATE %s "\
                             "SET modifydate = '%s', "\
                             "nickname = '%s', "\
                             "created_at = '%s', "\
                             "last_battle_time = '%s', "\
                             "hidden = '%s' "\
                             "WHERE id = '%s'" % (
                                 W_ACCOUNTS,
                                 self.now,
                                 self.stat['nickname'],
                                 self.stat['created_at'],
                                 self.stat['last_battle_time'],
                                 hidden,
                                 self.acc_id))
        else:
            self.db.do_query("INSERT INTO %s "\
                             "(id, modifydate, nickname, created_at, "\
                             "logout_at, hidden) VALUES "\
                             "('%s', '%s', '%s', '%s', '%s', '%s')" % (
                                 W_ACCOUNTS,
                                 self.acc_id,
                                 self.now,
                                 self.stat['nickname'],
                                 self.stat['created_at'],
                                 self.stat['last_battle_time'],
                                 hidden))

    def __store_w_stat(self):
        pvp_stat = self.stat['statistics']['pvp']

        self.db.do_query("SELECT count(*) FROM %s "\
                         "WHERE acc_id = '%s'" % (W_STAT, self.acc_id))
        res = self.db.cursor.fetchone()
        if res and res[0]:
            self.db.do_query("UPDATE %s SET "\
                             "modifydate = '%s', "\
                             "xp = '%s', "\
                             "battles = '%s', "\
                             "survived_battles = '%s', "\
                             "draws = '%s', "\
                             "frags = '%s', "\
                             "damage_scouting = '%s', "\
                             "wins = '%s', "\
                             "damage_dealt = '%s' "\
                             "WHERE acc_id = '%s'" % (
                                 W_STAT,
                                 self.now,
                                 pvp_stat['xp'],
                                 pvp_stat['battles'],
                                 pvp_stat['survived_battles'],
                                 pvp_stat['draws'],
                                 pvp_stat['frags'],
                                 pvp_stat['damage_scouting'],
                                 pvp_stat['wins'],
                                 pvp_stat['damage_dealt'],
                                 self.acc_id))
        else:
            self.db.do_query("INSERT INTO %s "\
                             "(acc_id, "\
                             "modifydate, "\
                             "xp, "\
                             "battles, "\
                             "survived_battles, "\
                             "draws, "\
                             "frags, "\
                             "damage_scouting, "\
                             "wins, "\
                             "damage_dealt) "
                             "VALUES "\
                             "('%s', '%s', '%s', "\
                             "'%s', '%s', '%s', '%s', "\
                             "'%s', '%s', '%s')" % (
                                 W_STAT,
                                 self.acc_id,
                                 self.now,
                                 pvp_stat['xp'],
                                 pvp_stat['battles'],
                                 pvp_stat['survived_battles'],
                                 pvp_stat['draws'],
                                 pvp_stat['frags'],
                                 pvp_stat['damage_scouting'],
                                 pvp_stat['wins'],
                                 pvp_stat['damage_dealt']))

    def store_info(self):
        if self.stat and self.stat['hidden_profile']:
            return False
        elif not self.stat:
            self.log.warning('%s returned %s, delete this id' % (
                                 self.acc_id, self.stat))
            self.db.do_query("DELETE FROM %s WHERE id = '%s'" % (
                                 W_ACCOUNTS, self.acc_id))
            return False

        self.__store_w_acc()

        self.__store_w_stat()


def main():
    pid = os.getpid()

    log_path = LOG_DIR+LOG_FNAME
    row_format = '%(asctime)s [%(levelname)s] %(message)s'
    logging.basicConfig(format=row_format, filename=log_path,
                        level=logging.INFO)
    log = logging.getLogger('main')
    log.info('%s start' % pid)

    acc_db = db.DatBaseObject(DB_NAME)
    acc_db.set_log(log)
    acc_db.get_connect(con_type=DB_CONTYPE, host=DB_HOST,
                       pg_port=DB_PORT, user=DB_USER,
                       passwd=DB_PASSWD)

    input_str = sys.stdin.read()
    data = input_str.split()
    del input_str
    i = 0
    for d in data:
        data[i] = d.strip(',()][')
        i += 1

    for acc_id in data:
        account = StatAccount(APP_ID, acc_id, log, acc_db)
        account.get_info()
        account.store_info()

    log.info('%s done' % pid)


if __name__ == '__main__':
    main()
