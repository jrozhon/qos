
# Quality of Service (QoS) in Networking

## Introduction to QoS:

Quality of Service (QoS) is a set of technologies and mechanisms designed to manage and improve the delivery of data over networks. It ensures that critical applications receive preferential treatment, leading to a more predictable and reliable network performance. QoS is particularly crucial in environments where various types of traffic, such as voice, video, and data, coexist.

## Key Parameters in QoS:

**Bandwidth:** The amount of data that can be transmitted over a network in a given time. Adequate bandwidth allocation is vital for ensuring the smooth delivery of information.

**Delay:** The delay between the initiation of a data transfer and its completion. Low latency is essential for real-time applications like voice and video.

**Jitter:** Variation in latency, which can cause disruptions in the flow of real-time data. Minimizing jitter is critical for applications that require consistent and predictable delivery.

**Packet Loss:** The percentage of data packets that fail to reach their destination. QoS aims to minimize packet loss, especially for applications sensitive to data integrity.

## Types of delays:

1. Propagation Delay:

The time it takes for a signal to travel from the source to the destination.

$d_{propagation} = \frac{d}{s}$, 

Where d is the distance, and s is the signal propagation speed in the medium.

2. Transmission Delay:

3. Queuing Delay:

4. Processing Delay:

5. Total End-to-End Delay:

Understanding and minimizing these delays are essential for designing efficient and responsive communication networks. Real-time applications, such as voice and video, are particularly sensitive to these delays, and their performance relies on the careful management of each delay component.

## Traffic Marking:

QoS often involves the use of traffic marking, where packets are labeled with Differentiated Services Code Points (DSCP) or other markings to indicate their priority. This marking allows network devices to prioritize certain types of traffic over others.

## Traffic Shaping:

Traffic shaping is a QoS technique used to control the rate of data transmission in a network. It smoothens the traffic flow by regulating the data rate, reducing the likelihood of congestion and packet loss. This is particularly valuable in scenarios where bursty traffic patterns might impact the overall network performance.


## QoS in Differentiated Services (DiffServ) Model:

Differentiated Services (DiffServ) is a scalable and flexible model for implementing Quality of Service (QoS) in computer networks. Unlike traditional approaches that attempt to treat each data packet individually (Integrated Services or IntServ), DiffServ classifies and manages traffic based on a small set of Differentiated Services Code Points (DSCP). This allows for more efficient and scalable handling of diverse traffic types in a network.

**DSCP (Differentiated Services Code Point):**

DiffServ utilizes the IPv4 header's TOS (Type of Service) field to assign a DSCP value to each packet.
DSCP is a 6-bit value that allows for 64 different code points, which are used to categorize packets into different behavior aggregates.
Per-Hop Behavior (PHB):

PHB defines the forwarding treatment that a set of packets with the same DSCP value should receive at each network node.
Commonly used PHBs include Default Forwarding (best-effort), Expedited Forwarding (EF) for low-latency, assured delivery, and Assured Forwarding (AF) for delivery with different levels of assurance.

**Traffic Classification:**

Network devices classify incoming packets into different behavior aggregates based on their DSCP values.
This classification allows routers and switches to make forwarding decisions according to the specified QoS policies.


**Packet Marking:**

DiffServ-enabled devices mark packets with appropriate DSCP values based on the type of service required.
This marking occurs at the network edge, where administrators can apply QoS policies to incoming traffic.
Edge Router Processing:

At the network edge, routers inspect the DSCP values and classify packets into appropriate behavior aggregates.
Edge routers may re-mark or reclassify packets to align with the network's QoS policies.

**Scalability:**

DiffServ's use of a small set of DSCP values allows for easier scalability in large networks compared to approaches that require per-flow state.
Simplicity:

The model is simpler to implement and manage than older QoS models like IntServ, making it more suitable for modern, dynamic networks.

**Flexibility:**

Administrators have the flexibility to define and implement QoS policies based on the specific needs of their network, applications, and services.
In conclusion, the Differentiated Services (DiffServ) model offers a pragmatic and scalable approach to implementing Quality of Service in computer networks. Its simplicity, scalability, and flexibility make it well-suited for modern network environments with diverse traffic types and varying QoS requirements.

## Queuing 

### Priority Queuing (PQ):

**Description:** Priority Queuing is a queuing discipline where packets are assigned priority values, and higher-priority packets are dequeued and transmitted before lower-priority packets.

**Operation:** Packets are categorized into priority queues, and the router or switch serves packets from the highest-priority queue first. This ensures that high-priority traffic is given preference over lower-priority traffic.

**Considerations:** While it provides fast service to high-priority traffic, it can lead to the starvation of lower-priority queues if there is a continuous arrival of high-priority packets.

### Custom Queuing (CQ):

**Description:** Custom Queuing is a queuing algorithm that allows the network administrator to define the exact percentage of bandwidth that each queue will receive.

**Operation:** The administrator can specify the percentage of bandwidth allocated to each queue, helping to control the flow of traffic based on predefined rules.

**Considerations:** CQ provides flexibility in bandwidth allocation but may not be as efficient as more advanced queuing disciplines in certain scenarios.

### Weighted Fair Queuing (WFQ):

**Description:** Weighted Fair Queuing is a queuing discipline that aims to provide fair bandwidth distribution among different flows by assigning weights to each flow.

**Operation:** Flows are assigned weights, and the scheduler allocates bandwidth proportionally based on these weights. This helps prevent one flow from dominating the bandwidth at the expense of others.

**Considerations:** WFQ is more equitable in distributing bandwidth compared to simple queuing algorithms.

### Class-Based Weighted Fair Queueing (CBWFQ):

**Description:** CBWFQ is an extension of WFQ that allows for the creation of traffic classes with assigned bandwidth guarantees and restrictions.

**Operation:** Instead of flows, CBWFQ classifies traffic into different classes, and each class is assigned a minimum and maximum bandwidth. This allows for more granular control over different types of traffic.

**Considerations:** CBWFQ is particularly useful in environments where different applications or services require specific levels of bandwidth.

### Low Latency Queuing (LLQ):

**Description:** Low Latency Queuing is a modification of CBWFQ that introduces a priority queue to ensure low latency for delay-sensitive traffic.

**Operation:** LLQ includes a priority queue for delay-sensitive traffic, while still maintaining the benefits of CBWFQ for other types of traffic. This ensures that latency-sensitive packets are serviced without delay.

**Considerations:** LLQ is often used in scenarios where minimizing packet delay for certain types of traffic, such as voice or video, is critical.