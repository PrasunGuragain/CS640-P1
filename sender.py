import struct
import sys
import socket
import time
from datetime import datetime

# TODO: Check create_packet function
def create_packet(priority, s_port, d_address, d_port, packet1_length, packet_part, seqNo):
    priority_type = struct.pack('B', priority)
    src_ip_address = struct.pack('', socket.gethostname())
    src_port = struct.pack('H', s_port)
    dest_ip_address = struct.pack('', d_address)
    dest_port = struct.pack('H', d_port)
    length1 = struct.pack('I', packet1_length)
    
    header1 = priority_type + src_ip_address + src_port + dest_ip_address + dest_port + length1
    
    packetType = 'D'.encode()
    packetLength = len(packet_part)
    header2 = struct.pack('!cII', packetType, seqNo, packetLength)
    
    payload = header2 + packet_part
    
    packet = header1 + payload
    
    return packet
    

def main():
    # data packet
    '''
    Packet Type:   'D'
    Sequence Number: seqNo
    Length: packetLength
    Payload: 'fileData'
    '''
    
    # request packet
    '''
    Packet Type:   'R'
    Sequence Number: 0
    Length: 0
    Payload: 'file1.txt'
    '''
    
    # end packet
    '''
    Packet Type:   'E'
    Sequence Number: 
    Length: 
    Payload: ''
    '''
    
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
        
    # Requester port
    if '-g' in sys.argv:
        g = sys.argv.index('-g')
        requesterPort = int(sys.argv[g + 1])
    else:
        print("Requester port argument (-g) is missing.")
        sys.exit(1)

    # Rate
    if '-r' in sys.argv:
        r = sys.argv.index('-r')
        rate = int(sys.argv[r + 1])
    else:
        print("Rate argument (-r) is missing.")
        sys.exit(1)

    # Sequence number
    if '-q' in sys.argv:
        q = sys.argv.index('-q')
        seqNo = int(sys.argv[q + 1])
    else:
        print("Seq_no argument (-q) is missing.")
        sys.exit(1)

    # Length
    if '-l' in sys.argv:
        l = sys.argv.index('-l')
        length = int(sys.argv[l + 1])
    else:
        print("Length argument (-l) is missing.")
        sys.exit(1) 
        
    # f_hostname
    if '-f' in sys.argv:
        f = sys.argv.index('-f')
        f_hostname = sys.argv[f + 1]
    else:
        print("f_hostname argument (-f) is missing.")
        sys.exit(1)
        
    # f_port
    if '-e' in sys.argv:
        e = sys.argv.index('-e')
        f_port = int(sys.argv[e + 1])
    else:
        print("f_port argument (-e) is missing.")
        sys.exit(1)
    
    # priority
    if '-i' in sys.argv:
        i = sys.argv.index('-i')
        priority = sys.argv[i + 1]
    else:
        print("priority argument (-i) is missing.")
        sys.exit(1)
    
    # timeout
    if '-t' in sys.argv:
        t = sys.argv.index('-t')
        timeout = sys.argv[t + 1]
    else:
        print("timeout argument (-t) is missing.")
        sys.exit(1)
    
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))

    
    # GET REQUEST PACKET FROM REQUESTER
    
    # packet:
        # packet type (8 bit) | sequence number (32 bit) | length (32 bit) | payload (variable length)
    
    requestPacket, requestAddress = sock.recvfrom(5000)
    requestPacketType, requestSequenceNumber, window = struct.unpack('!cII', requestPacket[:9])
    
    print("requestPacket: ", requestPacket, " window: ", window, " requestPacketType:", requestPacketType, " requestSequenceNumber: ", requestSequenceNumber)
    sock.close()
    sys.exit(1)
    
    fileName = requestPacket[5:].decode()
        
     # SPLIT FILE INTO CHUNCKS FOR PACKETS
    try:
        filePart = []
        with open(fileName, "rb") as file:
            while True:
                # read in chucks by length
                chunk = file.read(length)
                
                # End of file
                if not chunk:
                    break
                
                filePart.append(chunk)
    except FileNotFoundError:
        print("File not found.")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', port))
        
        packet_type = 'E'.encode()
        packet_length = 0
        sequence_number = 0
        header = struct.pack('!cII', packet_type, sequence_number, packet_length)
        payload = b''
        
        end_packet = header + payload
        
        # Send the END packet to the requester
        sock.sendto(end_packet, (requestAddress, requesterPort))
        
        # Print information about the END packet
        curTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        print(f"END Packet (File Not Found)")
        print(f"send time: {curTime}")
        print(f"requester addr: {socket.gethostname()}:{requesterPort}")
        print(f"Sequence num: {sequence_number}")
        print(f"length: {packet_length}")
        print(f"payload: ''\n")
        
        # Close the socket and exit
        sock.close()
        sys.exit(1)
     
    # SEND DATA AND END PACKETS TO REQUESTER
    
    # buffer each packet by window size
    buffer = [[]]
    cur_index = 0
    cur_num_in_window = 0
    for part in range(len(filePart)):
        buffer[cur_index].append(filePart[part])
        cur_num_in_window += 1
        if cur_num_in_window == window:
            cur_index += 1
            cur_num_in_window = 0
    
    sock.setblocking(False)
    
    # Send Data packets by window size
    for window_of_packets in buffer:
        
        # we said tuples, but changed to lists, so its list of packet lists
        list_of_packet_tuples = []
        
        for packet_part in window_of_packets:
            outer_length = 9 + length
            packet = create_packet(priority, port, requestAddress[0], requesterPort, outer_length, packet_part, seqNo)
            curTime = time.time()
            packet_tuple = [packet, curTime, 1]
            list_of_packet_tuples.append(packet_tuple)
            sock.sendto(packet, (f_hostname, f_port))
            
        num_of_ack = 0
        
        # if we remove from list, it might effect the for loop, so we need this to keep track of which packets we received ACKs for
        ack_received = [False] * window
        
        # for each group of packets, wait for ACKs
        while num_of_ack < window:
            
            # once ack received for curr packet, then we remove it from window_of_packets
            curTime = time.time()
            for index, tuple in enumerate(list_of_packet_tuples):
                
                # either we have already received an ACK for this packet, or we have resent 5 times
                if ack_received[index]:
                    continue
                
                # if we already resent 5 times, then we remove it from the list
                if tuple[2] == 5:
                    # list_of_packet_tuples.remove(tuple)
                    ack_received[index] = True
                    
                    # even though we didn't receive an ACK, we need this for the while loop to end
                    num_of_ack += 1
                    
                    continue
                
                # if we have not resent 5 times, then we check if we need to resend
                if curTime + timeout > tuple[1]:
                    ack_packet, addr = sock.recvfrom(5000)
                    
                    # after timeout amount, if we receive an ACK, then we remove it from the list
                    if ack_packet is not None:
                        
                        # ACK received
                        num_of_ack += 1
                        
                        ack_received[index] = True
                        
                        pass
                    else: 
                        # ACK not received, resend packet
                        tuple[2] += 1
                        sock.sendto(packet, (f_hostname, f_port))
    
    # STUFF BELOW IS OLD CODE, KEEPING FOR REFERENCE
    
    for i in filePart:
        # Create a packet
        packetType = 'D'.encode()
        #if b'\n' in i:
	        #packetLength = len(i) + 1
        #else:
        packetLength = len(i)
        #packetLength = len(i)
        header = struct.pack('!cII', packetType, seqNo, packetLength)
        packet = header + i
        
         # Send the packets to requester
        sock.sendto(packet, (requestAddress[0], requesterPort))
        
        curTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # Print what was sent
        print(f"DATA Packet")
        print(f"send time: {curTime}")
        print(f"requester addr: {socket.gethostname()}:{requesterPort}")
        print(f"Sequence num: {seqNo}")
        print(f"length: {packetLength}")
        print(f"payload: {i.decode('utf-8')[:4]}\n")
        
        seqNo += packetLength
    
    # Send End packet
    packetType = 'E'.encode()
    packetLength = 0
    header = struct.pack('!cII', packetType, seqNo, packetLength)
    payload = b''
    
    packet = header + payload
    
        # Send the packets to requester
    sock.sendto(packet, (requestAddress[0], requesterPort))
    
    curTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # Print what was sent
    print(f"END Packet")
    print(f"send time: {curTime}")
    print(f"requester addr: {socket.gethostname()}:{requesterPort}")
    print(f"Sequence num: {seqNo}")
    print(f"length: {0}")
    print(f"payload: ""\n")
        
    # Close the socket
    sock.close()
        
main()
