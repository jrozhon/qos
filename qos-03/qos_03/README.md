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

**Packet Analysis:**

Scapy offers tools for analyzing captured packets, such as extracting statistics, calculating checksums, or dissecting protocols.

**Custom Protocols:**

You can create custom network protocols and define how they should be encoded/decoded in Scapy. This is useful for testing or simulating custom network applications.

These are just some of the main methods and functionalities of Scapy. It's a versatile library that can be used for a wide range of networking tasks, from simple packet crafting to complex network analysis and penetration testing. Be sure to refer to the Scapy documentation and tutorials for more in-depth information and examples.

## QoE

QoE stands for "Quality of Experience." It is a measurement that assesses the overall quality and satisfaction of a user's experience with a product or service, typically in the context of digital technologies and services.

QoE is often used in fields like telecommunications, streaming media, online gaming, and user interfaces to evaluate how well a service or product meets the user's expectations. It goes beyond traditional quality of service (QoS) metrics, which primarily focus on technical parameters like bandwidth and latency. Instead, QoE considers the end user's perspective and satisfaction with the service, aiming to understand how the user perceives the quality.

## SIP

Session Initiation Protocol (SIP) is a signaling protocol used for initiating, maintaining, modifying, and terminating real-time sessions that involve video, voice, messaging, and other communications applications and services over the Internet. It plays a fundamental role in the field of Voice over IP (VoIP), video conferencing, instant messaging, and other multimedia communication services. SIP is specified in RFC 3261.

### SIP key components:

**1. Session Establishment:** 

SIP is primarily used for setting up, modifying, and tearing down communication sessions. These sessions can include voice and video calls, multimedia conferences, instant messaging, and more. SIP allows devices to establish connections and negotiate the parameters necessary for the session.

**2. User Agents:** 

SIP relies on two main types of user agents: User Agents Client (UAC) and User Agent Server (UAS). UAC initiates requests, while UAS responds to them. For example, when you make a VoIP call, your device acts as a UAC to initiate the call, while the recipient's device acts as a UAS to accept or reject the call.

**3. URLs and Addresses:** 
**4. Session Description:** 
**5. Proxy Servers:** 
**6. Registrars** 
**7. Stateless Protocol:** 
**8. Security:** 
**9. Interoperability** 