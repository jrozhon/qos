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

SIP uses URLs (Uniform Resource Locators) to identify users and services. These are similar to email addresses and help locate users on the Internet. SIP addresses are typically in the form of "sip:user@example.com" or "tel:+1234567890."

**4. Session Description:** 

 SIP can carry session descriptions, typically in the Session Description Protocol (SDP) format, which describes the media streams involved in the session. SDP helps devices negotiate things like codec selection, bandwidth, and media types.

**5. Proxy Servers:** 

SIP communication often involves intermediary devices called proxy servers. Proxy servers can forward, redirect, or authenticate requests and responses. They play a crucial role in routing SIP messages and ensuring that sessions are established correctly.

**6. Registrars** 

SIP registrars maintain a database of users and their locations. When a user comes online, their SIP client sends a registration request to a registrar, which records their current location (IP address). When someone wants to call that user, the registrar can help route the call to their current location.

**7. Stateless Protocol:** 

SIP is a stateless protocol, meaning each request and response is independent. This design allows for scalability and redundancy in networks. However, it also means that SIP devices need to maintain state information to handle session state effectively.

**8. Security:** 

SIP can be secured using various mechanisms like Transport Layer Security (TLS) for encryption and authentication, and Secure Real-time Transport Protocol (SRTP) for securing media streams.

**9. Interoperability:** 

SIP is designed to work in a heterogeneous environment, allowing different vendors' devices and software to communicate with each other effectively. This interoperability is a significant advantage in the world of communication.

**10. Extensibility:** 

SIP is highly extensible and has numerous extensions and options that can be added to adapt it for various use cases and technologies. This flexibility has allowed it to evolve over time to accommodate new requirements.

In summary, SIP is a crucial protocol for real-time multimedia communication over the Internet. It provides a standardized way for devices to initiate and manage sessions involving voice, video, messaging, and more. SIP's flexibility, interoperability, and extensibility have made it a cornerstone of modern communication systems, enabling a wide range of services and applications to function seamlessly.

 ### RTP (Real-Time Transport Protocol):

Real-Time Transport Protocol, is a network protocol primarily used for delivering audio and video over IP networks, especially for real-time multimedia applications like video conferencing, online gaming, and streaming media. It was first standardized in 1996 by the Internet Engineering Task Force (IETF) in RFC 1889.

- RTP's main purpose is to transport real-time media data, such as audio and video, over IP networks.

- It is specifically designed for applications where low latency and timely delivery of data are critical, making it suitable for real-time communication.

### RTP key features:

**1. Time-Stamping:** 

RTP assigns a timestamp to each data packet, allowing the receiver to reconstruct the timing information and synchronize audio and video streams accurately.

**2. Sequence Numbers** 

Each packet is assigned a sequence number to help detect packet loss and ensure that packets are received in the correct order.

**3. Payload Types:**

RTP supports various payload types, enabling it to carry different types of media, including audio, video, and other data.

**4. Header Extensions:** 

RTP allows for optional header extensions, which can be used to transmit additional information such as codec parameters, source identification, or transmission timestamps.

**5. SSRC (Synchronization Source):** 

Each stream in an RTP session is identified by a unique SSRC identifier. This helps receivers distinguish between different sources of media in a single RTP session.
 

 ### Audio Codec:
 
 RTP is codec-agnostic, meaning it can carry audio data encoded with various audio codecs. Common audio codecs used in RTP include:

**G.711 (PCM):**

**G.729 (ACELP):**