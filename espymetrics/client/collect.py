# -*- coding: utf-8 -*-

import sys
import json
import time
import uuid
import socket
import getpass
import argparse
import datetime
import platform
import socklusion


DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8888
DEFAULT_PATH = '/v1/on_import'
TIMEOUT = 5.0

INSTANCE_ID = uuid.uuid4()
IS_64BIT = sys.maxsize > 2 ** 32

HAVE_READLINE = True
try:
    import readline
except:
    HAVE_READLINE = False

HAVE_UCS4 = getattr(sys, 'maxunicode', 0) > 65536


TIME_INFO = {'utc_epoch': str(datetime.datetime.utcnow()),
             'std_utc_offset': -time.timezone / 3600.0}


def get_python_info():
    ret = {}
    ret['argv'] = ' \t '.join(sys.argv)
    ret['bin'] = sys.executable
    ret['is_64bit'] = IS_64BIT
    try:
        ret['version'] = sys.version.split()[0]
    except:
        ret['version'] = ''
    ret['version_full'] = sys.version
    ret['compiler'] = platform.python_compiler()
    ret['build_date'] = platform.python_build()[1]
    ret['version_info'] = list(sys.version_info)
    ret['have_ucs4'] = HAVE_UCS4
    ret['have_readline'] = HAVE_READLINE
    return ret


def get_all_info():
    ret = {}
    ret['username'] = getpass.getuser()
    ret['uuid'] = str(INSTANCE_ID)
    ret['hostname'] = socket.gethostname()
    ret['hostfqdn'] = socket.getfqdn()
    ret['uname'] = platform.uname()

    ret['python'] = get_python_info()
    ret['time'] = TIME_INFO
    return ret


def build_post_message(data, host=DEFAULT_HOST, path=DEFAULT_PATH):
    msg_lines = ['POST %s HTTP/1.0' % path,
                 'Host: %s' % host,
                 'Content-Length: ' + str(len(data)),
                 '',
                 data]
    msg = '\r\n'.join(msg_lines)
    return msg


def send_import_analytics(host=DEFAULT_HOST, port=DEFAULT_PORT, data_dict=None,
                          timeout=TIMEOUT, path=DEFAULT_PATH):
    if data_dict is None:
        data_dict = get_all_info()
    msg = build_post_message(json.dumps(data_dict), host=host, path=path)
    return socklusion.send_data(msg,
                                host=host,
                                port=port,
                                wrap_ssl=False,
                                timeout=timeout,
                                want_response=True)


def main():
    prs = argparse.ArgumentParser()
    prs.add_argument('--host', default=DEFAULT_HOST)
    prs.add_argument('--port', default=DEFAULT_PORT, type=int)
    prs.add_argument('--path', default=DEFAULT_PATH)
    prs.add_argument('--verbose', action='store_true')
    args = prs.parse_args()
    output = send_import_analytics(host=args.host,
                                   port=args.port,
                                   path=args.path)
    if args.verbose:
        print output


if __name__ == '__main__':
    main()
