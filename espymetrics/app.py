# -*- coding: utf-8 -*-

import os
import json
import argparse
import datetime
from collections import Counter

from support import Group
from boltons import jsonutils
from clastic import Application, Middleware, render_basic, MetaApplication
from clastic.errors import BadRequest
from clastic.middleware import GetParamMiddleware


PORT = 8888
META_PORT = 8889
DEFAULT_FLUSH_INTERVAL = 1
DEFAULT_FILE_PATH = os.path.abspath('./import_analytics.jsonl')
_MISSING = object()


def create_v1_app(file_path=DEFAULT_FILE_PATH):
    data_store = LineDAL(file_path)
    rdm = RequestDataMiddleware()
    gpm = GetParamMiddleware({'group_by': str, 'limit': int})

    return Application([('/on_import', on_import_endpoint, render_basic),
                        ('/count', get_count_data, render_basic),
                        ('/download/import', get_import_data, render_basic)],
                       resources={'data_store': data_store},
                       middlewares=[gpm, rdm])


def main():
    prs = argparse.ArgumentParser()
    prs.add_argument('--debug', action='store_true')
    opts, _ = prs.parse_known_args()
    debug = opts.debug

    v1_app = create_v1_app()
    app = Application([('/v1', v1_app)])
    meta_app = MetaApplication()
    if debug:
        app.add(('/', meta_app))
        app.serve(port=PORT)
    else:
        group = Group(wsgi_apps=[(app, ('0.0.0.0', PORT), False),
                                 (meta_app, ('0.0.0.0', META_PORT), False)],
                      num_workers=1,
                      prefork=True,
                      daemonize=True)
        group.serve_forever()
    # stop a daemonized server using the .pgrp file:
    # kill -15 -$(cat support.pgrp)


# known weakness of the path approach is that the dictionaries cannot
# have string keys containing just integers
def parse_path(path):
    try:
        path_segs = path.split('.')
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


def get_path(target, path, default=_MISSING):
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

    def select_records(self, limit=None, group_by=None, raw_query=None):
        if raw_query is not None:
            raise NotImplementedError('JSONL DAL does not support raw queries')
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


class RequestDataMiddleware(Middleware):
    provides = ('request_data',)

    def __init__(self, as_text=False):
        self.as_text = as_text

    def request(self, next, request):
        return next(request_data=request.get_data(as_text=self.as_text))


def on_import_endpoint(request_data, data_store):
    if not request_data:
        raise BadRequest('expected json body')
    data = json.loads(request_data)
    data['server_time'] = str(datetime.datetime.utcnow())
    data_store.add_record(data)
    return {'success': True}


def get_count_data(data_store, group_by, limit):
    """\
    A very basic counting/grouping function for analytics data.

    From a browser, try <url>?group_by=username&limit=100

    Records are read in reverse, so a limit of 100 means the 100 most
    recent records.  If no limit is provided, all records are counted.
    """
    ret = data_store.select_records(group_by=group_by, limit=limit)
    return ret


def get_import_data(data_store):
    return open(data_store.file_path, 'rb').read()


if __name__ == '__main__':
    main()
