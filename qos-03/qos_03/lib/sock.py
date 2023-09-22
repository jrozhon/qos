from scapy.all import *
import socket

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    p = IP(dst="192.168.1.254")/TCP(flags="S", sport=RandShort(),dport=80)/Raw("Hallo world!")
    s.connect(("192.168.1.254",80))
    s.send(bytes(p))
    print "[+] Request Sent!"
except Exception, e:
    raise e
