# -*- coding: utf-8 -*-

import sys
import json
import time
import uuid
import socket
import getpass
import datetime
import platform
import socklusion

try:
    from strutils import escape_shell_args
except ImportError:
    from boltons.strutils import escape_shell_args


DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8888
DEFAULT_PATH = '/v1/on_import'
TIMEOUT = 5.0

INSTANCE_ID = uuid.uuid4()
IS_64BIT = sys.maxsize > 2 ** 32
HAVE_UCS4 = getattr(sys, 'maxunicode', 0) > 65536
HAVE_READLINE = True
try:
    import readline
except Exception:
    HAVE_READLINE = False

try:
    import sqlite3
    SQLITE_VERSION = sqlite3.sqlite_version
except Exception:
    SQLITE_VERSION = ''


try:
    import ssl
    OPENSSL_VERSION = ssl.OPENSSL_VERSION
except Exception:
    OPENSSL_VERSION = ''


TIME_INFO = {'utc': str(datetime.datetime.utcnow()),
             'std_utc_offset': -time.timezone / 3600.0}


def get_python_info():
    ret = {}
    ret['argv'] = escape_shell_args(sys.argv)
    ret['bin'] = sys.executable
    ret['is_64bit'] = IS_64BIT

    # Even though compiler/build_date are already here, they're
    # actually parsed from the version string. So, in the rare case of
    # the unparsable version string, we're still transmitting it.
    ret['version'] = sys.version

    ret['compiler'] = platform.python_compiler()
    ret['build_date'] = platform.python_build()[1]
    ret['version_info'] = list(sys.version_info)
    ret['openssl_version'] = OPENSSL_VERSION
    ret['sqlite_version'] = SQLITE_VERSION
    ret['have_ucs4'] = HAVE_UCS4
    ret['have_readline'] = HAVE_READLINE
    return ret


def get_all_info():
    ret = {}
    ret['username'] = getpass.getuser()
    ret['uuid'] = str(INSTANCE_ID)
    ret['hostname'] = socket.gethostname()
    ret['hostfqdn'] = socket.getfqdn()
    uname = platform.uname()
    ret['uname'] = {'system': uname[0],
                    'node': uname[1],
                    'release': uname[2],  # linux: distro name
                    'version': uname[3],  # linux: kernel version
                    'machine': uname[4],
                    'processor': uname[5]}
    linux_dist = platform.linux_distribution()
    ret['linux_dist'] = {'name': linux_dist[0],
                         'version': linux_dist[1]}

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
    return msg.encode('utf-8')


def send_import_analytics(host=DEFAULT_HOST, port=DEFAULT_PORT, data_dict=None,
                          timeout=TIMEOUT, path=DEFAULT_PATH, wrap_ssl=False):
    if data_dict is None:
        data_dict = get_all_info()
    msg = build_post_message(json.dumps(data_dict), host=host, path=path)
    return socklusion.send_data(msg,
                                host=host,
                                port=port,
                                wrap_ssl=wrap_ssl,
                                timeout=timeout,
                                want_response=True)


def main():
    import argparse  # TODO: optparse
    from pprint import pprint

    prs = argparse.ArgumentParser()
    prs.add_argument('--host', default=DEFAULT_HOST)
    prs.add_argument('--port', default=DEFAULT_PORT, type=int)
    prs.add_argument('--path', default=DEFAULT_PATH)
    prs.add_argument('--verbose', action='store_true')
    args = prs.parse_args()
    data_dict = get_all_info()
    if args.verbose:
        pprint(data_dict)
    output = send_import_analytics(host=args.host,
                                   port=args.port,
                                   data_dict=data_dict,
                                   path=args.path)
    if args.verbose:
        print(output)
    return


if __name__ == '__main__':
    main()
