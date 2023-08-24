from typing import List, Optional

import simpy


class Packet:
    def __init__(
        self, env: simpy.Environment, size: int, source: str, destination: str
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
        self.size = size
        self.creation_time: float = env.now
        self.source = source
        self.destination = destination


class SwitchPort:
    def __init__(
        self,
        env: simpy.Environment,
        capacity: int,
        transmission_rate: float,
        tap: Optional["NetworkTap"] = None,
    ) -> None:
        """
        Switch port to queue and transmit packets.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        capacity : int
            Maximum number of packets that can be queued.
        transmission_rate : float
            Rate at which packets are transmitted.
        tap : NetworkTap, optional
            Optional tap for monitoring traffic, by default None.
        """
        self.env = env
        self.capacity = capacity
        self.transmission_rate = transmission_rate
        self.queue: simpy.Store = simpy.Store(env)
        self.tap = tap

    def transmit(self, packet: Packet) -> simpy.Event:
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


class Switch:
    def __init__(
        self,
        env: simpy.Environment,
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
        num_ports : int
            Number of ports in the switch.
        port_capacity : int
            Capacity of each port.
        port_transmission_rate : float
            Transmission rate of each port.
        """
        self.env = env
        self.ports: List[SwitchPort] = [
            SwitchPort(env, port_capacity, port_transmission_rate)
            for _ in range(num_ports)
        ]

    def route_packet(self, packet: Packet) -> None:
        """
        Route the packet to an available port.

        Parameters
        ----------
        packet : Packet
            The packet to route.
        """
        for port in self.ports:
            if len(port.queue.items) < port.capacity:
                port.queue.put(packet)
                self.env.process(port.transmit(packet))
                break


class PacketSource:
    def __init__(
        self,
        env: simpy.Environment,
        switch: Switch,
        source_id: str,
        destination: str,
        interval: float,
        packet_size: int,
    ) -> None:
        """
        Source of packets generating at regular intervals.

        Parameters
        ----------
        env : simpy.Environment
            The simulation environment.
        switch : Switch
            The switch to route packets to.
        source_id : str
            Identifier for this source.
        destination : str
            Destination identifier for packets from this source.
        interval : float
            Time interval between packet generation.
        packet_size : int
            Size of the generated packets.
        """
        self.env = env
        self.switch = switch
        self.source_id = source_id
        self.destination = destination
        self.interval = interval
        self.packet_size = packet_size

    def start(self) -> simpy.Event:
        """
        Start generating packets.

        Yields
        ------
        simpy.Event
            Event signaling the next packet generation.
        """
        while True:
            yield self.env.timeout(self.interval)
            packet = Packet(
                self.env, self.packet_size, self.source_id, self.destination
            )
            self.switch.route_packet(packet)


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
        self.total_size: int = 0
        self.packet_times: List[float] = []

    def tap_packet(self, packet: Packet) -> None:
        """
        Record details of a packet as it's observed by the tap.

        Parameters
        ----------
        packet : Packet
            The observed packet.
        """
        self.packet_count += 1
        self.total_size += packet.size
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
