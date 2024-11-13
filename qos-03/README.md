# Features of Network Traffic and their Effect on QoE

:warning: This is a multi-week activity, please save your progress as you go to prevent data loss.

:information_source: Students should work in pairs or triplets.

## Step 01 - Make a call

Introduction:

- General idea of multimedia services and its form of an audio call.
- Network features affecting the QoE.

Steps:

- Network traffic capture using Wireshark. Students discuss what they already know about the tool and then start the capture on local interface.
- Students make a phone call to Asterisk PBX using the credentials from [LMS](https://lms.vsb.cz). The can call each other using the extension numbers provided, or use an echo service at extension \*43.
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
sudo tcpdump -i ens160 src 10.100.0.X
```

To implement a simple packet generator, students utilize Scapy library in Python ecosystem.

Steps:

- brief intro to Scapy (methods, functions, packet crafting)
- simple packet generation - IP, UDP, Raw, send in for loop, send using iter parameter
- add random losses, random packet times - impossible to perform with Scapy on a level of milliseconds.
- again observe the resulting traffic and identify where the information is stored and in what form.

## Step 03 - Utilize the tc utility

The tc (traffic control) utility in Linux is a powerful tool used to configure the kernel packet scheduler. It allows you to manage network traffic by assigning a specific amount of bandwidth, introducing delay, or simulating packet loss and duplication. This is particularly useful for testing how network applications handle these conditions, ensuring that they can maintain acceptable performance even in suboptimal network environments. Understanding how to use tc effectively is a valuable skill for network administrators and engineers, enabling them to ensure reliable and consistent network performance.

The tc command syntax for adding delay, packet loss, and managing queuing disciplines is as follows:

```bash
tc qdisc add dev DEVICE root netem delay TIME loss RANDOM%
```

- **qdisc**: Refers to queuing discipline, the method tc uses to schedule packet sending.
- **add**: Used to add a new queuing discipline to the specified network device.
- **dev DEVICE**: Replace DEVICE with the name of the network interface you want to configure (e.g., eth0).
- **root netem**: Specifies that the network emulator (netem) queuing discipline should be added as the root qdisc.
- **delay TIME**: Adds a fixed amount of delay to all packets going out of the specified interface. Replace TIME with the desired delay amount (e.g., 100ms for 100 milliseconds of delay).
- **loss RANDOM%**: Simulates packet loss. Replace RANDOM% with the desired packet loss percentage (e.g., 1% for 1% packet loss).

Example:

```bash
tc qdisc add dev ens192 root netem delay 100ms loss 1%
```

This command configures the eth0 network interface to introduce 100 milliseconds of delay and 1% packet loss. Adjust the eth0, 100ms, and 1% placeholders to suit your specific requirements.

> **Note**: You might need superuser privileges to execute tc commands, so you may need to prepend sudo to the command.

Before running these commands on a production system, it's crucial to test and understand their impact in a controlled environment to avoid unintentional disruption of network services.

The tc utility allows you to simulate various packet loss models to emulate different network conditions. The basic packet loss model is specified with the loss parameter, as shown above. However, tc also supports more complex loss models, such as the Gilbert-Elliott model, which can be used to simulate bursty packet loss.

Example of Using Gilbert-Elliott Model:

```bash
sudo tc qdisc add dev ens192 root netem loss gemodel 1% 2%
```

In this example:

- **gemodel**: Specifies the use of the Gilbert-Elliott loss model.
- **1%**: Is the probability of a packet being lost in the good state.
- **2%**: Is the probability of a packet being lost in the bad state.

:information_source: Resetting to Default Settings

After conducting your network tests, it's essential to revert the network interface to its default settings to ensure normal operation. You can delete the existing queuing discipline to achieve this.

Example:

```bash
sudo tc qdisc del dev ens192 root
```

This command removes the root queuing discipline from the eth0 network interface, effectively resetting it to its default settings.

> **Note**: As with adding a queuing discipline, you might need superuser privileges to delete one, so you may need to prepend sudo to the command.

:information_source: Observing Current Configuration

To observe the current traffic control configuration of a network interface, use the tc qdisc show command.

Example:

```bash
sudo tc qdisc show dev ens192
```

This command displays the current queuing discipline configuration for the eth0 network interface. It will show the delay, loss, and other parameters if they have been configured.

> **Note**: Ensure to replace eth0 with your specific network interface name.

By regularly monitoring the traffic control settings, you can ensure that the network interface is configured as expected and make adjustments as necessary to optimize network performance and reliability.

Explore the tc man page and other resources to learn more about the various loss models and other advanced features that tc offers for network traffic control and shaping.

Steps:

- students get familiarized with tc command
- students introduce various tc scheduling policies on the laboratory interface. !! The second interface they configured.
- discussion about common traffic properties

## tcpreplay
```bash
sudo tcpreplay -i <interface> -t -K --loop <number_of_loops> -M <mac_address> -p <packet_rate> <pcap_file>
```
**interface:** Replace this with the name of the network interface you want to send the RTP packets through (e.g., eth0).

**-t** or **--topspeed:** This option tells tcpreplay to send packets as fast as possible.

**-K** or **--keep-mac:** This option ensures that the original MAC addresses in the pcap file are retained when sending the packets.

**--loop <number_of_loops>:** Specify the number of times you want to loop through the pcap file. Set <number_of_loops> to a desired value (e.g., 0 for continuous looping).

**-M <mac_address>:** Specify the MAC address of the destination device where you want to send the RTP packets. Replace <mac_address> with the actual MAC address.

**-p <packet_rate>:**  Set the desired packet transmission rate. You can specify the rate in packets per second (e.g., 1000).

**<pcap_file>:**  Replace this with the path to the pcap file containing the RTP packets you want to send.

Make sure to run this command with sudo privileges as sending packets over a network interface typically requires administrative permissions.

Here's an example command with placeholder values filled in:
```bash
sudo tcpreplay -i eth0 -t -K --loop 0 -M 00:11:22:33:44:55 -p 1000 /path/to/your/pcap-file.pcap
```

## Adding audio

Steps:

- Students prepare a clean pcap file containing unmodified speech from telephone calls. RTP audio only.
- Students use a **tcpreplay** utility to send RTP from pcap to the specified destination.
- On destination, students capture the audio using tcpdump.
  - 0.5% packet loss
  - 1.0% packet loss
  - 3.0% packet loss
  - discussion: how would delay affect the evaluation? Hint: Listening vs Conversational test.
- Students evaluate audio files using Wireshark functions in terms of observed packet loss and delay/jitter.

## Evaluate audio

Take distorted audio and evaluate it using subjective and objective metrics.

Steps:

- ACR (Absolute Category Rating)

ACR is a category judgment method where the test sequences are presented one at a time and are rated independently on a category scale. 
- DCR (Degradation Category Rating)

The second suitable method is DCR, where test sequences are presented in pairs. The first stimulus presented in each pair is always the source reference without any impairments. The second one is the same source but impaired by the test conditions. This method is also called the Double Stimulus Impairment Scale (DSIS) method. 
- [PESQ - Perceptual Evaluation of Speech Quality](https://drive.google.com/file/d/15UCvcW7bdYVAVa3g9aXji06x0WfAOdYE/view?usp=sharing) !! Needs GCC-9 to compile

```bash
sudo apt-get update
sudo apt-get install gcc-9
unzip file
cd file
gcc -o PESQ *.c -lm

scp .\file student@host:  or use WINscp on Windows
./PESQ
./PESQ +8000 orig.wav degr.wav
```


- [ViSQOL](https://github.com/google/visqol)



## Extract audio from pcap file

```bash
tshark -nr input.pcap -q -z rtp,streams
# show significant udp streams in case sip is not present
tshark -nr input.pcap -q -z conv,udp
# convert rtp with given ssrc
tshark -nr input.pcap -Y "rtp.ssrc == $SSRC" -T fields -e rtp.payload > payload_$SSRC.txt
# convert based on udp port number
tshark -nr input.pcap -d udp.port==<PORT_NUMBER>,rtp -Y rtp -T fields -e rtp.payload > payload.txt
# convert from text to binary
cat payload_$SSRC.txt | xxd -r -p > rtp_payload_$SSRC.raw
# convert from raw bytes to audio
ffmpeg -f alaw -ar 8000 -ac 1 -i rtp_payload_$SSRC.raw output_$SSRC.wav
```





