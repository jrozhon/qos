from itertools import count
from typing import Optional, Protocol, Union

import networkx as nx
import simpy
from bokeh.io import output_notebook, show
from bokeh.models import (Circle, GraphRenderer, HoverTool, MultiLine, Rect,
                          StaticLayoutProvider)
from bokeh.plotting import figure, from_networkx, show


class PacketSourceProto(Protocol):
    env: simpy.Environment
    source_id: str
    destination: Union["SwitchProto", "PacketSinkProto"]
    packet_interval: float
    packet_size: int

    def start(self) -> simpy.Process:
        ...

    def generate_packet(self) -> simpy.Event:
        ...


class PacketSinkProto(Protocol):
    env: simpy.Environment
    sink_id: str
    logged_packets: list[dict[str, float]]

    def display_statistics(self) -> None:
        ...

    def receive_packet(self, packet: "PacketProto") -> None:
        ...


class NetworkTapProto(Protocol):
    env: simpy.Environment
    packet_count: int
    packet_sizes: list[int]
    packet_times: list[float]

    def display_statistics(self) -> None:
        ...

    def tap_packet(self, packet: "PacketProto") -> None:
        ...


class SwitchProto(Protocol):
    env: simpy.Environment
    id: str
    port_cnt: int
    ports: list["SwitchPortProto"]

    def route_packet(self, packet: "PacketProto") -> None:
        ...


class SwitchPortProto(Protocol):
    env: simpy.Environment
    port_no: int
    capacity: int
    transmission_rate: float
    queue: simpy.Store
    tap: Optional["NetworkTap"]
    destination: Optional["Switch"]

    def transmit(self, packet: "PacketProto") -> simpy.Event:
        ...


class PacketProto(Protocol):
    id: int
    size: int
    creation_time: float
    source: PacketSourceProto
    destination: Union[SwitchProto, PacketSinkProto]
    sink_id: Optional[str]
    sink_time: Optional[float]


class PacketSource:
    """
    Generates packets with specified inter-arrival times and sends them to a
    designated switch.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    source_id : str
        Identifier for this packet source.
    destination : Switch
        The switch to which generated packets will be sent.
    packet_interval : float
        The average interval between packet generations.
    packet_size : int
        The size of the generated packets.
    """

    def __init__(
        self,
        env: simpy.Environment,
        source_id: str,
        destination: Union[SwitchProto, PacketSinkProto],
        packet_interval: float = 1.0,
        packet_size: int = 10,
    ):
        """
        Initialize a new packet source.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        source_id : str
            Identifier for this packet source.
        destination : Union[Switch, PacketSink]
            The switch or sink to which generated packets will be sent.
        packet_interval : float, optional
            The average interval between packet generations, by default 1.0.
        packet_size : int, optional
            The size of the generated packets, by default 10.
        """
        self.env = env
        self.source_id = source_id
        self.destination = destination
        self.packet_interval = packet_interval
        self.packet_size = packet_size

    def generate_packet(self) -> simpy.Event:
        """
        Generate a packet and send it to the destination switch.

        Returns
        -------
        simpy.Event
            Event signaling the generation and sending of a packet.
        """
        yield self.env.timeout(self.packet_interval)

        packet = Packet(self.env, self.packet_size, self.source_id, self.destination)
        self.destination.route_packet(packet)

    def start(self) -> simpy.Process:
        """
        Begin the packet generation process.

        Returns
        -------
        simpy.Process
            The packet generation process.
        """
        while True:
            yield self.env.process(self.generate_packet())


class Packet:
    """
    Packet class to represent a data packet.

    Attributes
    ----------
    id : int
        Unique identifier for this packet.
    size : int
        Size of the packet.
    creation_time : float
        Time at which the packet was created.
    source : str
        Source identifier.
    destination : Union[Switch, PacketSink]
        Destination object to which the packet is being sent.
    sink_id : Optional[str]
        Identifier of the sink where the packet was received.
    sink_time : Optional[float]
        Time at which the packet was received at the sink.
    """

    cnt: count[int] = count()

    def __init__(
        self,
        env: simpy.Environment,
        size: int,
        source: PacketSourceProto,
        destination: Union[SwitchProto, PacketSinkProto],
    ) -> None:
        """
        Packet class to represent a data packet.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        size : int
            Size of the packet.
        source : str
            Source identifier.
        destination : str
            Destination identifier.
        """
        self.id = int(next(Packet.cnt))
        self.size = size
        self.creation_time: float = env.now
        self.source = source
        self.destination = destination
        self.sink_id: Optional[str] = None
        self.sink_time: Optional[float] = None

    def __repr__(self) -> str:
        """
        String representation of the packet.

        Returns
        -------
        str
            String representation of the packet.
        """
        return f"Packet(id={self.id}, size={self.size}, source={self.source}, destination={self.destination})"


class SwitchPort:
    def __init__(
        self,
        env: simpy.Environment,
        port_no: int,
        capacity: int = 10,
        transmission_rate: float = 1,
        tap: Optional["NetworkTap"] = None,
    ) -> None:
        """
        Switch port to queue and transmit packets.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        port_no : int
            Port number.
        capacity : int
            Maximum number of packets that can be queued.
        transmission_rate : float
            Rate at which packets are transmitted.
        tap : NetworkTap, optional
            Optional tap for monitoring traffic, by default None.
        """
        self.env = env
        self.port_no = port_no
        self.capacity = capacity
        self.transmission_rate = transmission_rate
        self.queue: simpy.Store = simpy.Store(env)
        self.tap = tap
        self.destination: Optional[Switch] = None

    def transmit(self, packet: PacketProto) -> simpy.Event:
        """
        Transmit the packet and record using tap if available.

        Parameters
        ----------
        packet : Packet
            The packet to transmit.

        Returns
        -------
        simpy.Event
            Event to signal the completion of transmission.
        """
        if self.tap:
            self.tap.tap_packet(packet)
        yield self.env.timeout(packet.size / self.transmission_rate)

    def __repr__(self) -> str:
        """
        String representation of the switch port.

        Returns
        -------
        str
            String representation of the switch port.
        """
        return f"SwitchPort(capacity={self.capacity}, transmission_rate={self.transmission_rate})"


class Switch:
    def __init__(
        self,
        env: simpy.Environment,
        switch_id: str,
        num_ports: int,
        port_capacity: int,
        port_transmission_rate: float,
    ) -> None:
        """
        Network switch containing multiple ports.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        switch_id : str
            Identifier for this switch.
        num_ports : int
            Number of ports in the switch.
        port_capacity : int
            Capacity of each port.
        port_transmission_rate : float
            Transmission rate of each port.
        """
        self.env = env
        self.id = switch_id
        self.port_cnt = count()
        self.ports: list[SwitchPortProto] = [
            SwitchPort(
                env,
                port_no=next(self.port_cnt),
                capacity=port_capacity,
                transmission_rate=port_transmission_rate,
            )
            for _ in range(num_ports)
        ]

    def route_packet(self, packet: PacketProto) -> None:
        """
        Route the packet to an available port.

        Parameters
        ----------
        packet : Packet
            The packet to route.
        """
        for port in self.ports:
            if port.destination:
                if isinstance(port.destination, PacketSink):
                    port.destination.receive_packet(packet)
                    return
                elif packet.destination == port.destination:
                    port.queue.put(packet)
                    self.env.process(port.transmit(packet))
                    break

    def __repr__(self) -> str:
        """
        String representation of the switch.

        Returns
        -------
        str
            String representation of the switch.
        """
        return f"Switch(id={self.id}, ports={len(self.ports)})"


class NetworkTap:
    def __init__(self, env: simpy.Environment) -> None:
        """
        Tap to monitor network traffic.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        """
        self.env = env
        self.packet_count: int = 0
        self.packet_sizes: list[int] = []
        self.packet_times: list[float] = []

    @property
    def total_size(self) -> int:
        """
        Total size of packets observed by the tap.

        Returns
        -------
        int
            Total size of packets observed by the tap.
        """
        return sum(self.packet_sizes)

    def tap_packet(self, packet: PacketProto) -> None:
        """
        Record details of a packet as it's observed by the tap.

        Parameters
        ----------
        packet : Packet
            The observed packet.
        """
        self.packet_count += 1
        self.packet_sizes.append(packet.size)
        self.packet_times.append(self.env.now)  # Store the time of packet observation

    def display_statistics(self) -> None:
        """
        Display statistics related to packets observed by the tap.
        """
        print("----- Network Tap Statistics -----")

        # Total number of packets
        print(f"Total Packets Observed: {self.packet_count}")

        # Total size of packets
        print(f"Total Size of Packets: {self.total_size} units")

        # Average size of packets
        if self.packet_count:
            avg_size = self.total_size / self.packet_count
            print(f"Average Packet Size: {avg_size:.2f} units")
        else:
            print("Average Packet Size: 0 units")

        # Average time between packets (Inter-arrival time)
        if self.packet_count > 1:
            inter_arrival_times = [
                self.packet_times[i + 1] - self.packet_times[i]
                for i in range(len(self.packet_times) - 1)
            ]
            avg_inter_arrival_time = sum(inter_arrival_times) / (self.packet_count - 1)
            print(
                f"Average Inter-Arrival Time: {avg_inter_arrival_time:.2f} time units"
            )
        else:
            print("Average Inter-Arrival Time: N/A")

        print("------------------------------")

    def __repr__(self) -> str:
        """
        String representation of the network tap.

        Returns
        -------
        str
            String representation of the network tap.
        """
        return f"NetworkTap(packet_count={self.packet_count}, total_size={self.total_size})"


class PacketSink:
    """
    An endpoint for packets to be received and logged.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    sink_id : str
        Identifier for this packet sink.
    logged_packets : List[Dict[str, float]]
        A list of dictionaries. Each dictionary contains details about a packet.
    """

    def __init__(self, env: simpy.Environment, sink_id: str):
        """
        Initialize a new packet sink.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        sink_id : str
            Identifier for this packet sink.
        """
        self.env = env
        self.sink_id = sink_id
        self.logged_packets: list[PacketProto] = []

    def receive_packet(self, packet: PacketProto):
        """
        Receive a packet and log its details.

        Parameters
        ----------
        packet : Packet
            The incoming packet.
        """
        arrival_time = self.env.now
        packet.sink_id = self.sink_id
        packet.sink_time = arrival_time
        self.logged_packets.append(packet)

    def display_statistics(self):
        """
        Display the logged information about received packets.
        """
        for packet_info in self.logged_packets:
            print(
                f"Packet from {packet_info['source_id']} arrived at {packet_info['arrival_time']:.2f} with length {packet_info['length']}"
            )

    def __repr__(self) -> str:
        """
        String representation of the packet sink.

        Returns
        -------
        str
            String representation of the packet sink.
        """
        return f"PacketSink(sink_id={self.sink_id}, logged_packets={len(self.logged_packets)})"


def visualize_topology(
    switches: List[Switch], sources: List[PacketSource], sinks: List[PacketSink]
) -> None:
    """
    Visualizes the network topology using Bokeh and networkx. PacketSources are represented as circles,
    Switches as rectangles (squares), and PacketSinks as circles as well.

    Parameters
    ----------
    switches : List[Switch]
        List of switch instances.
    sources : List[PacketSource]
        List of packet source instances.
    sinks : List[PacketSink]
        List of packet sink instances.

    Returns
    -------
    None
        The function displays the plot in the Jupyter notebook but doesn't return any values.
    """

    # Create a new networkx graph
    G = nx.Graph()

    # Add nodes
    for src in sources:
        G.add_node(f"Src: {src.source_id}", node_type="source")
    for sw in switches:
        G.add_node(sw.id, node_type="switch")
    for sk in sinks:
        G.add_node(f"Sink: {sk.sink_id}", node_type="sink")

    # Add edges from sources to their respective destinations
    for src in sources:
        G.add_edge(f"Src: {src.source_id}", src.destination.id)

    # Get spring layout positions from networkx
    layout = nx.spring_layout(G)

    # Create Bokeh graph renderer
    graph = GraphRenderer()

    # Extract positions from networkx spring layout and convert them to tuples
    graph_layout = {node: tuple(pos) for node, pos in layout.items()}

    # Nodes and edges for Bokeh graph
    node_indices = list(G.nodes())
    start, end = zip(*G.edges())

    # Create a node type list for styling the glyphs later
    node_types = [G.nodes[node]["node_type"] for node in node_indices]

    # Set up the graph renderer data
    graph.node_renderer.data_source.data = dict(index=node_indices, type=node_types)
    graph.edge_renderer.data_source.data = dict(start=start, end=end)

    # Set the node glyphs
    graph.node_renderer.glyph = Circle(size=15, fill_color="skyblue")
    graph.node_renderer.selection_glyph = Circle(size=15, fill_color="firebrick")
    graph.node_renderer.hover_glyph = Circle(size=15, fill_color="orange")

    # Set the edge glyphs
    graph.edge_renderer.glyph = MultiLine(
        line_color="black", line_alpha=0.8, line_width=2
    )

    # Use the spring layout positions in the Bokeh graph
    graph.layout_provider = StaticLayoutProvider(graph_layout=graph_layout)

    # Create a plot for rendering
    plot = figure(
        title="Network Topology",
        x_range=(-1.5, 1.5),
        y_range=(-1.5, 1.5),
        tools="",
        toolbar_location=None,
    )
    plot.renderers.append(graph)

    # Add hover tool for node info
    node_hover_tool = HoverTool(tooltips=[("Node", "@index"), ("Type", "@type")])
    plot.add_tools(node_hover_tool)

    # Display in notebook
    output_notebook()
    show(plot)
