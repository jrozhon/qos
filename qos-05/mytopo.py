"""Custom Mininet topology for Exercise 05.

Three switches in a tree, one host on each, and traffic-control parameters on
the inter-switch links. Run on a laboratory server with

    sudo mn --custom mytopo.py --topo mytopo --mac --link tc

The ``topos`` dictionary at the end registers the topology under the name
passed to ``--topo``.
"""

from mininet.topo import Topo


class MyTopo(Topo):
    """Tree of three switches with one host each and impaired inter-switch links."""

    def __init__(self, loss=0):
        Topo.__init__(self)

        # Hosts
        h1 = self.addHost("h1", ip="10.1.0.11/8")
        h2 = self.addHost("h2", ip="10.1.0.22/8")
        h3 = self.addHost("h3", ip="10.1.0.33/8")

        # Switches
        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")

        # Access links
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)

        # Inter-switch links: bandwidth [Mbit/s], delay, loss [%]
        self.addLink(s1, s2, bw=10, delay="30ms", loss=loss)
        self.addLink(s1, s3, bw=15, delay="50ms", loss=loss)


topos = {"mytopo": lambda: MyTopo(), "mytopo_lossy": lambda: MyTopo(loss=2)}
