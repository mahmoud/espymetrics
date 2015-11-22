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


_MISSING = object()
SEP = '$'  # '$' is valid in sqlite column names, no escaping required


class SQLiteDAL(object):
    _extension = '.db'

    def __init__(self, file_path):
        self.file_path = file_path

    def add_record(self, in_dict):
        pass

    def raw_query(self, query):
        pass

    def select_records(self, limit=None, group_by=None):
        pass
