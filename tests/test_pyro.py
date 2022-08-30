import unittest
from app.hirschberg.pyro import Process, start_name_server, start_daemon
import Pyro4


class PyroTest(unittest.TestCase):
    def test_process_creation(self):
        nameserverDaemon = start_name_server()
        daemon = Pyro4.Daemon()
        try:
            ns = Pyro4.locateNS()
            p1 = Process('p1')
            p1.register(daemon,ns)
            start_daemon(daemon)
            uri = ns.lookup('sample.p1')
            proxy = Pyro4.Proxy(uri)
            name = proxy.name
            nameserverDaemon.shutdown()
            daemon.shutdown()
        except Exception:
            # Always close the daemons when an exception is raised
            nameserverDaemon.shutdown()
            daemon.shutdown()
        self.assertEqual(name,'p1')


if __name__ == '__main__':
    unittest.main()