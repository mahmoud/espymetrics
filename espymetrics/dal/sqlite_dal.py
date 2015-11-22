# -*- coding: utf-8 -*-
"""The sqlite-based DAL writes data to a single-file SQL database
powered by Python's built-in sqlite3 module. The schema is based on a
prototype message found in dal/common.py.

The advantages of the SQLite DAL are:

* Faster loading - SQLite can efficiently seek to relevant data
* Efficient storage - SQLite is a binary format, may be more compact than text
* More flexible queries - SQL is powerful and easy to use

Drawbacks:

* Not human readable - Binary format makes it harder to read/grep
* More complex - More logic = more work = more time/resources?
"""

import sqlite3


_MISSING = object()
SEP = '$'  # '$' is valid in sqlite column names, no escaping required

TABLE_NAME = 'on_import_data'
CREATE_TABLE = ('CREATE TABLE IF NOT EXISTS ' + TABLE_NAME +
                '(id integer primary key, ' +
                'hostfqdn, hostname, python$argv, python$bin, ' +
                'python$build_date, python$compiler, python$have_readline, ' +
                'python$have_ucs4, python$is_64bit, python$version, python$version_full, ' +
                'time$epoch real, time$std_utc_offset real, ' +
                'uname$0, uname$1, uname$2, uname$3, uname$4, uname$5, ' +
                'username, uuid)')



class SQLiteDAL(object):
    _extension = '.db'

    def __init__(self, file_path):
        self.file_path = file_path

        conn = sqlite3.connect(file_path)
        conn.execute(CREATE_TABLE)

    def add_record(self, in_dict):
        pass

    def raw_query(self, query):
        pass

    def select_records(self, limit=None, group_by=None):
        pass


if __name__ == '__main__':
    SQLiteDAL('test.db')
