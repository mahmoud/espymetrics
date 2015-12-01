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

About this implementation
-------------------------

This implementation uses sqlite3 directly, but could arguably benefit
from usage of an ORM-like system. Most ORMs can have a lot of negative
side effects when working on large projects or with large teams, a la
unexpected generated SQL output. That said, in my experience,
SQLAlchemy's expression language is pretty enterprise-ready. Still,
raw SQL here for simplicity.

"""

import sqlite3
from boltons.iterutils import remap, get_path
# further reading: http://sedimental.org/remap.html


_MISSING = object()
SEP = '$'  # '$' is valid in sqlite column names, no escaping required

CREATE_QTMPL = ('CREATE TABLE IF NOT EXISTS {table_name}'
                ' ({cols_types})')
INSERT_QTMPL = ('INSERT INTO {table_name} ({cols})'
                ' VALUES ({placeholders})')


def flatten_fields(msg_proto, **kwargs):
    col_type_map = kwargs.pop('col_type_map', {})
    default_col_type = kwargs.pop('default_col_type', 'text')
    sep = kwargs.pop('sep', SEP)
    if kwargs:
        raise TypeError('unexpected keyword arguments: %r' % kwargs.keys())

    ret = []

    def visit(path, key, value):
        if isinstance(value, (list, dict)):
            return True  # traverse containers, but don't no columns for them

        full_path = path + (key,)
        col_type = col_type_map.get(full_path, default_col_type)
        full_path_str = sep.join([str(p) for p in full_path])
        ret.append((full_path, full_path_str, col_type))
        return True

    # read more about remap here: http://sedimental.org/remap.html
    remap(msg_proto, visit=visit)
    return sorted(ret, key=lambda x: x[0])


class SQLiteDAL(object):
    _extension = '.db'

    def __init__(self, file_path, table_name, message_proto, autoinitdb=True):
        self.file_path = file_path
        self.table_name = table_name
        self.message_proto = message_proto
        self._flat_fields = flatten_fields(self.message_proto)

        self._init_queries()
        if autoinitdb:
            self.init_db()

    def _init_queries(self):
        ff = self._flat_fields
        self._col_map = dict([(k, v) for _, k, v in ff])

        self._col_types_str = ', '.join(['%s %s' % (k, v) for _, k, v in ff])
        self._create_q = CREATE_QTMPL.format(table_name=self.table_name,
                                             cols_types=self._col_types_str)
        self._cols_str = ', '.join(['%s' % f[1] for f in ff])
        placeholders_str = ', '.join('?' * len(self._col_map))
        self._insert_q = INSERT_QTMPL.format(table_name=self.table_name,
                                             cols=self._cols_str,
                                             placeholders=placeholders_str)
        return

    def init_db(self):
        # TODO: check that schema matches in existing db case
        conn = sqlite3.connect(self.file_path)
        with conn:
            conn.execute(self._create_q)
        return

    def add_record(self, in_dict):
        bindables = []
        for path, col, _ in self._flat_fields:
            val = get_path(in_dict, path)
            bindables.append(val)
        conn = sqlite3.connect(self.file_path)
        with conn:
            conn.execute(self._insert_q, bindables)
        return

    def raw_query(self, query):
        conn = sqlite3.connect(self.file_path)
        conn.row_factory = sqlite3.Row
        with conn:
            rows = conn.execute(query).fetchall()
        return rows

    def select_records(self, limit=None, group_by=None):
        pass


if __name__ == '__main__':
    from common import MESSAGE_PROTO
    sqldal = SQLiteDAL('test.db', 'on_import_data', MESSAGE_PROTO)
    sqldal.add_record(MESSAGE_PROTO)

    import pdb;pdb.set_trace()
