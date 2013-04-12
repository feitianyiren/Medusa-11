"""Part of Medusa (MEDia USage Assistant).

Provides socket based communication between the Webmote and Receivers.
"""

import socket

from gevent_zeromq import zmq
import simplejson as json

import configger as config


def get_host_ip(hostname):
    # Cross platform, but needs testing to see if reliable.
    return socket.gethostbyname_ex(hostname)[2][0]


class Communicate(object):

    def __init__(self):
        self.receiver_hostname = None

    def __enter__(self):
        self.open_connection(self.receiver_hostname)

    def __exit__(self, type, value, traceback):
        self.close_connection()

    def open_socket(self):
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)

        # Allows the re-use of a port, for testing purposes.
        self.socket.setsockopt(socket.SOL_SOCKET,
                               socket.SO_REUSEADDR,
                               1)

    def open_connection(self, receiver_hostname):
        receiver_ip = get_host_ip(receiver_hostname)

        self.open_socket()

        # 3 second timeout seems more than enough.
        self.socket.settimeout(3)

        self.socket.connect((receiver_ip,
                             config.com_port))

    def listen(self):
        host_ip = get_host_ip(config.hostname)

        self.open_socket()

        self.socket.bind((host_ip, config.com_port))

        # Keep the queue shortish to prevent spamming lag.
        self.socket.listen(3)

    def close_connection(self):
        self.socket.close()

    def accept(self):
        (self.remote_client, remote_address) = self.socket.accept()

        # '1024' is more than enough. Haven't tested minimum.
        return json.loads(self.remote_client.recv(1024))

    def receive(self):
        return json.loads(self.socket.recv(1024))

    def reply(self, data):
        self.remote_client.sendall(json.dumps(data))

    def send(self, data):
        # If it is not a tuple, make it so. Minimum length of two.
        if not isinstance(data, tuple):
            data = (data, None)

        self.socket.sendall(json.dumps(data))


class Publish(object):

    def __init__(self):
        self.publish()

    def open_socket(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.PUB)

    def close_socket(self):
        self.socket.close()

    def publish(self):
        host_ip = get_host_ip(config.hostname)

        self.open_socket()

        self.socket.bind("tcp://%s:%s" % (host_ip, config.pub_port))

    def send(self, data):
        self.socket.send(json.dumps(data))


class Subscribe(object):

    def __init__(self, receiver_hostname):
        self.receiver_hostname = receiver_hostname

        self.subscribe()

    def open_socket(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.SUB)

    def close_socket(self):
        self.socket.close()

    def subscribe(self):
        receiver_ip = get_host_ip(self.receiver_hostname)

        self.open_socket()

        self.socket.connect("tcp://%s:%s" % (receiver_ip, config.pub_port))

        self.socket.setsockopt(zmq.SUBSCRIBE, "")

    def receive(self):
        return json.loads(self.socket.recv())

