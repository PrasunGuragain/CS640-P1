import socket
import sys
import struct
import random
import time
from queue import Queue

# global variables
topology = {}
ipPortPairInTopology = []

def readTopology(filename):
    '''
    Write a function to read the topology file and initialize the emulator with the network structure.
    Ensure that the emulator knows its neighbors.
    '''
    # fill in the topology
    with open(filename, 'r') as file:
        for line in file:
            ipPortPair = line.split(" ")
            
            firstIp, firstPort = ipPortPair[0].split(",")
            firstPair = (firstIp, firstPort)
            
            for i in range(len(ipPortPair)):
                ip, port = ipPortPair[i].split(",")
                pair = (ip, port.strip())
                
                # first pair is the ip and port to a node which is running an emulator
                if i == 0:
                    ipPortPairInTopology.append(pair)
                    topology[firstPair] = []
                    continue
                
                # the rest of the pairs are the ip and port to nodes which the emulator will be listening from
                topology[firstPair].append(pair)
    pass

def createRoutes():
    '''
    Refer to the course textbook pages 252-258 for details on the link-state protocol.
    Implement the link-state routing protocol to set up a shortest path forwarding table.
    Handle HelloMessages and LinkStateMessages for topology updates.
    Detect and react to node state changes.
    '''
    while True:
        # send HelloMessages to all neighbors every second
        for ipPortPair in ipPortPairInTopology:
            for neighbors in topology[ipPortPair]:
                # send HelloMessage
                neighborsIp, neighborsPort = neighbors
                packet = createPacket(neighborsIp, neighborsPort, "HelloMessage")
                sock.sendto(packet, (neighborsIp, neighborsPort))  
        
        # send LinkStateMessages to all neighbors
        for ipPortPair in ipPortPairInTopology:
            for neighbors in topology[ipPortPair]:
                # send LinkStateMessage
                neighborsIp, neighborsPort = neighbors
                packet = createPacket("LinkStateMessage")
                sock.sendto(packet, (neighborsIp, neighborsPort))
            
        # receive HelloMessage
        try:
            packet, address = sock.recvfrom(5000)
            timeStamp = parsePacket(packet)
        except BlockingIOError:
            pass
                
        for ipPortPair in ipPortPairInTopology:
            for neighbors in topology[ipPortPair]:
                pass
                
        

def createPacket(messageType):
    if messageType == "HelloMessage":
        timeStamp = time.time()
    elif messageType == "LinkStateMessage":
        pass
    elif messageType == "RequestPacket":
        pass
    elif messageType == "DatePacket":
        pass
    elif messageType == "EndPacket":
        pass

    sendingTimeStamp = struct.pack('!d', timeStamp)
    packetType = struct.pack('c', 'M'.encode('utf-8'))
    
    packet = sendingTimeStamp + packetType
    
    return packet

def parsePacket(packet):
    timeStamp = struct.unpack('!d', packet[:8])[0]
    # packetType = struct.unpack('c', packet[8:9])[0]
    
    return timeStamp # , packetType
    
# this list will have a list that contains [packet, delay_time_started]
delayed_packets = []

def parse_request_packet():
    pass

def parse_packet(packet):
    priority = struct.unpack('B', packet[:1])[0]
    src_ip_address = socket.inet_ntoa(struct.unpack('4s', packet[1:5])[0])
    src_port = struct.unpack('H', packet[5:7])[0]
    dest_ip_address = socket.inet_ntoa(struct.unpack('4s', packet[7:11])[0])
    dest_port = struct.unpack('H', packet[11:13])[0]
    length = struct.unpack('I', packet[13:17])[0]

    # payload
    packet_type = struct.unpack('c', packet[17:18])[0]
    sequence_number = struct.unpack('!I', packet[18:22])[0]
    payload_length = struct.unpack('!I', packet[22:26])[0]
    # sys.exit(1)
    payload = packet[26:]
    payload_length = len(payload)

    return priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload

def log_event(log, message):
    with open(log, 'a') as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        
def send_helper():
     # 4. If a packet is currently being delayed and the delay has not expired, goto Step 1.
     
    # if a packet is currently being delayed
    if delayed_packets != []:
        for delayed in delayed_packets:
            # get the packet infos
            current_packet, delay_start_time = delayed
            priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload = parse_packet(current_packet)
            
            next_hop_key = forwarding_table[(dest_ip_address, str(dest_port))][0]
            delay = forwarding_table[(dest_ip_address, str(dest_port))][1]
            loss_probability = forwarding_table[(dest_ip_address, str(dest_port))][2]
                
            # if delay has expired
            if time.time() - delayed[1] > delay / 1000:
                # send packet to next hop, drop if loss
                
                # 7. Otherwise, send the packet to the proper next hop.
                endPacket = False
                if packet_type == 'E':
                    endPacket = True
                
                if endPacket or random.random() * 100 > loss_probability:
                    destination_address, destination_port = next_hop_key[0], int(next_hop_key[1])

                    sock.sendto(current_packet, (destination_address, destination_port))  
                    
                    delayed_packets.remove(delayed)
                    
                    return
                else:
                    # 6. When the delay expires, randomly determine whether to drop the packet
                    message = "loss event occurred"
                    #log_event(log, message)
                    
                    # remove packet from priority queue
                    priority_list[priority].get()
                    
                    return
    else:
        # 5. If no packet is currently being delayed
        
        # select the packet at the front of the queue with highest priority
        for priority in priority_list.keys():
            if not priority_list[priority].empty():
                highest_priority_packet = priority_list[priority].queue[0]
                
                # remove that packet from the queue
                priority_list[priority].get()
                
                # delay it
                delayed_packets.append( [highest_priority_packet, time.time()])
                # delayed_packets.append(highest_priority_packet)
                
                break   

def routing(priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload, sock, filename,packet):
    dest_found = False
    
    # 2 Once you receive a packet, decide whether packet is to be forwarded by consulting the forwarding table
    if (dest_ip_address,str(dest_port)) in forwarding_table:
        
        # if packet is valid ie destination is found in fowarding table, then add it to priority queue
        get_current_time = time.time()
        packet_value = (packet, get_current_time)
        
        # This queue size is specified on the command line of the emulator startup. 
        # If a queue is full, the packet is dropped and this event is logged
        if priority_list[priority].full():
            message = "queue full"
            #log_event(log, message)
        else:
            priority_list[priority].put(packet)
        
        # send(next_hop, delay, loss_probability, sock, log)
        dest_found = True

    if not dest_found:
        message = "no forwarding entry found"
        #log_event(log, message)

readTopology("topology.txt")
for key, value in topology.items():
    print(f"{key} -> {value}")
sys.exit(1)
      
# PARSE COMMAND LINE ARGUMENTS
    
# Port
if '-p' in sys.argv:
    p = sys.argv.index('-p')
    port = int(sys.argv[p + 1])
    if port < 2049 and port > 65536:
        print("Sender port should be in this range: 2049 < port < 65536")
        sys.exit(1)
else:
    print("Port argument (-p) is missing.")
    sys.exit(1)

# Filename
if '-f' in sys.argv:
    f = sys.argv.index('-f')
    filename = sys.argv[f + 1]
else:
    print("Filename argument (-f) is missing.")
    sys.exit(1)
            
# Create a socket for the requester
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', port))

# set socket to non-blocking
sock.setblocking(False)

emulator_hostname = socket.gethostbyname(socket.gethostname())

# create a forwarding table: {(destination, d_port): [(next_hop, next_port), delay, loss_probability]}
forwarding_table = {}
with open(filename, 'r') as file:
    for line in file:
        columns = line.strip().split()
        emulator, e_port = columns[0:2]
        destination, d_port = columns[2:4]
        next_hop, next_port = columns[4:6]
        delay = columns[6]
        loss_probability = columns[7]
        
        if (emulator_hostname == emulator) and (str(port) == e_port):
            forwarding_table[(destination, d_port)] = [(next_hop, next_port), float(delay), float(loss_probability)]

# priority_list = {1: Queue(maxsize = queue_size), 2: Queue(maxsize = queue_size), 3: Queue(maxsize = queue_size)}
priority_list = {1: Queue(maxsize = 1), 2: Queue(maxsize = 1), 3: Queue(maxsize = 1)}

while True:
    
    # Receive a packet
    try:
        # Receive packet from network in a non-blocking way. This means that you should not wait/get blocked in the recvfrom function until you get a packet. Check if you have received a packet; If not jump to 4,
        try:
            packet, addr = sock.recvfrom(5000)
            
            #print("packet: " {packet})

            # Parse the packet
            priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload = parse_packet(packet)

            #if packet_type == 'E':
            #next_hop_key = forwarding_table[(dest_ip_address, str(dest_port))][0]
            #destination_address, destination_port = next_hop_key[0], int(next_hop_key[1])
            #sock.sendto(packet, (destination_address, destination_port))  
                  
            #else:
            # setting up priority queues, decide where it is to be forwarded
            routing(priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload, sock, filename,packet)
            send_helper()
        except BlockingIOError:
            # Have not received a packet, 2.3 Forwarding Summary step 4
            # Check if there are delayed packets
            send_helper()
            
    except KeyboardInterrupt:
            socket.close()
            sys.exit(0)
