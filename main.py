#!/usr/bin/python3

import argparse
import datetime
import logging
import subprocess

import database_lib.database as db


__VERSION__ = '0.1'


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Wargaming WoWSH")
    parser.add_argument("-L", "--log", dest="logfile",
                        default='./test.log',
                        help="path to logfile", metavar="FILE")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--full", action="store_true",
                       help="get info for all accounts")
    group.add_argument("-a", "--active", action="store_true",
                       help="get info for active accounts")
    group.add_argument("-t", "--top", action="store_true",
                       help="get info for top accounts")
    group.add_argument("-n", "--new", action="store_true",
                       help="get info for fresh accounts")
    group.add_argument("-V", "--version", action="version",
                       version=__VERSION__, help="show version and exit")

    return parser.parse_args()


args = parse_cli_args()

##################
# PARAMETER BLOCK
##################

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

# Main params:
THREAD_NUM = 20

# Id's selection thresholds:
BATTLE_PERIOD = 2592000  # in sec, 30 days
MIN_BATTLE_NUM = 500
MIN_WINS = 500
TOP_LIMIT = 10000
ID_NUM_LIMIT = 10000


class GetAccInfo(object):
    def __init__(self, db, log):
        self.db = db  # Must be database object
        self.log = log  # Must be logging object
        self.get_id_sql = ""
        # self.tt is last battle time threshold,
        # we don't count an account if user didn't play
        # for the BATTLE_PERIOD:
        self.tt = datetime.datetime.now().timestamp() - BATTLE_PERIOD

    def get_new_ids(self):
        """Get fresh account ids
        """
        self.get_id_sql = "SELECT a.id FROM %s AS a "\
                          "WHERE a.created_at = '0' "\
                          "LIMIT %s" % (W_ACCOUNTS, ID_NUM_LIMIT)
        self.__get_info()

    def get_all_ids(self):
        """Get all accout ids
        """
        self.get_id_sql = "SELECT a.id FROM %s AS a" % W_ACCOUNTS
        self.__get_info()

    def get_active_ids(self):
        """Get active account ids
        """
        self.get_id_sql = "SELECT a.id FROM %s AS a "\
                          "LEFT JOIN %s AS w ON a.id = w.acc_id "\
                          "WHERE w.battles >= %s "\
                          "AND NOT a.hidden "\
                          "AND a.last_battle_time >= %s" % (
                              W_ACCOUNTS, W_STAT, MIN_BATTLE_NUM,
                              self.tt)
        self.__get_info()

    def get_top_ids(self):
        """Get top account ids
        """
        self.get_id_sql = "SELECT a.id FROM %s AS a "\
                          "LEFT JOIN %s AS w ON a.id = w.acc_id "\
                          "WHERE w.battles >= %s "\
                          "AND w.wins >= %s "\
                          "AND a.last_battle_time >= %s "\
                          "AND NOT a.hidden "\
                          "ORDER BY w.wins DESC "\
                          "LIMIT %s" % (W_ACCOUNTS, W_STAT,
                                        MIN_BATTLE_NUM, MIN_WINS,
                                        self.tt, TOP_LIMIT)
        self.__get_info()

    def __get_info(self):
        self.db.do_query(self.get_id_sql)
        res = self.db.cursor.fetchall()
        if not res or not res[0]:
            self.log.error("'%s' returns %s" % (
                           get_id_sql, res))
            exit(1)

        acc_num = len(res)
        print(acc_num)  # for debug

        thread_portion = (acc_num // THREAD_NUM) + 1

        start_id = 0
        fin_id = thread_portion
        for thread in range(0, THREAD_NUM):
            i = res[start_id:fin_id]
            input_str = str(i).encode()

            p = subprocess.Popen(['./fetcher.py'],
                                 stdin=subprocess.PIPE)
            p.stdin.write(input_str)

            start_id = fin_id
            fin_id += thread_portion


def main():
    row_format = '%(asctime)s [%(levelname)s] %(message)s'
    logging.basicConfig(format=row_format, filename=args.logfile,
                        level=logging.INFO)
    log = logging.getLogger('main')

    acc_db = db.DatBaseObject(DB_NAME)
    acc_db.set_log(log)
    acc_db.get_connect(con_type=DB_CONTYPE, host=DB_HOST,
                       pg_port=DB_PORT, user=DB_USER,
                       passwd=DB_PASSWD)

    info = GetAccInfo(acc_db, log)

    if args.top:
        info.get_top_ids()

    elif args.new:
        info.get_new_ids()

    elif args.active:
        info.get_active_ids()

    elif args.full:
        info.get_all_ids()


if __name__ == '__main__':
    main()
