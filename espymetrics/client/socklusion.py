# -*- coding: utf-8 -*-

import os
import ssl
import sys
import time
import socket
import optparse
import subprocess


DEFAULT_TIMEOUT = 60.0
DEFAULT_SOCKET_TIMEOUT = 5.0

PYTHON = sys.executable
CUR_FILE = os.path.abspath(__file__)


def get_opt_map(values_obj):
    attr_names = set(dir(values_obj)) - set(dir(optparse.Values()))
    return dict([(an, getattr(values_obj, an)) for an in attr_names])


def parse_args():
    prs = optparse.OptionParser()
    prs.add_option('--host')
    prs.add_option('--port', type=int)
    prs.add_option('--wrap-ssl', action='store_true')
    prs.add_option('--timeout')
    prs.add_option('--socket-timeout')
    prs.add_option('--want-response', action='store_true')
    prs.add_option('--child', action='store_true')

    opts, args = prs.parse_args()

    return get_opt_map(opts), args


def get_data():
    return sys.stdin.read()


def send_data_child(data,
                    host,
                    port=None,
                    wrap_ssl=None,
                    timeout=None,
                    socket_timeout=None,
                    want_response=False,
                    response_stream=None):
    timeout = DEFAULT_TIMEOUT if timeout is None else float(timeout)
    if not response_stream:
        response_stream = sys.stdout
    if not host:
        raise ValueError('expected host, not %r' % host)
    if not port:
        # default to HTTP(S) ports
        if wrap_ssl:
            port = 443
        else:
            port = 80

    start_time = time.time()
    max_time = start_time + timeout
    sock = socket.socket()
    if wrap_ssl:
        sock = ssl.wrap_socket(sock)
    sock.settimeout(socket_timeout)
    sock.connect((host, port))
    sock.sendall(data)

    if not want_response:
        return

    while 1:
        data = sock.recv(4096)
        if not data:
            break
        response_stream.write(data)
        response_stream.flush()
        if time.time() > max_time:
            break
    return


def send_data(data, host, port=None, wrap_ssl=None, timeout=None,
              socket_timeout=None, want_response=False):
    cmd_tokens = [PYTHON, CUR_FILE, '--child', '--host', host]
    if port:
        cmd_tokens += ['--port', str(port)]
    if want_response:
        cmd_tokens += ['--want-response']
    if timeout is not None:
        cmd_tokens += ['--timeout', str(timeout)]
    if socket_timeout is not None:
        cmd_tokens += ['--socket-timeout', str(socket_timeout)]
    if wrap_ssl:
        cmd_tokens += ['--wrap-ssl']

    proc = subprocess.Popen(cmd_tokens,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if want_response:
        return proc.communicate(input=data)
    else:
        proc.stdin.write(data)
        proc.stdin.flush()
        proc.stdin.close()
        return None, None


def main():
    opts, args = parse_args()
    data = get_data()
    kwargs = dict(opts)

    is_child = kwargs.pop('child', False)
    if is_child:
        send_data_child(data, **kwargs)
    else:
        #kwargs['want_response'] = True  # TODO
        stdout, stderr = send_data(data, **kwargs)
        if stdout:
            print stdout
        if stderr:
            print 'stderr:', stderr


if __name__ == '__main__':
    main()
