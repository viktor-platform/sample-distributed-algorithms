from threading import Thread
from time import sleep

import Pyro4
import Pyro4.naming as naming


class Process(object):
    """An object using Pyro4 functionality. With this class it is able to simulate a network for distributed
    algorithms.
    """

    def __init__(self, name: str, prefix: str = "sample"):
        """Initializes the process.

        Args:
            name (str): Name of the process used in the nameserver
            prefix (str, optional): Prefix of the process used in the nameserver. Defaults to "sample".
        """
        self._name = name  # Name of the process
        self._prefix = prefix
        self._neighbours = []
        self._data = dict()

    @Pyro4.expose
    @Pyro4.oneway
    def add_neighbour(self, proxy: Pyro4.Proxy):
        """Add a proxy as a neighbour so we can loop self._neighbours to send stuff to our neighbours"""
        self._neighbours.append(proxy)

    @property
    @Pyro4.expose
    def neighbours(self):
        """The neighbours of the proxy"""
        return self._neighbours

    @property
    @Pyro4.expose
    def data(self):
        """The dictionary of the process."""
        return self._data

    def run(self, *args):
        """This process should be overwritten when making the algorithms. Keeps the process alive."""
        while True:
            sleep(1)
            if self._killed:
                break

    @Pyro4.expose
    @Pyro4.oneway
    def start(self, *args):
        """Starts the run method in a thread."""
        self._killed = False
        self.thread = Thread(target=self.run, args=args)
        self.thread.start()

    @Pyro4.expose
    @Pyro4.oneway
    def stop(self):
        """Set the killed flag true so run can finish."""
        self._killed = True

    @Pyro4.expose
    @Pyro4.oneway
    def join(self):
        """Waits for the main thread to finish."""
        self.thread.join()

    def lookup(self, name, ns=None):
        """Look up a proxy on the name server

        Args:
            name: The name of the process you are trying to find.
            ns: The nameserver you are using.
        """
        if ns is None:
            ns = Pyro4.locateNS()
        uri = ns.lookup(f"{self._prefix}.{name}")
        return uri

    def register(self, daemon, ns=None):
        """Registers itself on the daemon and the ns

        Args:
            daemon: The daemon you want use for the requestloop
            ns: The nameserver you want to register to
        """
        if ns is None:
            ns = Pyro4.locateNS()
        uri = daemon.register(self)
        ns.register(str(self._prefix) + "." + str(self._name), uri)

    @property
    @Pyro4.expose
    def name(self):
        return self._name

    @property
    def uri(self):
        return self.lookup(self.name)

    @property
    def proxy(self):
        return Pyro4.Proxy(self.uri)


def start_daemon(daemon: Pyro4.Daemon) -> None:
    """Uses threading to start a daemon so we can run multiple in parallel."""
    Thread(target=daemon.requestLoop, args=()).start()


def start_name_server() -> Pyro4.Daemon:
    """Start the name server and returns the daemon"""
    _, nameserverDaemon, _ = naming.startNS()
    start_daemon(nameserverDaemon)
    return nameserverDaemon
