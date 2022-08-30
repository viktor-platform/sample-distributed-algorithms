from enum import Enum
from time import sleep
from time import time_ns

import numpy as np
import pandas as pd
import Pyro4

from viktor.core import progress_message

from .pyro import Process
from .pyro import start_daemon
from .pyro import start_name_server


class State(Enum):
    """Possible states for each Hirschberg Process"""

    IDLE = 0
    SEND_OUT = 1
    SEND_IN = 2
    RECEIVE_OUT = 3
    RECEIVE_IN = 4
    SELECTED = 5


class Hirschberg(Process):
    """Process that will follow the Hirschberg and Sinclair algorithm."""

    def __init__(self, name: int, id_: int, number_of_nodes: int):
        """Initializes the process.

        Args:
            name (int): The name of the process used for plotting.
            id_ (int): The id of the process used for leader selection.
            number_of_nodes (int): Known number of nodes in the network.
        """
        super().__init__(name)
        self.id = int(id_)
        self.l = 0
        self.number_of_nodes = number_of_nodes
        self._elected = False
        self._data = {"name": [], "id": [], "round": [], "clock": [], "state": []}

    def add_data(self, state: State = State.IDLE, clock: int = None):
        """Adds the current state to the data dictionary. Can later be used for plotting
        and viewing the results.

        Args:
            state (State, optional): The current state of the process. Defaults to State.IDLE.
            clock (int, optional): The current time the state occurs. Defaults to None.
        """
        self._data["name"].append(self._name)
        self._data["id"].append(self.id)
        self._data["round"].append(self.l)
        if clock is None:
            self._data["clock"].append(time_ns())
        else:
            self._data["clock"].append(clock)
        self._data["state"].append(state.name)

    def run(self):
        """Starts the first round of the algorithm."""
        # Initiating the election
        self.l = 1
        self.add_data(state=State.IDLE, clock=0)  # For plotting
        self.counter = 0
        self.send_out(self.id, self.l, self._neighbours)

    def other_neighbour(self, sender: Pyro4.Proxy) -> Pyro4.Proxy:
        """Returns the neighbour on the other side then the message received.

        Args:
            sender (Pyro4.Proxy): The proxy of the sender.

        Returns:
            Pyro4.Proxy: The neighbour other then the sender.
        """
        for neighbour in self._neighbours:
            if neighbour != sender:
                break
        return neighbour

    @property
    @Pyro4.expose
    def elected(self):
        """Returns True if the process is elected as leader."""
        return self._elected

    @Pyro4.expose
    @Pyro4.oneway
    def receive_out(self, nid: int, h: int, sender: Pyro4.Proxy):
        """Receives and outgoing message asking to compare the id. Sends its own id
        back if it is in the same round. Otherwise forwards to other neighbour.

        Args:
            nid (int): The id of the neighbour to compare.
            h (int): Hops of the previous message.
            sender (Pyro4.Proxy): The proxy of the sender of the message.
        """
        self.add_data(state=State.RECEIVE_OUT)
        if nid > self.id:
            h = h - self.l
            if h > 0:
                self.send_out(nid, h, self.other_neighbour(sender))
            else:
                self.send_in(nid, sender)

    @Pyro4.expose
    @Pyro4.oneway
    def receive_in(self, nid: int, sender: Pyro4.Proxy):
        """Receives an incoming message with an id to compare itself to.
        Is elected if the incoming message is from the farthest neighbour
        else starts a new round.

        Args:
            nid (int): Id of the furthest current node.
            sender (Pyro4.Proxy): Proxy of the neighbour that has
            send the message.
        """
        self.add_data(state=State.RECEIVE_IN)
        if nid == self.id:
            self.counter += 1
            if self.counter == 2:
                if 2**self.l + 1 >= self.number_of_nodes:
                    self._elected = True
                    # Data below is just for plotting
                    print(f"{self._name} is elected with value {self.id}!")
                    self.l += 1
                    self.add_data(state=State.SELECTED)
                else:
                    self.l += 1
                    self.counter = 0
                    self.send_out(self.id, 2 ** (self.l - 1), self._neighbours)

        else:
            self.send_in(nid, self.other_neighbour(sender))

    def send_out(self, nid: int, h: int, neighbours: Pyro4.Proxy):
        """Send an outgoing message requesting the furthest id.

        Args:
            nid (int): id of the original sender.
            h (int): Hopcount.
            neighbours (Pyro4.Proxy): The neighbours to send the message to.
        """
        self.add_data(state=State.SEND_OUT)
        if type(neighbours) == Pyro4.Proxy:
            neighbours = [neighbours]
        for neighbour in neighbours:
            neighbour.receive_out(nid, h, self.proxy)

    def send_in(self, nid: int, neighbours: Pyro4.Proxy):
        """Send an ingoing message with and id to compare.

        Args:
            nid (int): Id of the furthest node in the round.
            neighbours (Pyro4.Proxy): The proxy of the sender.
        """
        self.add_data(state=State.SEND_IN)
        if type(neighbours) == Pyro4.Proxy:
            neighbours = [neighbours]
        for neighbour in neighbours:
            neighbour.receive_in(nid, self.proxy)


def run_hirschberg_sinclair_algorithm(number_of_nodes: int) -> pd.DataFrame:
    """Creates a network and runs the Hirschberg and Sinclair algorithm for leader
    election in a bidirectional ring.

    Args:
        number_of_nodes (int): Number of nodes in the network.

    Returns:
        pd.DataFrame: The results of the algorithm.
    """
    p_message = "Starting name server"
    progress_message(message=p_message)
    nameserverDaemon = start_name_server()
    daemon = Pyro4.Daemon()
    Pyro4.config.THREADPOOL_SIZE = 400
    try:
        ns = Pyro4.locateNS()

        # Create deamon
        p_message += "\nCreating daemon"
        progress_message(message=p_message, percentage=0)
        proxies = []
        ids = [np.random.randint(1, number_of_nodes**4) for _ in range(number_of_nodes)]
        for name, id_ in zip(range(number_of_nodes), ids):
            progress_message(message=p_message, percentage=name / number_of_nodes * 100)
            process = Hirschberg(name, id_, number_of_nodes)
            process.register(daemon, ns)
            proxies.append(Pyro4.Proxy(ns.lookup(f"sample.{name}")))
        start_daemon(daemon)

        # Connect nodes to create a ring
        p_message += "\nCreating network"
        progress_message(message=p_message, percentage=0)
        for idx, proxy in enumerate(proxies):
            progress_message(message=p_message, percentage=idx / number_of_nodes * 100)
            right = idx - 1
            left = idx + 1
            if left >= len(proxies):
                left = 0
            proxy.add_neighbour(proxies[right])
            proxy.add_neighbour(proxies[left])

        # Start nodes
        p_message += "\nRunning algorithm"
        progress_message(message=p_message)
        for proxy in proxies:
            proxy.start()

        # Check if node is elected. In reality we would need to implement an algorithm that checks if an algorithm is elected but for
        # the purpose of demonstrating we check only the node we know is going to win. In a real distributed system this is unknown.
        sleep(number_of_nodes)
        max_value = np.max(ids)
        idx = np.where(ids == max_value)[0][0]
        proxy = proxies[idx]
        while True:
            if proxy.elected:
                break
            sleep(1)

        # Shutdown
        p_message += "\nFinishing up"
        progress_message(message=p_message)
        df = pd.DataFrame()
        for proxy in proxies:
            proxy_df = pd.DataFrame(proxy.data)
            df = pd.concat([df, proxy_df])
            proxy.stop()
        daemon.shutdown()
        nameserverDaemon.shutdown()
        df = df.sort_values(by=["round", "clock", "name"])
        p_message += "\nPlotting data"
        progress_message(message=p_message)

        return df
    except Exception as err:
        # Always close the daemons when an exception is raised
        daemon.shutdown()
        nameserverDaemon.shutdown()
        raise
