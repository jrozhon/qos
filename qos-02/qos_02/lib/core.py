import sys
from itertools import accumulate, count
from typing import Any, Callable, Optional, Protocol, Union

import simpy
from loguru import logger
from numpy.random import default_rng

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time}</green> | <level>{level}</level> | {message}",
)

BYTES_TO_BITS = 8


class PacketSourceProto(Protocol):
    env: simpy.Environment
    source_id: str
    destination: Union["DestinationProto", None]
    packet_interval: float
    packet_size: int

    def start(self) -> simpy.Process:
        ...

    def generate_packet(self) -> simpy.Event:
        ...


# class PacketSinkProto(Protocol):
#     env: simpy.Environment
#     sink_id: str
#     logged_packets: list[dict[str, float]]
#
#     def display_statistics(self) -> None:
#         ...
#
#     def process_packet(self, packet: "PacketProto") -> Optional[simpy.Event]:
#         ...


class DestinationProto(Protocol):
    env: simpy.Environment

    def process_packet(self, packet: "PacketProto") -> Optional[simpy.Event]:
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
    ports: list["SwitchPort"]


# class SwitchPortProto(Protocol):
#     env: simpy.Environment
#     port_no: int
#     capacity: int
#     transmission_rate: float
#     queue: simpy.Store
#     tap: Optional["NetworkTap"]
#     destination: Union["SwitchPortProto", "PacketSinkProto", None]
#
#     def transmit(self, packet: "PacketProto") -> simpy.Event:
#         ...
#
#     def process_packet(self, packet: "PacketProto") -> Optional[simpy.Event]:
#         ...


class PacketProto(Protocol):
    id: int
    size: int
    creation_time: float
    source: str
    # destination: Union[SwitchPortProto, PacketSinkProto]
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
    packet_interval : Union[Callable[[], float], float], optional
        The interval between packet generations, by default 1.0.
        Can be a callable function that returns a float value.
        Use functools.partial to pass arguments to the function.
        Or can be a float/int value.
    packet_size : int
        The size of the generated packets.
    """

    def __init__(
        self,
        env: simpy.Environment,
        source_id: str,
        destination: Union[DestinationProto, None] = None,
        packet_interval: Union[Callable[[], float], float] = 1.0,
        packet_size: Union[Callable[[], int], int] = 10,
        debug: bool = False,
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
        packet_interval : Union[Callable[[], float], float], optional
            The interval between packet generations, by default 1.0.
            Can be a callable function that returns a float value.
            Use functools.partial to pass arguments to the function.
            Or can be a float/int value.
        packet_size : Union[Callable[[], int], int], optional
            The size of the generated packets, by default 10.
            Can be a callable function that returns an int value.
            Use functools.partial to pass arguments to the function.
            Or can be an int value.
        """
        self.env = env
        self.source_id = source_id
        self.destination = destination
        self.packet_interval = packet_interval
        self.packet_size = packet_size
        self.debug = debug

        # start the packet generation process
        self.process = self.env.process(self.start())  # type: ignore

    def generate_packet(self) -> simpy.Event:
        """
        Generate a packet and send it to the destination switch.

        Returns
        -------
        simpy.Event
            Event signaling the generation and sending of a packet.
        """
        if isinstance(self.packet_interval, (int, float)):
            yield self.env.timeout(self.packet_interval)  # type: ignore
        else:
            yield self.env.timeout(self.packet_interval())  # type: ignore

        if isinstance(self.packet_size, (int, float)):
            _packet_size = int(self.packet_size)
        else:
            _packet_size = int(self.packet_size()) or 1  # handle zero

        if self.destination:
            packet = Packet(self.env, _packet_size, self.source_id)
            self.destination.process_packet(packet)
            if self.debug:
                logger.info(f"Source {self.source_id}. Generated: {packet}.")
        else:
            raise ValueError("No destination specified for packet source.")

    def start(self) -> simpy.Process:
        """
        Begin the packet generation process.

        Returns
        -------
        simpy.Process
            The packet generation process.
        """
        while True:
            yield self.env.process(self.generate_packet())  # type: ignore


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
    sink_id : Optional[str]
        Identifier of the sink where the packet was received.
    sink_time : Optional[float]
        Time at which the packet was received at the sink.
    """

    cnt: "count[int]" = count()

    def __init__(self, env: simpy.Environment, size: int, source: str) -> None:
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
        return f"Packet(id={self.id:6}, size={self.size:6.2f}, source={self.source})"


class SwitchPort:
    def __init__(
        self,
        env: simpy.Environment,
        port_no: int,
        capacity: int = 10,
        transmission_rate: float = 1,
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
            Maximum number of bytes that can be queued. This is how many packets
            can be in the queue/system at any given time.
        transmission_rate : float
            Rate at which packets are transmitted.
        """
        self.env = env
        self.port_no = port_no
        self.capacity = capacity
        self.transmission_rate = transmission_rate
        self.queue: simpy.Store = simpy.Store(env)
        self.destination: Optional[DestinationProto] = None
        self.cum_drop_count: int = 0  # total number of dropped packets
        self.byte_count: int = 0  # current number of bytes in queue
        self.cum_byte_count: int = 0  # total number of bytes processed
        self.packet_count: int = 0  # current number of packets in queue
        self.cum_packet_count: int = 0  # total number of packets processed
        self.processing: bool = False

        # start the packet processing process
        self.process = self.env.process(self.start())  # type: ignore

    def transmit(self, packet: PacketProto) -> simpy.Event:
        """
        Transmit the packet and record using tap if available.

        Parameters
        ----------
        packet : Packet
            The packet to transmit.

        Raises
        ------
        ValueError
            If no destination is specified for switch port.

        Returns
        -------
        simpy.Event
            Event to signal the completion of transmission.
        """

        # wait for transmission to complete
        yield self.env.timeout(BYTES_TO_BITS * packet.size / self.transmission_rate)
        # hand over packet to destination
        if self.destination:
            self.destination.process_packet(packet)
        else:
            raise ValueError("No destination specified for switch port.")

    def start(self) -> simpy.Process:
        """
        Start the packet processing process. This method runs indefinitely,
        processing packets as they arrive in the queue.

        Returns
        -------
        simpy.Process
            The packet processing process.
        """
        while True:
            packet = yield self.queue.get()  # type: ignore
            self.processing = True
            self.byte_count -= packet.size
            self.packet_count -= 1
            yield self.env.process(self.transmit(packet))  # type: ignore
            self.processing = False

    def process_packet(self, packet: PacketProto) -> Optional[simpy.Event]:
        """
        Process a packet by adding it to the queue if there is enough capacity.
        If the packet size exceeds the remaining capacity, the packet is dropped.

        Parameters
        ----------
        packet : PacketProto
            The packet to be processed.

        Returns
        -------
        Optional[simpy.Event]
            Event signaling the addition of the packet to the queue, or None if the packet is dropped.
        """
        _byte_count = self.byte_count + packet.size
        _packet_count = self.packet_count + 1
        self.cum_packet_count += 1
        self.cum_byte_count += packet.size

        if self.capacity is None:
            self.byte_count = _byte_count
            self.packet_count = _packet_count
            return self.queue.put(packet)

        if self.capacity and _byte_count > self.capacity:
            # dropped packet here
            self.cum_drop_count += 1
            return None
        else:
            self.byte_count = _byte_count
            self.packet_count = _packet_count
            return self.queue.put(packet)

    def __repr__(self) -> str:
        """
        String representation of the switch port.

        Returns
        -------
        str
            String representation of the switch port.
        """
        return f"SwitchPort(capacity={self.capacity}, transmission_rate={self.transmission_rate}, destination={self.destination})"


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
        Only meant as a collection of ports.

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
        self.ports: list[SwitchPort] = [
            SwitchPort(
                env,
                port_no=next(self.port_cnt),
                capacity=port_capacity,
                transmission_rate=port_transmission_rate,
            )
            for _ in range(num_ports)
        ]

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
    def __init__(self, env: simpy.Environment, port: SwitchPort) -> None:
        """
        Initialize a new network tap.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        port : SwitchPort
            The switch port to be tapped.
        """
        self.env = env
        self.port = port
        self.packet_count: list[int] = []
        self.byte_count: list[int] = []
        self.process = self.env.process(self.start())  # type: ignore

    def start(self) -> simpy.Process:
        """
        Start the network tap process. This method runs indefinitely,
        appending the packet count and byte count from the port to the respective lists every second.

        Returns
        -------
        simpy.Process
            The network tap process.
        """
        while True:
            yield self.env.timeout(1)  # type: ignore
            self.packet_count.append(self.port.packet_count)
            self.byte_count.append(self.port.byte_count)

    def __repr__(self) -> str:
        """
        String representation of the network tap.

        Returns
        -------
        str
            String representation of the network tap.
        """
        return f"NetworkTap(Last 10 packet counts={self.packet_count[-10:]}, last 10 byte counts={self.byte_count[-10:]})"


class PacketSink:
    """
    An endpoint for packets to be received and logged.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    sink_id : str
        Identifier for this packet sink.
    logged_packets : list[Dict[str, float]]
        A list of dictionaries. Each dictionary contains details about a packet.
    """

    def __init__(self, env: simpy.Environment, sink_id: str, debug: bool = False):
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
        self.delays: list[float] = []
        self.arrivals: list[float] = []
        self.interarrivals: list[float] = []
        self.last_arrival_time: float = 0
        self.debug = debug

    def process_packet(self, packet: PacketProto) -> Optional[simpy.Event]:
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
        self.delays.append(arrival_time - packet.creation_time)
        self.arrivals.append(arrival_time)
        self.interarrivals.append(arrival_time - self.last_arrival_time)
        self.last_arrival_time = arrival_time
        if self.debug:
            logger.info(
                f"{self}. Arrival time {arrival_time:6.2f}. Processed: {packet}"
            )
        return None

    def __repr__(self) -> str:
        """
        String representation of the packet sink.

        Returns
        -------
        str
            String representation of the packet sink.
        """
        return f"PacketSink(sink_id={self.sink_id}, logged_packets={len(self.logged_packets):6})"


class PacketFork:
    """
    Class to fork packets to different destinations based on the specified probabilities.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    probs : list[float]
        List of probabilities for each destination.
    cum_probs : list[float]
        Cumulative probabilities for each destination.
    destinations : list[Union[DestinationProto, None]]
        List of destinations for the packets.
    rng : numpy.random.Generator
        Random number generator.
    """

    def __init__(self, env: simpy.Environment, probs: list[float]):
        """
        Forks packets to different destinations based on the specified
        probabilities.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        probs : list[float]
            List of probabilities for each destination.
        """
        self.env = env
        self.probs = probs
        self.cum_probs = list(accumulate(probs))
        if not int(self.cum_probs[-1]) == 1:
            raise ValueError("Probabilities must sum to 1.")
        self.destinations: list[Union[DestinationProto, None]] = [None for _ in probs]
        self.rng = default_rng()

    def process_packet(self, packet: PacketProto) -> Optional[simpy.Event]:
        """
        Process a packet and send it to the appropriate destination.

        Parameters
        ----------
        packet : Packet
            The incoming packet.
        """
        for i, p in enumerate(self.cum_probs):
            r = self.rng.random()
            if r < p:
                if self.destinations[i] is not None:
                    return self.destinations[i].process_packet(packet)  # type: ignore
            else:
                raise ValueError("No destination specified for packet fork.")
        return None
