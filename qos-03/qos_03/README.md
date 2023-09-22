# Features of Network Traffic and their Effect on QoE

:warning: This is a multi-week activity, please save your progress as you go to prevent data loss.

:information_source: Students should work in pairs or triplets.

## Scapy library

Scapy is a powerful Python library that allows you to craft, manipulate, and work with network packets at a low level. It's often used for network analysis, penetration testing, and network protocol development. Here are some of the main methods and functionalities of Scapy, along with examples:

**Creating Packets:**

You can create various types of network packets using Scapy, such as Ethernet, IP, TCP, UDP, and more. Here's an example of creating an ICMP (ping) packet:

```python
from scapy.all import IP, ICMP
packet = IP(dst="192.168.1.1") / ICMP()
```

**Sending Packets:**

Scapy allows you to send packets over the network. Here's an example of sending an ICMP packet:

```python
response = sr1(packet)
response.show()
```

**Packet Manipulation:**

You can manipulate packet fields easily. For example, changing the source IP address of a packet:

```python
packet[IP].src = "10.0.0.1"
```

**Packet Inspection:**

Scapy provides methods to inspect packet contents. For example, printing packet details:

```python
packet.show()
```

**Packet Sniffing:**

from scapy.all import sniff

```python
packets = sniff(count=10)
packets.summary()
```

**Packet Filtering:**

You can filter packets during sniffing to capture specific traffic. For instance, capturing only TCP packets:

```python
packets = sniff(filter="tcp", count=10)
```

**Packet Reconstruction:**

Scapy allows you to reconstruct packets from binary data. For example, parsing a pcap file:

```python
packets = rdpcap("traffic.pcap")
```

**Layer Extraction:**

You can access specific packet layers to extract information. For example, extracting the TCP layer:

```python
tcp_layer = packet[TCP]
```

**Sending Custom Packets:**

Scapy enables you to send custom-crafted packets with specific payloads. For example, sending an HTTP request:

```python
from scapy.layers import http

http_request = IP(dst="example.com") / TCP() / http.HTTPRequest(method="GET")
send(http_request)
```

## QoE

QoE stands for "Quality of Experience." It is a measurement that assesses the overall quality and satisfaction of a user's experience with a product or service, typically in the context of digital technologies and services.

QoE is often used in fields like telecommunications, streaming media, online gaming, and user interfaces to evaluate how well a service or product meets the user's expectations. It goes beyond traditional quality of service (QoS) metrics, which primarily focus on technical parameters like bandwidth and latency. Instead, QoE considers the end user's perspective and satisfaction with the service, aiming to understand how the user perceives the quality.










  - Students identify and discuss signaling protocol SIP.
  - Students identify and discuss media transport protocol RTP.
  - Students discuss the form of audio data inside RTP.
- Students relate the captured trace with TCP/IP and ISO/OSI network stack.

## Step 02 - Make your own traffic generator

Introduction:

- Discussion about the process of transforming audio to packets.
- Goal is to make students understand and recognize the relation between network stack layers and allow them to create custom packets. This is a complex process, hence we try to make it easy with simple UDP packets.
- The reasons for use of Python ecosystem and Scapy library in this case - high-level abstraction, "ease-of-use".

Prepararion:

- To allow Scapy to send and receive packets, you either need to run is as root or set the necessary capabilities.

```bash
sudo setcap cap_net_raw=eip /usr/bin/pythonX.X
sudo setcap cap_net_raw=eip /usr/bin/tcpdump
```

To implement a simple packet generator, students utilize Scapy library in Python ecosystem.

Steps:

- brief intro to scapy (methods, functions, packet crafting)
- simple packet generation - IP, UDP, Raw, send in for loop, send using iter parameter
- add random losses, random packet times - impossible to perform with Scapy on a level of milliseconds.
- again observe the resulting traffic and identify where the information is stored and in what form.

## Step 03 - Utilize the tc utility

1. Make a call and trace it using wireshark.
2. Observe and describe the features of VoIP call focusing on RTP session. Relate it to TCP/IP and ISO/OSI network stack.
3. Make a custom packet generator using Scapy.
   - a brief intro to scapy
   - simple packet generation - just UDP, but with sequence number and constant length
   - observe the packets sent using wireshark
4. Add basic randomness to the packet stream using the distributions learnt in previous exercises and describe the effects on the receiving side.

5. Make adjustments to the network configuration of your virtual computer so that it is directly connected to the computer of the person you are cooperating with. Use computer's second interface to achieve that. Warning! All VPCs are connected to the same virtual switch!
6. Move the generated traffic to the newly created network and check that everything works as expected.
7. Study the documentation of "tc" - the traffic control utility of the linux machine (similar functions can be found on all advanced network devices)
   - focus on queues, and queueing disciplines
8. Implement randomness using the tc command.
   - random delay,
   - random packet losses.
9. With original design of the packet generator (no randomness in Python code) observe the traffic using Wireshark.

10. Modify the generator to include real audio data encapsulated in RTP protocol.
11. Transmit the audio across the impaired network and observe it in Wireshark/TCPDump and listen to it.

12. Make a one minute long conversation with your colleague using softphones on your workstation and capture it using Wireshark.
13. Extract the audio from the recording and name it with "original" suffix so you can use it later.
14. Read the pcap using Scapy and transfer it to your colleague's computer who will capture it using TCPDump in 3 iterations:
    - 0.5% packet loss
    - 1.0% packet loss
    - 3.0% packet loss
15. Extract the audio from the recordings and evaluate it using:
    - ACR
    - DCR
    - PESQ
