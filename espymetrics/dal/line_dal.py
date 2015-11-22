# -*- coding: utf-8 -*-
"""The line-based DAL writes one text line per record to a
UTF-8-encoded file of your choosing. Each line is a JSON object, per
the JSON Lines spec: http://jsonlines.org/

The advantages are simplicity and scalability of writes (append-only
to the end of a text file). The drawbacks are limits in terms
of query language, storage efficiency, and data load speeds.
"""


import json

from collections import Counter
from boltons import jsonutils

_MISSING = object()

DEFAULT_FLUSH_INTERVAL = 1  # write to disk on every new record
DEFAULT_SEP = '$'  # '$' is valid in sqlite column names without escaping


class LineDAL(object):
    _extension = '.jsonl'

    def __init__(self, file_path, flush_interval=DEFAULT_FLUSH_INTERVAL):
        self.file_path = file_path
        self.flush_interval = int(flush_interval)

        self._fh = open(self.file_path, 'a')
        self.total_count = 0  # TODO: read number of existing lines in file?

    def add_record(self, indict):
        self._fh.write(json.dumps(indict))
        self._fh.write('\n')
        self.total_count += 1
        if self.total_count % self.flush_interval == 0:
            self._fh.flush()

    def raw_query(self, query):
        raise NotImplementedError('JSONL DAL does not support raw queries')

    def select_records(self, limit=None, group_by=None):
        ret = {}
        ret['counts'] = counts = Counter()
        reverse = True
        if not limit:
            reverse = False
        jliter = jsonutils.JSONLIterator(open(self.file_path),
                                         reverse=reverse)
        if group_by:
            group_by_path = parse_path(group_by)
        else:
            group_by_path = [None]
        for i, cur_record in enumerate(jliter):
            if limit and i > limit:
                break
            try:
                key_val = get_path(cur_record, group_by_path)
                key_val = str(key_val)
            except (KeyError, IndexError, TypeError):
                try:
                    ret['error_count'] += 1
                except KeyError:
                    ret['error_count'] = 1
            else:
                counts[key_val] += 1
        if not counts:
            return {'record_count': 0}  # no records yet
        ret['grouped_key_count'] = len(counts)
        ret['record_count'] = i - 1
        ret['grouped_by'] = group_by
        return ret


# known weakness of the path approach is that the dictionaries cannot
# have string keys containing just integers
def parse_path(path, sep=DEFAULT_SEP):
    try:
        path_segs = path.split(sep)
    except:
        raise TypeError('expected string, not %r' % path)
    ret = []
    for p in path_segs:
        p = p.strip()
        if not p:
            continue
        try:
            ret.append(int(p))
        except ValueError:
            ret.append(p)
    return ret


def get_path(target, path, default=_MISSING, sep=DEFAULT_SEP):
    if isinstance(path, basestring):
        path = parse_path(path)
    cur = target
    for p in path:
        try:
            cur = cur[p]
        except (IndexError, KeyError, TypeError):
            if default is not _MISSING:
                return default
            raise KeyError('error retrieving segment %r of path %r'
                           % (p, path))
    return cur
