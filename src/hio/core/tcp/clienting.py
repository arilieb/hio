# -*- encoding: utf-8 -*-
"""
hio.core.tcp.clienting Module
"""

import sys
import os
import errno
import socket
import ssl

from contextlib import contextmanager


from ... import help
from ...base import tyming, doing
from .. import coring, wiring


logger = help.ogler.getLogger()

@contextmanager
def openClient(cls=None, **kwa):
    """
    Wrapper to create and open TCP Client instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls is Class instance of subclass instance

    Usage:
        with openClient() as client0:
            client0.accept()

        with openClient(cls=ClientTls) as client0:
            client0.accept()

    """
    if cls is None:
        cls = Client
    try:
        client = cls(**kwa)
        client.reopen()

        yield client

    finally:
        client.close()


class Client(tyming.Tymee):
    """
    Nonblocking TCP Socket Client Class.

    See tyming.Tymee for inherited attributes, properties, and methods

    Attributes:

    Properties:

    Methods:

    """
    Tymeout = 0.0  # tymeout in seconds, tymeout of 0.0 means ignore tymeout
    Reconnectable = False  # auto reconnect flag

    def __init__(self,
                 tymeout=None,
                 ha=None,
                 host='127.0.0.1',
                 port=56000,
                 reconnectable=None,
                 bs=8096,
                 txbs=None,
                 rxbs=None,
                 wl=None,
                 **kwa):
        """
        Initialization method for instance.

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tymeout = auto reconnect retry tymeout
            ha = host address duple (host, port) of remote server
            host = host address or tcp server to connect to
            port = socket port
            reconnectable = Boolean retry auto reconnect if timed out
            bs = buffer size
            txbs = bytearray of data to send
            rxbs = bytearray of data received
            wl = WireLog object if any
        """
        super(Client, self).__init__(**kwa)
        self.tymeout = tymeout if tymeout is not None else self.Tymeout
        self.tymer = tyming.Tymer(tymth=self.tymth, duration=self.tymeout)  # reconnect retry timer

        self.ha = ha or (host, port)
        host, port = self.ha
        self.hostname = host  # host domain name
        host = coring.normalizeHost(host)  # ip host address
        self.ha = (host, port)

        self.cs = None  # connection socket
        self.ca = (None, None)  # host address of local connection
        self._accepted = False  # attribute to support accepted property
        self.cutoff = False  # True when detect connection closed on far side
        self.reconnectable = reconnectable if reconnectable is not None else self.Reconnectable
        self.opened = False

        self.bs = bs
        self.txbs = txbs if txbs is not None else bytearray()  # byte array of data to send
        self.rxbs = rxbs if rxbs is not None else bytearray()  # byte array of data recieved
        self.wl = wl


    @property
    def host(self):
        """
        Property that returns host in .ha duple
        """
        return self.ha[0]


    @host.setter
    def host(self, value):
        """
        setter for host property
        """
        self.ha = (value, self.port)


    @property
    def port(self):
        """
        Property that returns port in .ha duple
        """
        return self.ha[1]


    @port.setter
    def port(self, value):
        """
        setter for port property
        """
        self.ha = (self.host, value)


    @property
    def accepted(self):
        """
        Property that returns accepted state of TCP socket
        """
        return self._accepted


    @accepted.setter
    def accepted(self, value):
        """
        setter for accepted property
        """
        self._accepted = value


    @property
    def connected(self):
        """
        Property that returns connected state of TCP socket
        Non-tls tcp is connected when accepted
        """
        return self.accepted


    @connected.setter
    def connected(self, value):
        """
        setter for connected property
        """
        self.accepted = value


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Client, self).wind(tymth)
        self.tymer.wind(tymth)


    def actualBufSizes(self):
        """
        Returns duple of the the actual socket send and receive buffer size
        (send, receive)
        """
        if not self.cs:
            return (0, 0)

        return (self.cs.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
                self.cs.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))


    def open(self):
        """
        Opens connection socket in non blocking mode.

        if socket not closed properly, binding socket gets error
          OSError: (48, 'Address already in use')
        """
        self.accepted = False
        self.connected = False
        self.cutoff = False

        #create connection socket
        self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # make socket address reusable.
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in
        # TIME_WAIT state, without waiting for its natural timeout to expire.
        self.cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Linux TCP allocates twice the requested size
        if sys.platform.startswith('linux'):
            bs = 2 * self.bs  # get size is twice the set size
        else:
            bs = self.bs

        if self.cs.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) <  bs:
            self.cs.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.bs)
        if self.cs.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < bs:
            self.cs.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.bs)

        self.cs.setblocking(0) #non blocking socket
        self.opened = True
        return True


    def reopen(self):
        """
        Idempotently opens socket
        """
        self.close()
        return self.open()


    def shutdown(self, how=socket.SHUT_RDWR):
        """
        Shutdown connected socket .cs
        """
        if self.cs:
            try:
                self.cs.shutdown(how)  # shutdown socket
            except OSError as ex:
                pass


    def shutdownSend(self):
        """
        Shutdown send on connected socket .cs
        """
        if self.cs:
            try:
                self.shutdown(how=socket.SHUT_WR)  # shutdown socket
            except OSError as ex:
                pass


    def shutdownReceive(self):
        """
        Shutdown receive on connected socket .cs
        """
        if self.cs:
            try:
                self.shutdown(how=socket.SHUT_RD)  # shutdown socket
            except OSError as ex:
                pass


    def close(self):
        """
        Shutdown and close connected socket .cs
        """
        if self.cs:
            self.shutdown()
            self.cs.close()  #close socket
            self.cs = None
            self.accepted = False
            self.connected = False
            self.opened = False


    def refresh(self):
        """
        Restart timer
        """
        self.tymer.restart()


    def accept(self):
        """
        Attempt nonblocking acceptance connect to .ha
        Returns True if successful
        Returns False if not so try again later
        """
        if not self.cs:
            self.reopen()

        try:
            result = self.cs.connect_ex(self.ha)  # async connect
        except OSError as ex:
            logger.error("OSError = %s\n", ex)
            raise

        if result not in [0, errno.EISCONN]:  # not connected
            if result in (errno.EINVAL, errno.ECONNREFUSED):  # server not listening so must reopen
                self.reopen()
            return False  # try again later

        # now self.cs has new virtual port see self.cs.getsockname()
        self.ca = self.cs.getsockname()  # resolved local connection address
        # self.cs.getpeername() is self.ha
        self.ha = self.cs.getpeername()  # resolved remote connection address

        self.accepted = True  # also sets .connected == True
        self.cutoff = False
        return True


    def connect(self):
        """
        Attempt nonblocking connect to .ha
        Returns True if successful
        Returns False if not so try again later
        For non-TLS tcp connect is done when accepted
        This is placeholder for subclass Tls
        """
        return self.accept()


    def serviceConnect(self):
        """
        Service connection attempt
        If not already connected make a nonblocking attempt
        Returns .connected
        """
        if not self.connected:
            self.connect()  # if successful sets .accepted .connected to True

            if not self.connected and self.reconnectable:
                if self.tymeout > 0.0 and self.tymer.expired:  # timed out
                    self.reopen()
                    self.tymer.restart()

        return self.connected


    def receive(self):
        """
        Perform non blocking receive from connected socket .cs

        If no data then returns None
        If connection closed then returns empty
        Otherwise returns data
        data is string in python2 and bytes in python3
        """
        try:
            data = self.cs.recv(self.bs)
        except OSError as ex:
            # ex.args[0] == ex.errno for better os compatibility.
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if  ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                return None  # blocked waiting for data
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED):

                self.cutoff = True  # this signals need to close/reopen connection
                return bytes()  # data empty
            else:
                logger.error("Error: Receive on HTTP Client '%s'."
                              " '%s'\n", self.ha, ex)
                raise  # re-raise

        if data:  # connection open
            if self.wl:  # log over the wire rx
                self.wl.writeRx(data, self.ha)
        else:  # data empty so connection closed on other end, whereas see above for blocked
            self.cutoff = True

        return data


    def serviceReceives(self):
        """
        Service receives until no more
        """
        while self.connected and not self.cutoff:
            data = self.receive()
            if not data:
                break
            self.rxbs.extend(data)


    def serviceReceiveOnce(self):
        '''
        Retrieve from server only one reception
        '''
        if self.connected and not self.cutoff:
            data = self.receive()
            if data:
                self.rxbs.extend(data)


    def clearRxbs(self):
        """
        Clear .rxbs
        """
        del self.rxbs[:]


    def send(self, data):
        """
        Perform non blocking send on connected socket .cs.
        Return number of bytes sent
        data is string in python2 and bytes in python3
        """
        try:
            count = self.cs.send(data)  # result is number of bytes sent
        except OSError as ex:
            # ex.args[0] == ex.errno for better os compatibility.
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                count = 0  # blocked try again
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED):

                self.cutoff = True  # this signals need to close/reopen connection
                count = 0
            else:
                logger.error("Error: Send on HTTP Client '%s'."
                              " '%s'\n", self.ha, ex)
                raise

        if count:
            if self.wl:
                self.wl.writeTx(data[:count], self.ha)

        return count


    def tx(self, data):
        """
        Copy data onto .txbs, .extend copies data.
        """
        self.txbs.extend(data)


    def serviceSends(self):
        """
        Service sends (transmits) of data in .txbs bytearray
        Attempt to send all of .txbs. Delete what is actually sent.
        """
        while self.txbs and self.connected and not self.cutoff:
            count = self.send(self.txbs)
            del self.txbs[:count]
            break  # try again later


    def service(self):
        """
        Service connect, txbs, and receives.
        """
        self.serviceConnect()
        self.serviceSends()
        self.serviceReceives()



class ClientTls(Client):
    """
    Outgoer with Nonblocking TLS/SSL support
    Nonblocking TCP Socket Client Class.

    Attributes:


    Properties:


    Methods:
    """
    def __init__(self,
                 context=None,
                 version=None,
                 certify=None,
                 hostify=None,
                 certedhost="",
                 keypath=None,
                 certpath=None,
                 cafilepath=None,
                 **kwa):
        """
        Initialization method for instance.

        IF no context THEN create one
        IF no version THEN create using library default
        IF certify is not None then use certify else use default
        IF hostify is not none the use hostify else use default

        Parameters:
            context = context object for tls/ssl If None use default
            version = ssl version If None use default
            certify = cert requirement If None use default
                      ssl.CERT_NONE = 0
                      ssl.CERT_OPTIONAL = 1
                      ssl.CERT_REQUIRED = 2
            keypath = pathname of local client side PKI private key file path
                      If given apply to context
            certpath = pathname of local client side PKI public cert file path
                      If given apply to context
            cafilepath = Cert Authority file path to use to verify server cert
                      If given apply to context
            hostify = verify server hostName If None use default
            certedhost = server's certificate common name (hostname) to check against
        """
        super(ClientTls, self).__init__(**kwa)

        self._connected = False  # attributed supporting connected property

        if context is None:  # create context
            if not version:  # use default context
                context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
                context.verify_flags &= ~ssl.VERIFY_X509_STRICT  # XXXX new with python 3.13
                # XXXX ToDo create new test certificates that are RFC 5280 compliant
                hostify = hostify if hostify is not None else context.check_hostname
                context.check_hostname = hostify
                certify = certify if certify is not None else context.verify_mode
                context.verify_mode = certify

            else:  # create context with specified protocol version
                context = ssl.SSLContext(version)
                # disable bad protocols versions
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3
                # disable compression to prevent CRIME attacks (OpenSSL 1.0+)
                context.options |= getattr(ssl._ssl, "OP_NO_COMPRESSION", 0)
                context.verify_mode = certify = ssl.CERT_REQUIRED if certify is None else certify
                context.check_hostname = hostify = True if hostify else False

        self.context = context
        self.certedhost = certedhost or self.hostname

        if cafilepath:
            context.load_verify_locations(cafile=cafilepath,
                                          capath=None,
                                          cadata=None)
        elif context.verify_mode != ssl.CERT_NONE:
            context.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)

        if keypath or certpath:
            context.load_cert_chain(certfile=certpath, keyfile=keypath)

        if hostify and certify == ssl.CERT_NONE:
            raise ValueError("Check Hostname needs a SSL context with "
                             "either CERT_OPTIONAL or CERT_REQUIRED")

    @property
    def connected(self):
        """
        Property that returns connected state of TCP socket
        TLS tcp is connected when accepted and handshake completed
        """
        return self._connected

    @connected.setter
    def connected(self, value):
        """
        setter for connected property
        """
        self._connected = value

    def close(self):
        """
        Shutdown and close connected socket .cs
        """
        if self.cs:
            self.shutdown()
            self.cs.close()  #close socket
            self.cs = None
            self.accepted = False
            self.connected = False
            self.opened = False


    def wrap(self):
        """
        Wrap socket .cs in ssl context
        """
        self.cs = self.context.wrap_socket(self.cs,
                                           server_side=False,
                                           do_handshake_on_connect=False,
                                           server_hostname=self.certedhost)

    def handshake(self):
        """
        Attempt nonblocking ssl handshake to .ha
        Returns True if successful
        Returns False if not so try again later
        """
        try:
            self.cs.do_handshake()
        except OSError as ex:
            if ex.errno in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                return False
            elif ex.errno in (ssl.SSL_ERROR_EOF, ):
                self.close()
                raise   # should give up here nicely
            else:
                self.close()
                raise
        except OSError as ex:
            self.close()
            if ex.errno in (errno.ECONNABORTED, ):
                raise  # should give up here nicely
            raise
        except Exception as ex:
            self.close()
            raise

        self.connected = True
        return True

    def connect(self):
        """
        Attempt nonblocking connect to .ha
        Returns True if successful
        Returns False if not so try again later
        Connected when both accepted connection and TLS handshake complete
        """
        if not self.accepted:
            self.accept()

            if self.accepted:  # only do this once immediately after accepted
                if not self.certedhost:
                    self.certedhost = self.ha[0]
                self.wrap()

        if self.accepted and not self.connected:
            self.handshake()

        return self.connected

    def receive(self):
        """
        Perform non blocking receive from connected socket .cs

        If no data then returns None
        If connection closed then returns ''
        Otherwise returns data
        data is string in python2 and bytes in python3
        """
        try:
            data = self.cs.recv(self.bs)
        except OSError as ex:  # ssl.SSLError is a subtype of OSError
            # ex.args[0] == ex.errno for better os compatibility.
            # the value of a given errno.XXXXX may be different on each os
            if ex.args[0] in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                return None
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED,
                                ssl.SSLEOFError):

                self.cutoff = True  # this signals need to close/reopen connection
                return bytes()  # data empty
            else:
                logger.error("Error: Receive on HTTP ClientTLS '%s'."
                              " '%s'\n", self.ha, ex)
                raise  # re-raise

        if data:  # connection open

            if self.wl:  # log over the wire rx
                self.wl.writeRx(data, self.ha)
        else:  # data empty so connection closed on other end
            self.cutoff = True

        return data

    def send(self, data):
        """
        Perform non blocking send on connected socket .cs.
        Return number of bytes sent
        data is string in python2 and bytes in python3
        """
        try:
            result = self.cs.send(data) #result is number of bytes sent
        except OSError as ex:  # ssl.SSLError is a subtype of OSError
            # ex.args[0] == ex.errno for better os compatibility.
            # the value of a given errno.XXXXX may be different on each os
            if ex.args[0] in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                result = 0
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED,
                                ssl.SSLEOFError):

                self.cutoff = True  # this signals need to close/reopen connection
                result = 0
            else:
                logger.error("Error: Send on HTTP ClientTLS '%s'."
                              " '%s'\n", self.ha, ex)
                raise

        if result:
            if self.wl:
                self.wl.writeTx(data[:result], self.ha)

        return result



class ClientDoer(doing.Doer):
    """
    Basic TCP Client Doer

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .client is TCP Client instance

    """

    def __init__(self, client, **kwa):
        """
        Initialize instance.

        Parameters:
           client is TCP Client instance
        """
        super(ClientDoer, self).__init__(**kwa)
        self.client = client



    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(ClientDoer, self).wind(tymth)
        self.client.wind(tymth)


    def enter(self, *, temp=None):
        """Do 'enter' context actions.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any
        """
        # inject temp into file resources here if any

        if self.tymth:  # Doist or DoDoer winds is doers on enter
            self.client.wind(self.tymth)
        self.client.reopen()


    def recur(self, tyme):
        """"""
        self.client.service()


    def exit(self):
        """"""
        self.client.close()


