import socket
import sys
import struct
import random
import time
from queue import Queue
import heapq

# global variables

'''
topology = {
    (ip, port): [((ip, port), connected?, timeStamp), ((ip, port), connected?, timeStamp), ...],
    (ip, port): [((ip, port), connected?, timeStamp), ((ip, port), connected?, timeStamp), ...],
    ...
}
'''
topology = {}

'''
all the emulators in the topology
ipPortPairInTopology = [(ip, port), (ip, port), ...]
'''
ipPortPairInTopology = []

'''
The largest sequence number of the received LinkStateMessages from each node except itself. 
It will be a list of pairs (Node, Largest Seq No). 
largestSequenceNumber = {Node: Largest Seq No, Node: Largest Seq No, ...}
'''
largestSequenceNumber = {}

# Completed
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
            firstPair = (firstIp, firstPort) # ((firstIp, firstPort), True, 0)
            
            for i in range(len(ipPortPair)):
                ip, port = ipPortPair[i].split(",")
                pair = ((ip, port.strip()), True, 0)
                pair2 = (ip, port.strip()) # only the ip and address
                
                # first pair is the ip and port to a node which is running an emulator
                if i == 0:
                    ipPortPairInTopology.append(pair2)
                    topology[firstPair] = []
                    continue
                
                # the rest of the pairs are the ip and port to nodes which the emulator will be listening from
                topology[firstPair].append(pair)
    
    # build largestSequenceNumber
    for node in ipPortPairInTopology:
        largestSequenceNumber[node] = 0
    
    buildForwardTable()
    pass

# TODO: Not completed
def createRoutes():
    '''
    Refer to the course textbook pages 252-258 for details on the link-state protocol.
    Implement the link-state routing protocol to set up a shortest path forwarding table.
    Handle HelloMessages and LinkStateMessages for topology updates.
    Detect and react to node state changes.
    '''
    while True:
        '''
        HelloMessage: At defined intervals, each emulator should send the HelloMessage to its immediate neighbors. 
        The goal of this message is letting the node know the state of its immediate neighbors.  
        '''
        # send HelloMessage to immediate neighbors
        sendHelloMessages()
        
        # Receive packet from network in a non-blocking way. 
        # check for incoming packets
        try:
            packet, address = sock.recvfrom(5000)
            
            # should this be packet[:1] ?
            packetType = struct.unpack('c', packet[:8])[0]
            
            # Once you receive a packet, decide the type of the packet. 
            
            if packetType == 'H':
                timeStamp = parseHelloPacket(packet)
                handleHelloMessage(timeStamp, address)
                pass
            elif packetType == 'L':
                linkStateInfo = parseLinkStatePacket(packet)
                handleLinkStateMessage(linkStateInfo, packet, address)
                pass
        except BlockingIOError:
            pass
        
        checkNeighborTimeout()

# TODO: almost completed
def buildForwardTable(): 
    # initialize the confirmed set with the current emulator (Destination (ip, port): (Cost, NextHop))
    confirmed = {(emulator_hostname, port): (0, None)}
    
    while True:
        tentative = {}
        # For the node just added to the Confirmed list in the previous step, call it node Next and select its LSP
        for current_node, (cost, _) in confirmed.items():
            for neighbor_info in topology[current_node]:
                neighbor, connected, _  = neighbor_info
                if connected:
                    neighbor_cost = 1
                    total_cost = cost + neighbor_cost
                    if neighbor not in confirmed and (neighbor not in tentative or total_cost < tentative[neighbor][0]):
                        tentative[neighbor] = (total_cost, current_node)
        if not tentative:
            break
        next_node = min(tentative, key=lambda x: tentative[x][0])
        tentative_next_hop = tentative[next_node][1]

        # Check if the next hop is the destination, and update it accordingly
        if tentative_next_hop == (emulator_hostname, port):
            confirmed[next_node] = (1, next_node)
        elif(confirmed[tentative_next_hop]):
            og_cost =  tentative[next_node][0]
            while(confirmed[tentative_next_hop][0] != 1):
                tentative_next_hop = confirmed[tentative_next_hop][1]
            new_hop = (og_cost,confirmed[tentative_next_hop][1] )
            confirmed[next_node] = new_hop
        else:
            confirmed[next_node] = tentative[next_node]
            
    # Build the forwarding table from the perspective of each source node
    forwarding_table = {}
    for source_node, (cost, next_hop) in confirmed.items():
        forwarding_table[source_node] = (cost, next_hop)

    return forwarding_table

# TODO: Completed
def checkNeighborTimeout():
    '''
    Check if any of the neighbors have timed out.
    If a neighbor has timed out, update the route topology and forwarding table.
    Send LinkStateMessage to all neighbors.
    '''
    for neighbor in currentNeighbors:
        ip = neighbor[0][0]
        port = neighbor[0][1]
        timeStamp = neighbor[2]
        threshold = 1 # change to something else later
        
        if time.time() - timeStamp > threshold:
            # update route topology and forwarding table
            
            # pass in false here because the neighbor is no longer connected
            updateRouteTopology((ip, port), False)
            
            # re build the forwarding table
            buildForwardTable()
            
            # send LinkStateMessage
            sendLinkStateMessage()
    pass

# Completed
def createHelloPacket():
    timeStamp = time.time()
    packetType = 'H' # HelloMessage
    
    sendingPacketType = struct.pack('c', packetType.encode('utf-8'))
    sendingTimeStamp = struct.pack('!d', timeStamp)
    
    packet = sendingPacketType + sendingTimeStamp
    
    return packet

# Completed
def createLinkStatePacket():
    '''
    LinkStateMessage: At defined intervals, each emulator should send a LinkStateMessage to its immediate neighbors. 
    It contains the following information:
        The (ip, port) pair of the node that created the message.
        A list of directly connected neighbors of that node, with the cost of the link to each one.
        A sequence number. Incremental by one each time the information b is updated and a new LinkStateMessage is generated. 
        A time to live (TTL) for this packet. 
    '''
    packetType = 'L' # LinkStateMessage
    
    # pack (ip, port) pair of the node that created the message
    thisNodeIp = struct.pack('4sH', currentIpPortPair[0].encode('utf-8'))
    thisNodePort = struct.pack('4sH', currentIpPortPair[1].encode('utf-8'))
    
    # pack directly connected neighbors of that node
    sendingNeighbors = []
    for neighbor in topology[currentIpPortPair]:
        sendingIp = struct.pack('4sH', neighbor[0][0].encode('utf-8'))
        sendingPort = struct.pack('4sH', neighbor[0][1].encode('utf-8'))
        sendingConnected = struct.pack('?', neighbor[1])
        sendingTimeStamp = struct.pack('!d', neighbor[2])
        sendingNeighbors.append(sendingIp + sendingPort + sendingConnected + sendingTimeStamp)
        # sendingNeighbors.append(sendingIp + b'~' + sendingPort + b'~' + sendingConnected + b'~'+ sendingTimeStamp)
    
    # pack sequence number
    sequenceNumber = 0
    
    # pack time to live
    timeToLive = 0
    
    sendingPacketType = struct.pack('c', packetType.encode('utf-8'))
    sendingSequenceNumber = struct.pack('!I', sequenceNumber)
    sendingTimeToLive = struct.pack('!I', timeToLive)
    
    packet = sendingPacketType + thisNodeIp + thisNodePort + b' '.join(sendingNeighbors) + sendingSequenceNumber + sendingTimeToLive
    
    return packet

# Completed
def parseLinkStatePacket(packet):
    nodeIp, nodePort = struct.unpack('4sH', packet[1:9])[0]
    nodeIp = nodeIp.decode('utf-8')
    
    neighbors = []
    while offset < len(packet):
        neighborInfo = struct.unpack('4sH?d', packet[offset:offset+16])
        neighborIp, neighborPort, neighborConnected, neighborTimeStamp = neighborInfo
        neighborIp = neighborIp.decode('utf-8')
        neighbors.append(((neighborIp, neighborPort), neighborConnected, neighborTimeStamp))
        offset += 16
    
    sequenceNumber, timeToLive = struct.unpack('!II', packet[offset:offset+8])
    
    linkStateInfo = {
        "nodeIpPortPair": (nodeIp, nodePort),
        "neighbors": neighbors,
        "sequenceNumber": sequenceNumber,
        "timeToLive": timeToLive
    }
    
    return linkStateInfo

# Completed
def parseHelloPacket(packet):
    # should this be packet[1:?] ?
    timeStamp = struct.unpack('!d', packet[8:9])[0]
    
    return timeStamp

# Completed
def sendHelloMessages():
    '''
    Send HelloMessages to all neighbors
    '''
    for ipPortPair in ipPortPairInTopology:
        for neighbors in topology[ipPortPair]:
            # send HelloMessage
            neighborsIp, neighborsPort = neighbors
            packet = createHelloPacket()
            sock.sendto(packet, (neighborsIp, neighborsPort))
            
# TODO: Completed
def handleHelloMessage(timestamp, address):
    '''
    If it is a helloMessage, your code should
        Update the latest timestamp for receiving the helloMessage from the specific neighbor.
        Check the route topology stored in this emulator. If the sender of helloMessage is from a previously unavailable node, 
        change the route topology and forwarding table stored in this emulator. 
        Then generate and send a new LinkStateMessage to its neighbors.
    '''
    '''
    Similarly, when handling the helloMessage coming from an unavailable neighbor, you should declare it available, 
    update the route topology and forwarding table, and generate a new LinkStateMessage.
    '''
    currentNeighbors = topology[currentIpPortPair]
    
    # update the latest timestamp for the specific neighbor
    updateTimeStamp(timestamp, address)
    
    # check if the sender was previously unavilable
    for neighbor in currentNeighbors:
        ip = neighbor[0][0]
        port = neighbor[0][1]
        if ip == address[0] and port == address[1]:
            if neighbor[1] == False:
                # update route topology to true and forwarding table
                updateRouteTopology(address, True)
                
                # re build the forwarding table
                buildForwardTable()
                
                # send LinkStateMessage
                sendLinkStateMessage()

# Completed
def handleLinkStateMessage(linkStateInfo, packet, address):
    '''
    If it is a LinkSateMessage, your code should 
        Check the largest sequence number of the sender node to determine whether it is an old message. 
        If it’s an old message, ignore it. 
        If the topology changes, update the route topology and forwarding table stored in this emulator if needed.
        Call forwardpacket function to make a process of flooding the LinkStateMessage to its own neighbors.
    '''
    # gather all link state messages from all nodes
    
    # check the largest sequence number of the sender node to determine whether it is an old message
    # if it is an old message, ignore it
    nodeIpPortPair = linkStateInfo['nodeIpPortPair']
    if largestSequenceNumber[nodeIpPortPair] > linkStateInfo['sequenceNumber']:
        return
    
    # check if topology changes
    nodeNeighborsFromLSM = linkStateInfo['neighbors']
    nodeNeighbors = topology[nodeIpPortPair]
    for i in range(len(nodeNeighborsFromLSM)): 
        neighborConnectedFromLSM = nodeNeighborsFromLSM[i][1]
        
        neighborConnected = nodeNeighbors[i][1]
        
        if neighborConnectedFromLSM != neighborConnected:
            # update the route topology and forwarding table stored in this emulator if needed
            nodeNeighbors[i][1] = neighborConnectedFromLSM
            
            # re build the forwarding table
            buildForwardTable()

            forwardPacket(packet, 'L', address, nodeIpPortPair)
    pass

# TODO: Not completed - only handled packets regarding LinkStateMessage
def forwardPacket(packet, packetType, address, nodeIpPortPair):
    '''
    forwardpacket will determine whether to forward a packet and where to forward a packet received by an emulator in 
    the network. Your emulator should be able to handle both packets regarding the LinkStateMessage, 
    and packets that are forwarded to it from the routetrace application (described below). 
    For LinkStateMessage, you need to forward the LinkStateMessage to all its neighbors except where it comes from. 
    However, when TTL (time to live) decreases to 0, you don’t need to forward this packet anymore.
    '''
    if packetType == 'L':
        # forward the LinkStateMessage to all its neighbors except where it comes from
        for neighbor in currentNeighbors:
            if neighbor[1] == False:
                continue
            
            ip = neighbor[0][0]
            port = neighbor[0][1]
            
            # neighbor that sent the packet
            if ip == address[0] and port == address[1]: 
                continue
            
            # source node of the packet
            if ip == nodeIpPortPair[0] and port == nodeIpPortPair[1]:
                continue
            
            sock.sendto(packet, (ip, port))

# Completed
def sendLinkStateMessage():
    packet = createLinkStatePacket()
    for neighbor in currentNeighbors:
        if neighbor[1] == False:
            continue
        ip = neighbor[0][0]
        port = neighbor[0][1]
        sock.sendto(packet, (ip, port)) 

# Completed
def updateTimeStamp(timestamp, address):
    for neighbor in currentNeighbors:
        ip = neighbor[0][0]
        port = neighbor[0][1]
        if ip == address[0] and port == address[1]:
            neighbor[2] = timestamp

# Completed
def updateRouteTopology(address, status):
    print("update route topology")
    for neighbors in currentNeighbors:
        ip = neighbors[0][0]
        port = neighbors[0][1]
        if ip == address[0] and port == address[1]:
             # make sure that when we update currentNeighbors, topology is also updated 
            neighbors[1] = status

# PROJECT 2 BELOW
    
# this list will have a list that contains [packet, delay_time_started]
delayed_packets = []

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

# MAIN FUNCTION STARTS HERE

'''
Example topology:
If 2 goes down:
dest 3 through 3 with cost 1
dest 4 through 3 with cost 2
dest 5 through 3 with cost 3
'''

# parse command line
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
    
ip = socket.gethostbyname(socket.gethostname())
currentIpPortPair = (ip, port)
currentNeighbors = topology[currentIpPortPair]
            
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
