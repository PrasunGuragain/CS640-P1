import struct
import sys
import socket
import time
from datetime import datetime
import math

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

    return priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload

# TODO: Check create_packet function
def create_packet(priority, s_port, d_address, d_port, packet1_length, packet_part, seqNo, packetType):
    priority_type = struct.pack('B', priority)
    src_ip_address = struct.pack('4s', socket.inet_aton(socket.gethostbyname(socket.gethostname())))
    src_port = struct.pack('H', s_port)
    dest_ip_address = struct.pack('4s', socket.inet_aton(socket.gethostbyname(d_address)))
    dest_port = struct.pack('H', d_port)
    length1 = struct.pack('I', packet1_length)
    
    header1 = priority_type + src_ip_address + src_port + dest_ip_address + dest_port + length1
    
    encodedPacketType = packetType.encode()
    packetLength = len(packet_part)
    header2 = struct.pack('!cII', encodedPacketType, seqNo, packetLength)
    
    payload = header2 + packet_part.encode('utf-8')
    
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
    
    total_transmission, total_retransmission = 0, 0
    
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
        length_chunk = int(sys.argv[l + 1])
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
        givenPriority = int(sys.argv[i + 1])
    else:
        print("priority argument (-i) is missing.")
        sys.exit(1)
    
    # timeout
    if '-t' in sys.argv:
        t = sys.argv.index('-t')
        timeout = int(sys.argv[t + 1])
    else:
        print("timeout argument (-t) is missing.")
        sys.exit(1)
    
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))

    
    # GET REQUEST PACKET FROM REQUESTER 
    requestPacket, requestAddress = sock.recvfrom(5000)

    priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, window, payload = parse_packet(requestPacket)
        
    fileName = payload.decode()
            
     # SPLIT FILE INTO CHUNCKS FOR PACKETS
    try:
        filePart = []
        with open(fileName, "r") as file:
            while True:
                # read in chucks by length
                chunk = file.read(length_chunk)
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
        total_transmission += 1
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
    # buffer = [[]]
    # length of buffer is file size / length_chunk
    buffer = [[] for i in range(math.ceil(len(filePart) / window))]
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
        
        match_by_seq = {}
        
        received_ack_packets_for_seq = []
        
        for packet_part in window_of_packets:
            outer_length = 9 + length
            packet = create_packet(priority, port, requestAddress[0], requesterPort, outer_length, packet_part, seqNo, 'D')
            
            curTime = time.time()
            packet_tuple = [packet, curTime, 1, seqNo, False]
            match_by_seq[seqNo] = packet_tuple
            list_of_packet_tuples.append(packet_tuple)
            
            print(f"Packet: {packet_tuple} SENT to {f_hostname}:{f_port}")
            total_transmission += 1
            sock.sendto(packet, (f_hostname, f_port))
            
            curTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            '''
            # Print what was sent
            print(f"DATA Packet")
            print(f"send time: {curTime}")
            print(f"requester addr: {requestAddress[0]}:{requesterPort}")
            print(f"Sequence num: {seqNo}")
            print(f"length: {packetLength}")
            print(f"payload: {packet_part}\n")
            '''
            
            seqNo += 1
            
        num_of_ack = 0
        
        # for each group of packets, wait for ACKs
        while num_of_ack < window:
            
            # for each packet, listen for ack until timeout expires
            for key, value in match_by_seq.items():
                # if the fifth time we resend
                if value[2] == 5:
                    print(f"Failed to receive ACK after 5 retransmits - Giving up on packet with sequence number: {value[3]}")
                    continue
                if  value[4]:
                    continue
                # if current packet is already acked, move on 
                
                # while current packet is not acked, and timeout not expired, listen for ack packet
                # send = 80, time = 50, stop ack/resent = 80 + 50 = 130, cur = 100
                while time.time() < value[1] + timeout:
                    #print(f"Packet: {value} LISTENING for ACK from {f_hostname}:{f_port}")
                    try:
                        ack_packet, addr = sock.recvfrom(5000)
                        priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, window, payload = parse_packet(ack_packet)
                        
                        match_by_seq[sequence_number][4] = True
                        num_of_ack += 1
                        if sequence_number == value[3]:
                            break
                    except BlockingIOError:
                        pass
                
                # if timeout expires and no ack packet, then retransmit, update tuple
                value[2] += 1
                total_retransmission += 1
                total_transmission += 1
                sock.sendto(value[0], (f_hostname, f_port))
    
    # def create_packet(priority, s_port, d_address, d_port, packet1_length, packet_part, seqNo, packetType):
    # TODO: Send End packet
    outer_length = 0 
    packet_part = ""
    endPacket = create_packet(givenPriority, port, requestAddress[0], requesterPort, outer_length, packet_part, seqNo, 'E')
    total_transmission += 1
    sock.sendto(endPacket, (f_hostname, f_port))
    

    # print loss rate
    print(f"LOSS RATE: {(total_retransmission/total_transmission) * 100}%")
        
main()
