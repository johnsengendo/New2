import pandas as pd
import time
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import Link
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import os

print("Script started")

"""
Loading the CSV data
"""
csv_file = "predictions_window_300_ahead_60.csv"

"""
Ensuring the script and CSV file are in the same directory
"""
current_directory = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_directory, csv_file)

print(f"CSV file path: {csv_path}")

"""
Loading the CSV data
"""
print("About to read CSV file")
data = pd.read_csv(csv_path)
print(f"CSV file read. Number of rows: {len(data)}")

"""
Setting up the Mininet network
"""
print("Setting log level")
setLogLevel("info")

"""
Creating a network
"""
print("Creating Mininet network")
net = Mininet(switch=OVSSwitch)

"""
Adding two switches
"""
print("Adding switches")
s1 = net.addSwitch("s1")
print("s1 added")
s2 = net.addSwitch("s2")
print("s2 added")

"""
Adding two hosts
"""
print("Adding hosts")
h1 = net.addHost("h1", ip="10.0.0.1/24")
h2 = net.addHost("h2", ip="10.0.0.2/24")
print("Hosts added")

"""
Adding links between the hosts and the switches
"""
print("Adding links")
net.addLink(h1, s1)
net.addLink(s1, s2)
net.addLink(s2, h2)
print("Links added")

"""
Starting the network
"""
print("Starting network")
net.start()
print("Network started")

"""
Setting bandwidth limits using tc
"""
print("Setting bandwidth limits")
h1.cmd("tc qdisc add dev h1-eth0 root tbf rate 10Mbit burst 15k latency 1ms")
s1.cmd("tc qdisc add dev s1-eth1 root tbf rate 10Mbit burst 15k latency 1ms")
s1.cmd("tc qdisc add dev s1-eth2 root tbf rate 10Mbit burst 15k latency 1ms")
s2.cmd("tc qdisc add dev s2-eth1 root tbf rate 10Mbit burst 15k latency 1ms")
s2.cmd("tc qdisc add dev s2-eth2 root tbf rate 10Mbit burst 15k latency 1ms")
h2.cmd("tc qdisc add dev h2-eth0 root tbf rate 10Mbit burst 15k latency 1ms")
print("Bandwidth limits set")

"""
Defining the pcap file path in the same directory as the script
"""
pcap_file = os.path.join(current_directory, "h1_capture.pcap")

"""
Starting tcpdump on h1 to capture traffic on its interface and store it in the specified directory
"""
print("Starting tcpdump")
h1.cmd(f"tcpdump -i h1-eth0 -w {pcap_file} &")
print("tcpdump started")

"""
Starting the iperf server on h2
"""
print("Starting iperf server")
h2.cmd("iperf3 -s &")
print("iperf server started")

"""
Iterating over each row in the CSV file
"""
print("Starting iperf tests")
for index, row in data.iterrows():
    packets_per_second = row['Predicted']

    """
    Calculating bandwidth from packets/second and packet size
    """
    bandwidth_bps = packets_per_second * 1540.4859017313352 * 8
    bandwidth_mbps = bandwidth_bps / 1e6

    """
    Setting the protocol to TCP
    """
    protocol_option = ''

    """
    Running the iperf client on h1 with the specified bandwidth and protocol
    """
    iperf_command = f"iperf3 -c 10.0.0.2 {protocol_option} -b {bandwidth_mbps}M -t 1 -i 1 &"
    h1.cmd(iperf_command)

    """
    Waiting for 1 second before running the next iperf command
    """
    time.sleep(1)

    if index % 100 == 0:
        print(f"Completed {index} iperf tests")

print("All iperf tests completed")

"""
Stopping tcpdump after the test is completed
"""
print("Stopping tcpdump")
h1.cmd("pkill tcpdump")
print("tcpdump stopped")

"""
Optionally, dropping into the CLI for further testing or interaction
"""
print("Entering CLI")
CLI(net)

"""
Stopping the network
"""
print("Stopping network")
net.stop()
print("Network stopped")

print("Script completed")
