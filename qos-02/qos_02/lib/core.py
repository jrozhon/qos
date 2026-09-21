"""
Discrete-event building blocks for the Exercise 02 queueing simulations.

The components form a pipeline that is wired by assigning ``destination``
attributes::

    PacketSource -> SwitchPort -> PacketSink

A :class:`NetworkTap` may be attached to a :class:`SwitchPort` to sample its
occupancy, and a :class:`PacketFork` splits a stream probabilistically.

Throughout this module the *queue* means the packets waiting in the buffer and
the *system* means the queue plus the packet currently being transmitted. The
attribute names follow that distinction: ``queue_packets`` and ``queue_bytes``
exclude the packet in service, whereas
:attr:`SwitchPort.packets_in_system` and :attr:`SwitchPort.bytes_in_system`
include it. The M/M/1 quantities $L_q$ and $W_q$ refer to the queue, $L$ and $W$
to the system.

One simulation time unit (STU) represents one second in this exercise.
"""

import sys
from bisect import bisect_right
from itertools import accumulate, count
from math import isclose
from typing import Callable, Optional, Protocol, Union

import simpy
from loguru import logger
from numpy.random import Generator, default_rng

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time}</green> | <level>{level}</level> | {message}",
)

BYTES_TO_BITS = 8

#: A quantity that is either a fixed number or a zero-argument callable
#: returning a number. Use :func:`functools.partial` to bind the arguments of a
#: random generator method, for example ``partial(rng.exponential, 2)``.
Variate = Union[Callable[[], float], float]


def draw(value: Variate) -> float:
    """
    Resolve a simulation parameter that may be a constant or a callable.

    Parameters
    ----------
    value : Union[Callable[[], float], float]
        Either a number, returned unchanged, or a zero-argument callable that
        is called once and whose result is returned.

    Returns
    -------
    float
        The resolved value.
    """
    return float(value()) if callable(value) else float(value)


# --------------------------------------------------------------------------- #
# Public interfaces
# --------------------------------------------------------------------------- #


class PacketProto(Protocol):
    """Unit of traffic moving through the simulated network."""

    id: int
    size: int
    creation_time: float
    source: str
    sink_id: Optional[str]
    sink_time: Optional[float]


class DestinationProto(Protocol):
    """Anything a packet can be handed to: a port, a fork, or a sink."""

    env: simpy.Environment

    def process_packet(self, packet: PacketProto) -> Optional[simpy.Event]: ...


class PacketSourceProto(Protocol):
    """Generator of packets at a given rate and size distribution."""

    env: simpy.Environment
    source_id: str
    destination: Optional[DestinationProto]
    packet_interval: Variate
    packet_size: Variate
    packets_sent: int

    def generate_packet(self) -> simpy.Event: ...

    def start(self) -> simpy.Process: ...


class SwitchPortProto(DestinationProto, Protocol):
    """Single server with a finite buffer, draining at a fixed bit rate."""

    port_no: int
    capacity: Optional[int]
    transmission_rate: float
    queue: simpy.Store
    destination: Optional[DestinationProto]
    queue_packets: int
    queue_bytes: int
    cum_packet_count: int
    cum_byte_count: int
    cum_drop_count: int

    @property
    def packets_in_system(self) -> int: ...

    @property
    def bytes_in_system(self) -> int: ...

    def transmit(self, packet: PacketProto) -> simpy.Event: ...

    def start(self) -> simpy.Process: ...


class SwitchProto(Protocol):
    """Collection of independent ports sharing an identifier."""

    env: simpy.Environment
    id: str
    ports: list[SwitchPortProto]


class PacketSinkProto(DestinationProto, Protocol):
    """Endpoint recording the time each packet spent in the network."""

    sink_id: str
    logged_packets: list[PacketProto]
    delays: list[float]
    arrivals: list[float]
    interarrivals: list[float]


class NetworkTapProto(Protocol):
    """Periodic sampler of the occupancy of one port."""

    env: simpy.Environment
    port: SwitchPortProto
    interval: float
    times: list[float]
    system_packets: list[int]
    queue_packets: list[int]
    queue_bytes: list[int]

    def start(self) -> simpy.Process: ...


# --------------------------------------------------------------------------- #
# Implementations
# --------------------------------------------------------------------------- #


class Packet:
    """
    A data packet moving through the simulated network.

    Attributes
    ----------
    id : int
        Unique identifier, taken from a counter shared by all packets.
    size : int
        Size of the packet [B].
    creation_time : float
        Simulation time at which the packet was created [STU].
    source : str
        Identifier of the source that created the packet.
    sink_id : Optional[str]
        Identifier of the sink that received the packet, None while in transit.
    sink_time : Optional[float]
        Simulation time at which the packet reached a sink [STU], None while in
        transit.
    """

    cnt: "count[int]" = count()

    def __init__(self, env: simpy.Environment, size: int, source: str) -> None:
        """
        Create a packet stamped with the current simulation time.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        size : int
            Size of the packet [B].
        source : str
            Identifier of the generating source.
        """
        self.id = int(next(Packet.cnt))
        self.size = size
        self.creation_time: float = env.now
        self.source = source
        self.sink_id: Optional[str] = None
        self.sink_time: Optional[float] = None

    @classmethod
    def reset_counter(cls) -> None:
        """
        Restart packet numbering at zero.

        The counter is shared by every packet in the kernel session, so packet
        identifiers keep growing when a notebook cell is re-run. Call this
        together with a fresh :class:`simpy.Environment` to make the logs of a
        repeated simulation identical.
        """
        cls.cnt = count()

    def __repr__(self) -> str:
        """
        String representation of the packet.

        Returns
        -------
        str
            String representation of the packet.
        """
        return f"Packet(id={self.id:6}, size={self.size:6} B, source={self.source})"


class PacketSource:
    """
    Generates packets with given inter-arrival times and sizes.

    Drawing each inter-arrival time from an exponential distribution makes the
    generated stream a Poisson process, which is the arrival model assumed by
    the M/M/1 formulas.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    source_id : str
        Identifier for this packet source.
    destination : Optional[DestinationProto]
        Component the generated packets are handed to.
    packet_interval : Union[Callable[[], float], float]
        Interval between two packets [STU], a number or a zero-argument
        callable.
    packet_size : Union[Callable[[], float], float]
        Size of a generated packet [B], a number or a zero-argument callable.
        The drawn value is rounded to the nearest whole byte, with a floor of
        one byte.
    packets_sent : int
        Number of packets generated so far [–].
    """

    def __init__(
        self,
        env: simpy.Environment,
        source_id: str,
        destination: Optional[DestinationProto] = None,
        packet_interval: Variate = 1.0,
        packet_size: Variate = 10,
        debug: bool = False,
    ):
        """
        Initialize a new packet source and start generating.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        source_id : str
            Identifier for this packet source.
        destination : Optional[DestinationProto], optional
            The port, fork, or sink to which generated packets will be sent, by
            default None. It may also be assigned after construction.
        packet_interval : Union[Callable[[], float], float], optional
            The interval between packet generations [STU], by default 1.0. Use
            :func:`functools.partial` to bind the arguments of a random
            generator method, for example ``partial(rng.exponential, 2)``.
        packet_size : Union[Callable[[], float], float], optional
            The size of the generated packets [B], by default 10. Accepts a
            callable on the same terms as `packet_interval`.
        debug : bool, optional
            Log every generated packet, by default False.
        """
        self.env = env
        self.source_id = source_id
        self.destination = destination
        self.packet_interval = packet_interval
        self.packet_size = packet_size
        self.debug = debug
        self.packets_sent: int = 0

        # start the packet generation process
        self.process = self.env.process(self.start())  # type: ignore

    def generate_packet(self) -> simpy.Event:
        """
        Wait one inter-arrival time, then create a packet and hand it over.

        Raises
        ------
        ValueError
            If no destination has been assigned.

        Returns
        -------
        simpy.Event
            Event signaling the generation and sending of a packet.
        """
        yield self.env.timeout(draw(self.packet_interval))  # type: ignore

        if self.destination is None:
            raise ValueError("No destination specified for packet source.")

        # Round rather than truncate: truncation would shorten every packet by
        # half a byte on average and bias the service rate mu upwards.
        size = max(1, round(draw(self.packet_size)))
        packet = Packet(self.env, size, self.source_id)
        self.destination.process_packet(packet)
        self.packets_sent += 1
        if self.debug:
            logger.info(f"Source {self.source_id}. Generated: {packet}.")

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


class SwitchPort:
    """
    Output port that buffers waiting packets and transmits them one at a time.

    The port is the single server of the queueing model. A packet whose size
    does not fit in the remaining buffer space is dropped and counted in
    `cum_drop_count`. A packet larger than `capacity` is therefore dropped even
    when the buffer is empty, so a small buffer biases the sizes of the packets
    that get through. Transmitting a packet of `size` bytes takes
    ``8 * size / transmission_rate`` seconds, so exponentially distributed
    packet sizes at a constant rate give exponentially distributed service
    times, as M/M/1 assumes.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    port_no : int
        Port number within its switch.
    capacity : Optional[int]
        Buffer size [B], counting waiting packets only. None means unbounded.
    transmission_rate : float
        Rate at which the port drains its buffer [bit/s].
    queue : simpy.Store
        The waiting packets.
    destination : Optional[DestinationProto]
        Component transmitted packets are handed to.
    packet_in_service : Optional[PacketProto]
        Packet currently being transmitted, None when the port is idle.
    queue_packets : int
        Packets waiting in the buffer, excluding the one in service [–].
    queue_bytes : int
        Bytes waiting in the buffer, excluding the one in service [B].
    cum_packet_count : int
        Packets offered to the port, including those dropped [–].
    cum_byte_count : int
        Bytes offered to the port, including those dropped [B].
    cum_drop_count : int
        Packets dropped for lack of buffer space [–].
    """

    def __init__(
        self,
        env: simpy.Environment,
        port_no: int,
        capacity: Optional[int] = 10,
        transmission_rate: float = 1.0,
        destination: Optional[DestinationProto] = None,
    ) -> None:
        """
        Initialize a new switch port and start serving its buffer.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        port_no : int
            Port number within its switch.
        capacity : Optional[int], optional
            Buffer size [B], by default 10. Counts waiting packets only; the
            packet in service has already left the buffer. None means an
            unbounded buffer, in which case no packet is ever dropped.
        transmission_rate : float, optional
            Rate at which the port transmits [bit/s], by default 1.0.
        destination : Optional[DestinationProto], optional
            The port, fork, or sink transmitted packets are handed to, by
            default None. It may also be assigned after construction.
        """
        self.env = env
        self.port_no = port_no
        self.capacity = capacity
        self.transmission_rate = transmission_rate
        self.queue: simpy.Store = simpy.Store(env)
        self.destination = destination
        self.packet_in_service: Optional[PacketProto] = None
        self.queue_packets: int = 0
        self.queue_bytes: int = 0
        self.cum_packet_count: int = 0
        self.cum_byte_count: int = 0
        self.cum_drop_count: int = 0

        # start the packet processing process
        self.process = self.env.process(self.start())  # type: ignore

    @property
    def transmitting(self) -> bool:
        """bool: True while a packet occupies the server."""
        return self.packet_in_service is not None

    @property
    def packets_in_system(self) -> int:
        """int: Waiting packets plus the one in service [–], the M/M/1 $L$."""
        return self.queue_packets + (1 if self.packet_in_service else 0)

    @property
    def bytes_in_system(self) -> int:
        """int: Waiting bytes plus those of the packet in service [B]."""
        in_service = self.packet_in_service.size if self.packet_in_service else 0
        return self.queue_bytes + in_service

    def transmit(self, packet: PacketProto) -> simpy.Event:
        """
        Hold the packet for its transmission time, then hand it over.

        Parameters
        ----------
        packet : PacketProto
            The packet to transmit.

        Raises
        ------
        ValueError
            If no destination has been assigned.

        Returns
        -------
        simpy.Event
            Event signaling the completion of transmission.
        """
        # wait for transmission to complete
        yield self.env.timeout(BYTES_TO_BITS * packet.size / self.transmission_rate)
        # hand over packet to destination
        if self.destination is None:
            raise ValueError("No destination specified for switch port.")
        self.destination.process_packet(packet)

    def start(self) -> simpy.Process:
        """
        Serve the buffer indefinitely, one packet at a time.

        Returns
        -------
        simpy.Process
            The packet processing process.
        """
        while True:
            packet = yield self.queue.get()  # type: ignore
            # The packet leaves the buffer and occupies the server.
            self.queue_bytes -= packet.size
            self.queue_packets -= 1
            self.packet_in_service = packet
            yield self.env.process(self.transmit(packet))  # type: ignore
            self.packet_in_service = None

    def process_packet(self, packet: PacketProto) -> Optional[simpy.Event]:
        """
        Enqueue a packet, or drop it when the buffer cannot hold it.

        Parameters
        ----------
        packet : PacketProto
            The packet to be processed.

        Returns
        -------
        Optional[simpy.Event]
            Event signaling the addition of the packet to the queue, or None if
            the packet was dropped.
        """
        self.cum_packet_count += 1
        self.cum_byte_count += packet.size

        queue_bytes = self.queue_bytes + packet.size
        if self.capacity is not None and queue_bytes > self.capacity:
            self.cum_drop_count += 1
            return None

        self.queue_bytes = queue_bytes
        self.queue_packets += 1
        return self.queue.put(packet)

    def __repr__(self) -> str:
        """
        String representation of the switch port.

        Returns
        -------
        str
            String representation of the switch port.
        """
        return (
            f"SwitchPort(port_no={self.port_no}, capacity={self.capacity} B, "
            f"transmission_rate={self.transmission_rate} bit/s, "
            f"in system={self.packets_in_system}, dropped={self.cum_drop_count})"
        )


class Switch:
    """
    Network switch holding several independent ports.

    The switch itself performs no forwarding; it is a collection of identically
    configured :class:`SwitchPort` objects that are wired individually.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    id : str
        Identifier for this switch.
    ports : list[SwitchPort]
        The ports of the switch, in order.
    """

    def __init__(
        self,
        env: simpy.Environment,
        switch_id: str,
        num_ports: int,
        port_capacity: Optional[int],
        port_transmission_rate: float,
    ) -> None:
        """
        Initialize a switch and its ports.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        switch_id : str
            Identifier for this switch.
        num_ports : int
            Number of ports in the switch.
        port_capacity : Optional[int]
            Buffer size of each port [B]; None means unbounded.
        port_transmission_rate : float
            Transmission rate of each port [bit/s].
        """
        self.env = env
        self.id = switch_id
        self.ports: list[SwitchPort] = [
            SwitchPort(
                env,
                port_no=port_no,
                capacity=port_capacity,
                transmission_rate=port_transmission_rate,
            )
            for port_no in range(num_ports)
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
    """
    Samples the occupancy of one port at a regular interval.

    The tap records the queue and the system separately, because the two are
    compared with different formulas: `queue_packets` corresponds to $L_q$ and
    `system_packets` to $L$. Sampling at fixed instants estimates the
    time-average occupancy, which is the quantity Little's law relates to the
    mean delay measured by a :class:`PacketSink`.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    port : SwitchPort
        The port being sampled.
    interval : float
        Time between two samples [STU].
    times : list[float]
        Simulation time of each sample [STU].
    system_packets : list[int]
        Packets in the system at each sample, including the one in service [–].
    queue_packets : list[int]
        Packets waiting at each sample, excluding the one in service [–].
    queue_bytes : list[int]
        Bytes waiting at each sample, excluding the one in service [B].
    """

    def __init__(
        self, env: simpy.Environment, port: SwitchPort, interval: float = 1.0
    ) -> None:
        """
        Initialize a new network tap and start sampling.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        port : SwitchPort
            The switch port to be tapped.
        interval : float, optional
            Time between two samples [STU], by default 1.0.
        """
        self.env = env
        self.port = port
        self.interval = interval
        self.times: list[float] = []
        self.system_packets: list[int] = []
        self.queue_packets: list[int] = []
        self.queue_bytes: list[int] = []
        self.process = self.env.process(self.start())  # type: ignore

    def start(self) -> simpy.Process:
        """
        Sample the port indefinitely, once every `interval`.

        Returns
        -------
        simpy.Process
            The network tap process.
        """
        while True:
            yield self.env.timeout(self.interval)  # type: ignore
            self.times.append(self.env.now)
            self.system_packets.append(self.port.packets_in_system)
            self.queue_packets.append(self.port.queue_packets)
            self.queue_bytes.append(self.port.queue_bytes)

    def __repr__(self) -> str:
        """
        String representation of the network tap.

        Returns
        -------
        str
            String representation of the network tap.
        """
        return (
            f"NetworkTap(port={self.port.port_no}, samples={len(self.times)}, "
            f"last 10 in system={self.system_packets[-10:]}, "
            f"last 10 waiting={self.queue_packets[-10:]})"
        )


class PacketSink:
    """
    Endpoint that receives packets and records how long they took.

    The recorded delay runs from the creation of the packet at its source to
    its arrival here, so it includes every waiting time and every transmission
    time on the path. For a single port this is the M/M/1 time in system $W$,
    not the waiting time $W_q$.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    sink_id : str
        Identifier for this packet sink.
    logged_packets : list[PacketProto]
        Every packet received, in arrival order.
    delays : list[float]
        Time from creation to arrival for each packet [STU].
    arrivals : list[float]
        Arrival time of each packet [STU].
    interarrivals : list[float]
        Time since the previous arrival [STU]. These are the intervals of the
        departure process, not of the source.
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
        debug : bool, optional
            Log every received packet, by default False.
        """
        self.env = env
        self.sink_id = sink_id
        self.logged_packets: list[PacketProto] = []
        self.delays: list[float] = []
        self.arrivals: list[float] = []
        self.interarrivals: list[float] = []
        self.last_arrival_time: float = 0.0
        self.debug = debug

    def process_packet(self, packet: PacketProto) -> Optional[simpy.Event]:
        """
        Receive a packet and log its details.

        Parameters
        ----------
        packet : PacketProto
            The incoming packet.

        Returns
        -------
        Optional[simpy.Event]
            Always None; the sink absorbs the packet immediately.
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
    Sends each packet to one of several destinations at random.

    One random number is drawn per packet and compared with the cumulative
    probabilities, so destination `i` receives a share `probs[i]` of the
    traffic for any number of destinations. Splitting a Poisson stream this way
    yields independent Poisson streams with rates $p_i \\lambda$, which is what
    makes the offered traffic of each port in Step 5 computable by hand.

    Attributes
    ----------
    env : simpy.Environment
        The simulation environment.
    probs : list[float]
        Share of the traffic sent to each destination [–]; must sum to 1.
    cum_probs : list[float]
        Cumulative sums of `probs`, used to select a destination.
    destinations : list[Optional[DestinationProto]]
        Destination for each branch, assigned after construction.
    rng : numpy.random.Generator
        Random number generator used to select a destination.
    """

    def __init__(
        self,
        env: simpy.Environment,
        probs: list[float],
        rng: Optional[Generator] = None,
    ):
        """
        Initialize a new packet fork.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        probs : list[float]
            Share of the traffic sent to each destination [–]. Must sum to 1.
        rng : Optional[numpy.random.Generator], optional
            Generator used to select a destination, by default None, which
            creates an unseeded one. Pass the notebook's seeded generator to
            make a simulation containing a fork reproducible.

        Raises
        ------
        ValueError
            If `probs` is empty or does not sum to 1.
        """
        if not probs:
            raise ValueError("At least one probability is required.")
        if not isclose(sum(probs), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"Probabilities must sum to 1, got {sum(probs)}.")

        self.env = env
        self.probs = probs
        self.cum_probs = list(accumulate(probs))
        self.destinations: list[Optional[DestinationProto]] = [None for _ in probs]
        self.rng = default_rng() if rng is None else rng

    def process_packet(self, packet: PacketProto) -> Optional[simpy.Event]:
        """
        Select a branch at random and hand the packet to its destination.

        Parameters
        ----------
        packet : PacketProto
            The incoming packet.

        Raises
        ------
        ValueError
            If the selected branch has no destination assigned.

        Returns
        -------
        Optional[simpy.Event]
            Whatever the selected destination returns.
        """
        # One draw per packet, clamped so that rounding in the cumulative sums
        # can never select a branch past the last one.
        index = min(
            bisect_right(self.cum_probs, self.rng.random()),
            len(self.destinations) - 1,
        )
        destination = self.destinations[index]
        if destination is None:
            raise ValueError(f"No destination specified for fork branch {index}.")
        return destination.process_packet(packet)

    def __repr__(self) -> str:
        """
        String representation of the packet fork.

        Returns
        -------
        str
            String representation of the packet fork.
        """
        return f"PacketFork(probs={self.probs})"
