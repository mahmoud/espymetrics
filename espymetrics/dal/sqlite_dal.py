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
                '(id integer primary key asc, ' +
                'hostfqdn, hostname, python$argv, python$bin, ' +
                'python$build_date, python$compiler, python$have_readline, ' +
                'python$have_ucs4, python$is_64bit, python$version, python$version_full, ' +
                'time$utc_epoch real, time$std_utc_offset real, ' +
                'uname$0, uname$1, uname$2, uname$3, uname$4, uname$5, ' +
                'username, uuid)')


class SQLiteDAL(object):
    _extension = '.db'

    def __init__(self, file_path):
        self.file_path = file_path

        conn = sqlite3.connect(file_path)
        conn.execute(CREATE_TABLE)

    def add_record(self, in_dict):
        query = ('INSERT INTO ' + TABLE_NAME +
                 ' (hostfqdn, hostname, python$argv, python$bin, ' +
                 'python$build_date, python$compiler, python$have_readline, ' +
                 'python$have_ucs4, python$is_64bit, python$version, python$version_full, ' +
                 'time$utc_epoch, time$std_utc_offset, ' +
                 'uname$0, uname$1, uname$2, uname$3, uname$4, uname$5, ' +
                 'username, uuid) VALUES (')
        query += '"' + in_dict['hostfqdn'] + '", '
        query += '"' + in_dict['hostname'] + '", '
        query += '"' + in_dict['python']['argv'] + '", '
        query += '"' + in_dict['python']['bin'] + '", '
        query += '"' + in_dict['python']['build_date'] + '", '
        query += '"' + in_dict['python']['compiler'] + '", '
        query += '"' + str(in_dict['python']['have_readline'])[0] + '", '
        query += '"' + str(in_dict['python']['have_ucs4'])[0] + '", '
        query += '"' + str(in_dict['python']['is_64bit'])[0] + '", '
        query += '"' + in_dict['python']['version'] + '", '
        query += '"' + in_dict['python']['version_full'] + '", '
        query += '"' + str(in_dict['time']['utc_epoch']) + '", '
        query += '"' + str(in_dict['time']['std_utc_offset']) + '", '
        query += '"' + in_dict['uname'][0] + '", '
        query += '"' + in_dict['uname'][1] + '", '
        query += '"' + in_dict['uname'][2] + '", '
        query += '"' + in_dict['uname'][3] + '", '
        query += '"' + in_dict['uname'][4] + '", '
        query += '"' + in_dict['uname'][5] + '", '
        query += '"' + in_dict['username'] + '", '
        query += '"' + in_dict['uuid']
        query += '")'

        conn = sqlite3.connect(self.file_path)
        conn.isolation_level = None  # autocommit
        print repr(query)
        conn.execute(query)
        conn.close()
        return

    def raw_query(self, query):
        pass

    def select_records(self, limit=None, group_by=None):
        ret = {'counts': {}}
        if not group_by:
            return {}
        group_by = group_by.replace('.', '$')
        query = 'SELECT ROWID, ' + group_by + ', COUNT(*) FROM ' + TABLE_NAME
        query += ' GROUP BY ' + str(group_by)
        if limit:
            query += ' ORDER BY ROWID DESC LIMIT ' + str(limit)

        conn = sqlite3.connect(self.file_path)
        rows = conn.execute(query).fetchall()
        for _, group_key, group_count in rows:
            ret['counts'][group_key] = group_count

        ret['grouped_by'] = group_by
        ret['grouped_key_count'] = len(rows)
        ret['record_count'] = sum(ret['counts'].values())
        return ret


if __name__ == '__main__':
    SQLiteDAL('test.db')
