# Features of Network Traffic and their Effect on QoE

:warning: This is a multi-week activity, please save your progress as you go to prevent data loss.

:information_source: Students should work in pairs or triplets.

## Step 01 - Make a call

Introduction:

- General idea of multimedia services and its form of an audio call.
- Network features affecting the QoE.

Steps:

- Network traffic capture using Wireshark. Students discuss what they already know about the tool and then start the capture on local interface.
- Linphone Application can perform a direct IP call (no account needed). Students make a phone call between two stations.
- Students observe the features and form of information exchanged in VoIP call.
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
