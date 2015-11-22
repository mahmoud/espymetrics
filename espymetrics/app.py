# -*- coding: utf-8 -*-

import json
import argparse
import datetime


from clastic import Application, Middleware, render_basic, MetaApplication
from clastic.errors import BadRequest
from clastic.middleware import GetParamMiddleware

from dal import LineDAL, SQLiteDAL


PORT = 8888
META_PORT = 8889
DEFAULT_DAL = 'line'
DEFAULT_PREFIX = 'metrics_data'


def main():
    prs = argparse.ArgumentParser()
    prs.add_argument('--debug', action='store_true')
    opts, _ = prs.parse_known_args()
    debug = opts.debug

    v1_app = create_v1_app('sql')
    app = Application([('/v1', v1_app)])
    meta_app = MetaApplication()
    if debug:
        app.add(('/', meta_app))

    app.serve(port=PORT, threaded=True)

    return


def create_v1_app(dal_name=DEFAULT_DAL, file_path=None):
    if dal_name == 'line':
        dal_type = LineDAL
    elif dal_name == 'sql':
        dal_type = SQLiteDAL
    else:
        raise ValueError('unrecognized DAL name: %r' % dal_name)

    if file_path is None:
        file_path = DEFAULT_PREFIX + dal_type._extension

    data_store = dal_type(file_path)

    rdm = RequestDataMiddleware()
    gpm = GetParamMiddleware({'raw_query': str, 'group_by': str, 'limit': int})

    return Application([('/on_import', on_import_endpoint, render_basic),
                        ('/count', get_count_data, render_basic),
                        ('/download/import', get_import_data, render_basic)],
                       resources={'data_store': data_store},
                       middlewares=[gpm, rdm])


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
