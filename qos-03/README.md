Students should work in pairs or triplets.

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
