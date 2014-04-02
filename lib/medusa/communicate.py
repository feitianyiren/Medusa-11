#!/usr/bin/env python

"""
Communicate asynchronously over sockets as either a client or a server while
using MessagePack for serialization.

Trigger remote method calls on both ends through the provided proxy object.

Both ends of the communication will automatically reconnect in the event of
a disconnection.
"""

import asyncore
import socket
import threading
import time

from PyQt4 import QtCore
import msgpack

from lib.medusa import utilities
from lib.medusa.config import config
from lib.medusa.log import log

#------------------------------------------------------------------------------

class Communicate(object):
    """
    Determine if we are to be a client or a server, and then start an
    appropriate communication thread.
    """

    __metaclass__ = utilities.Singleton

    def __init__(self, proxy, host=None, port=None, name=None, qthread=False):
        self.proxy = proxy
        self.host = host or "0.0.0.0"
        self.port = port or config.getint("ports", "socket")
        self.name = name or ""

        # Determine if we should run as a client or a server.
        #
        if self.name:
            self.client = True

        else:
            self.client = False

            # Keep track of client connections.
            Communicate.connections = {}

        # Use a QThread is we are on the GUI side.
        self.qthread = qthread

        self._start()

    def _start(self):
        call = CommunicationThread

        if self.qthread:
            call = CommunicationQThread

        self.thread = call(self.client,
                           self.proxy,
                           self.host,
                           self.port,
                           self.name)
        self.thread.start()

    #--------------------------------------------------------------------------

    def send(self, *args):
        """
        Send a message in the appropriate direction.
        """

        if self.client:
            result = self.thread._send_client(args[0])

            # If the message fails to send, restart the client connection.
            #
            if not result:
                log.warn("Relaunching communication thread")

                self._start()

            return result

        else:
            return self.thread._send_server(args[0], args[1])

#------------------------------------------------------------------------------

class CommunicationThread(threading.Thread):
    """
    Launch either a client or a server socket communication interface.
    """

    def __init__(self, client, proxy, host, port, name):
        super(CommunicationThread, self).__init__()

        log.info("CommunicationThread initialised")

        self.handler = CommunicationHandler(client, proxy, host, port, name)
        CommunicationThread.packer = self.handler.packer
        self.run = self.handler.run
        self._send_client = self.handler._send_client
        self._send_server = self.handler._send_server


class CommunicationQThread(QtCore.QThread):
    """
    Launch either a client or a server socket communication interface, inside
    a GUI.
    """

    def __init__(self, client, proxy, host, port, name):
        super(CommunicationQThread, self).__init__()

        log.info("CommunicationQThread initialised")

        self.handler = CommunicationHandler(client,
                                            proxy,
                                            host,
                                            port,
                                            name,
                                            qthread=True)
        CommunicationQThread.packer = self.handler.packer
        self.run = self.handler.run
        self._send_client = self.handler._send_client
        self._send_server = self.handler._send_server

#------------------------------------------------------------------------------

class CommunicationHandler(object):
    """
    Handle communication for a server or client communication thread.
    """

    packer = msgpack.Packer()

    def __init__(self, client, proxy, host, port, name, qthread=False):
        self.client = client
        self.proxy = proxy
        self.host = host
        self.port = port
        self.name = name
        self.qthread = qthread

    def run(self):
        # Open a client connection.
        #
        if self.client:
            self.connection = CommunicationClient(self.proxy,
                                                  self.host,
                                                  self.port,
                                                  self.name,
                                                  qthread=self.qthread)

        # Start listening as a server.
        #
        else:
            CommunicationServer(self.proxy, self.host, self.port)

        asyncore.loop(timeout=0.5)

    def _send_client(self, message):
        """
        Check for an active connection and then send a message to the server.
        """

        try:
            # Check that we are connected.
            if self.connection.connected:
                # Write the message to the buffer so that it will be sent.
                self.connection.buffer_ = self.packer.pack(message)

                log.info("%s buffered: %s", self.name, message)

            else:
                log.error("Send failed: No active connection found")

                return False

        except AttributeError as excp:
            log.error("Send failed: %s", excp)

            return False

        return True

    def _send_server(self, names, message):
        """
        Send a message to the named connection(s).
        """

        try:
            for name in names:
                connection = Communicate.connections[name]
                connection.send(self.packer.pack(message))

                log.info("Sent to %s: %s", name, message)

        except (KeyError, RuntimeError) as excp:
            log.error("Send failed: %s", excp)

            return False

        return True


class CommunicationClient(asyncore.dispatcher):
    """
    Connect to a server and send/receive remote method calls asynchronously.
    """

    buffer_ = ""

    def __init__(self, proxy, host, port, name, qthread=False):
        asyncore.dispatcher.__init__(self)

        log.info("CommunicationClient initialised")

        self.unpacker = msgpack.Unpacker()
        self.proxy = proxy()
        self.host = host
        self.port = port
        self.name = name
        self.qthread = qthread
        self._connect()

    def _connect(self):
        self.connected = False

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.connect((self.host, self.port))

        except socket.gaierror as excp:
            log.error("%s failed to connect: %s", self.name, excp)

            raise

        # Send our name to the server to register the connection with.
        #
        try:
            while True:
                if self.qthread:
                    sent = self.send(CommunicationQThread.packer.pack(self.name))
                
                else:
                    sent = self.send(CommunicationThread.packer.pack(self.name))

                if sent != 0:
                    break

            self.connected = True

            log.warn("%s sent name" % self.name)

        except socket.error as excp:
            log.error("%s failed to send name: %s", self.name, excp)

    def writable(self):
        return (len(self.buffer_) > 0)

    def handle_write(self):
        sent = self.send(self.buffer_)
        self.buffer_ = self.buffer_[sent:]

    def handle_read(self):
        """
        Stream incoming messages into MessagePack, and action them when ready.
        """

        try:
            self.unpacker.feed(self.recv(1))

            for message in self.unpacker:
                log.info("%s received: %s", self.name, message)

                # Attempt to call the requested method on the proxy.
                #
                try:
                    method = message.keys()[0]

                    try:
                        getattr(self.proxy, method)(message[method])

                    except AttributeError as excp:
                        log.error("Failed to call method %s: %s", method, excp)

                except AttributeError as excp:
                    log.error("Failed to call a method: %s", excp)

        except socket.error as excp:
            log.error("Failed to receive: %s", excp)

    def handle_close(self):
        self.close()
        self.connected = False
        log.info("CommunicationClient closed")

        time.sleep(5)
        log.warn("Attempting to reconnect to server")
        self._connect()


class CommunicationServer(asyncore.dispatcher):
    """
    Listen for incoming client connections and dispatch them to a handler.
    """

    proxy = None

    def __init__(self, proxy, host, port):
        asyncore.dispatcher.__init__(self)

        log.info("CommunicationServer initialised")

        CommunicationServer.proxy = proxy()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()

        try:
            self.bind((host, port))

        except socket.error as excp:
            log.error("Failed to bind socket: %s", excp)

            raise

        log.warn("Listening on port: %s", port)

        self.listen(5)

    def handle_accept(self):
        client, address = self.accept()

        log.warn("Received connection from: %s", address[0])

        # Pass this client off to a handler.
        CommunicationClientHandler(client)


class CommunicationClientHandler(asyncore.dispatcher_with_send):
    """
    Send/receive remote method calls to/from a server.
    """

    def __init__(self, client):
        asyncore.dispatcher_with_send.__init__(self, client)

        self.unpacker = msgpack.Unpacker()
        self.name = None

    def handle_read(self):
        """
        Stream incoming messages into MessagePack and action them when ready.
        """

        self.unpacker.feed(self.recv(1))

        for message in self.unpacker:
            if not self.name:
                # The first message received from a new connection will be the
                # name of the client, which we can store and use in future to
                # access this connection.
                #
                try:
                    Communicate.connections[message] = self
                    self.name = message

                    log.info("%s connected", self.name)

                except TypeError as excp:
                    log.error("Failed to set name: %s", excp)

            else:
                log.info("Received from %s: %s", self.name, message)

                # Attempt to call the requested method on the proxy.
                #
                method = message.keys()[0]

                try:
                    getattr(CommunicationServer.proxy, method)(message[method])

                except AttributeError as excp:
                    log.error("Failed to call method %s: %s", method, excp)

    def handle_close(self):
        self.close()

        try:
            Communicate.connections.pop(self.name, None)

        except TypeError as excp:
            log.error("Failed to remove connection: %s", excp)

        log.warn("%s disconnected", self.name)
