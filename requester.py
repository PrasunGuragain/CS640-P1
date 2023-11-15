import socket
import struct
import sys
from datetime import datetime
import math
import time

def create_packet(priority, s_port, d_address, d_port, packet1_length, packet_part, seqNo, packetType):
    # socket.inet_aton(requester_ip)
    # msg = struct.pack('c l h l h I c I I')

    priority_type = struct.pack('B', priority)
    src_ip_address = struct.pack('4s', socket.inet_aton(socket.gethostbyname(socket.gethostname())))
    src_port = struct.pack('H', s_port)
    dest_ip_address = struct.pack('4s', socket.inet_aton(socket.gethostbyname(d_address)))
    dest_port = struct.pack('H', d_port)
    length1 = struct.pack('I', packet1_length)
    
    header1 = priority_type + src_ip_address + src_port + dest_ip_address + dest_port + length1
    
    packetLength = len(packet_part)
    header2 = struct.pack('!cII', packetType, seqNo, packetLength)
    payload = header2 + packet_part.encode('utf-8')
    
    packet = header1 + payload
    
    return packet
    
def parse_packet(packet):
    priority = struct.unpack('B', packet[:1])
    src_ip_address = struct.unpack('4s', packet[1:5])
    src_port = struct.unpack('H', packet[5:7])
    dest_ip_address = struct.unpack('4s', packet[7:11])
    dest_port = struct.unpack('H', packet[11:13])
    length = struct.unpack('I', packet[13:17])

    # payload
    packet_type = struct.unpack('c', packet[17:18])
    sequence_number = struct.unpack('I', packet[18:22])
    payload_length = struct.unpack('I', packet[22:26])
    payload = packet[26:26 + payload_length]

    return priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload

def parse_tracker(tracker_file_path):
    file_parts = {} 
    
    # read tracker
    with open(tracker_file_path, 'r') as file:
        for line in file:
            columns = line.strip().split()
            if len(columns) == 4:
                filename, part_id, sender_hostname, sender_port = columns
                
                # get the id and port
                part_id = int(part_id)
                sender_port = int(sender_port)

                part_info = {"ID": part_id, "SenderHostname": sender_hostname, "SenderPort": sender_port}
                
                # add the info into its file
                if filename not in file_parts:
                    file_parts[filename] = []
                file_parts[filename].append(part_info)
                
    # Sort file parts within each file entry based on their IDs
    for filename, parts in file_parts.items():
        file_parts[filename] = sorted(parts, key=lambda x: x['ID'])
        
    return file_parts

def main():
    # PARSE COMMAND LINE ARGUMENTS
    
    # port
    if '-p' in sys.argv:
        p = sys.argv.index('-p')
        port = int(sys.argv[p + 1])
        if port < 2049 and port > 65536:
            print("Sender port should be in this range: 2049 < port < 65536")
            sys.exit(1)
    else:
        print("Port argument (-p) is missing.")
        sys.exit(1)
        
    # file option
    if '-o' in sys.argv:
        o = sys.argv.index('-o')
        file_option = sys.argv[o + 1]
    else:
        print("File option argument (-o) is missing.")
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
    
    # window
    if '-w' in sys.argv:
        w = sys.argv.index('-w')
        window = int(sys.argv[w + 1])
    else:
        print("window argument (-w) is missing.")
        sys.exit(1)
    
    # PARSE TRACKER
    
    tracker_info = parse_tracker("./tracker.txt")

    # Check if the requested file is in the tracker
    if file_option not in tracker_info:
        print("Requested file not found in the tracker.")
        sys.exit(1)
    
    start_time = time.time()
    
    # SEND REQUEST PACKET TO SERVER
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    
    
    for part_info in tracker_info[file_option]:
        sender_hostname = part_info["SenderHostname"]
        sender_port = part_info["SenderPort"]
        part_id = part_info["ID"]

        request_packet = create_packet(1,port,sender_hostname, sender_port, 0, file_option, 0, 'R'.encode())
        
        # Send the request packet to the sender
        sock.sendto(request_packet, (f_hostname, f_port))
        
    
    # RECEIVE PACKETS FROM SERVER AND SEND ACKS
    
    # summaryInfo[address] = [Total Data packets, Total Data bytes]
    summary_info = {}
    
    num_of_senders =  0
    num_of_ends = 0
    
    # received_packets[address] = {sequence number: payload}
    received_packets = {}
    
    sender_order = []
    
    # empty file
    with open(file_option, 'w') as file:
        pass
    
    while True:
        # Get packet from sender
        data, sender_address = sock.recvfrom(1024) 
        priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload = parse_packet(data)
        
        # TODO: sender might send the same packet multiple times, check if the packet is already received
        
        # Verify that the destination IP address in its received packet (data packets or end packets) is indeed its own IP address
        if dest_ip_address != socket.gethostbyname(socket.gethostname()):
            pass # What to do here?
        
        # Send ack to sender
        ack_packet = struct.pack('!cII', b'A', sequence_number, 0)
        sock.sendto(ack_packet, sender_address)
        
        # packet_type, sequence_number, payload_length = struct.unpack('!cII', data[:9])
        payload = payload[9:9 + payload_length]  # extract payload
        
        if sender_address[1] not in received_packets:
            received_packets[sender_address[1]] = {}
            
            
        curTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        
        # Initialize summaryInfo for each sender
        if sender_address[1] not in summary_info:
            summary_info[sender_address[1]] = [0, 0]
            num_of_senders += 1

        # Process the payload data as needed (writing to file, assembling file parts, etc.)
    
        # Check for END packet and break the loop if received END packet for all senders
        if packet_type == b'E':
            num_of_ends += 1
            end_time = time.time()
            
            # Print end receipt information
            print("End Packet")
            print(f"recv time: {curTime}")
            print(f"sender addr: {sender_address[0]}:{sender_address[1]}")
            print(f"sequence: {sequence_number}")
            print(f"length: {0}")
            print(f"payload: {0}\n")
            
            duration = int(((end_time) - (start_time)) * 1000)
            average = math.ceil((summary_info[sender_address[1]][0]) / (duration))
            
            # summary
            print("Summary")
            print(f"sender addr: {sender_address[0]}:{sender_address[1]}")
            print(f"Total Data packets: {summary_info[sender_address[1]][0]}")
            print(f"Total Data bytes: {summary_info[sender_address[1]][1]}")
            print(f"Average packets/second: {average}")
            print(f"Duration of the test: {duration} ms\n")


            
            # save to split.txt
            sorted_packets = sorted(received_packets[sender_address[1]].items())
            
            reassembled_data = b''.join(packet_payload for _, packet_payload in sorted_packets)
            
           
            
            
            # add each payload to file
            with open(file_option, "ab") as reassembled_file:
                reassembled_file.write(reassembled_data)

            if num_of_ends == len(tracker_info[file_option]):
                break
        else:
            # Print data receipt information
            print("DATA Packet")
            print(f"recv time: {curTime}")
            print(f"sender addr: {sender_address[0]}:{sender_address[1]}")
            print(f"sequence: {sequence_number}")
            print(f"length: {payload_length}")
            print(f"payload: {payload.decode()[:4]}\n")
           
            received_packets[sender_address[1]][sequence_number] = payload
            # update total data packets and bytes
            summary_info[sender_address[1]][0] += 1
            summary_info[sender_address[1]][1] += payload_length
        
        sequence_number += payload_length
    
    # Close the socket
    sock.close()

main()
