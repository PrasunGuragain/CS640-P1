import socket
import struct
import sys
from datetime import datetime
import math
import time

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
    
    
    # PARSE TRACKER
    
    tracker_info = parse_tracker("./tracker.txt")

    # Check if the requested file is in the tracker
    if file_option not in tracker_info:
        print("Requested file not found in the tracker.")
        sys.exit(1)
    
    start_time = time.time()
    
    # SEND REQUEST PACKET TO SERVER
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    
    for part_info in tracker_info[file_option]:
        sender_hostname = part_info["SenderHostname"]
        sender_port = part_info["SenderPort"]
        part_id = part_info["ID"]

        request_packet = struct.pack('!cI', b'R', 0) + file_option.encode('utf-8')
        
        # Send the request packet to the sender
        sock.sendto(request_packet, ('localhost', sender_port))
        
    
    # RECEIVE PACKETS FROM SERVER
    
    # summaryInfo[address] = [Total Data packets, Total Data bytes]
    summary_info = {}
    
    num_of_senders =  0
    num_of_ends = 0
    received_packets = {}
    
    while True:
        # Get packet from sender
        data, sender_address = sock.recvfrom(1024) 
        packet_type, sequence_number, payload_length = struct.unpack('!cII', data[:9])
        payload = data[9:9 + payload_length]  # extract payload
        
        if sender_address[1] not in received_packets:
            received_packets[sender_address[1]] = {}
        else:
            received_packets[sender_address[1]][sequence_number] = payload
            
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
            print(f"payload: {0}\n\n")
            
            #print(f"Start: {start_time}, End: {end_time}\n")
            duration = ((end_time) - (start_time)) * 1000
            average = math.ceil((summary_info[sender_address[1]][0]) / (duration))
            #average2 = (summary_info[sender_address[1]][0]) / (duration)
            
            # summary
            print("Summary")
            print(f"sender addr: {sender_address[0]}:{sender_address[1]}")
            print(f"Total Data packets: {summary_info[sender_address[1]][0]}")
            print(f"Total Data bytes: {summary_info[sender_address[1]][1]}")
            print(f"Average packets/second: {average}")
            print(f"Duration of the test: {duration} ms\n\n")

            # save to split.txt
            sorted_packets = sorted(received_packets[sender_address[1]].items())
            print("Sorted packets: ", sorted_packets)
            reassembled_data = b''.join(packet_payload for _, packet_payload in sorted_packets)
            #print("Sorted Packets:")
            #for seq_number, packet_payload in sorted_packets:
                #print(f"Sequence Number: {seq_number}, Payload: {packet_payload}")

            # Debugging: Print reassembled file content
            #print("Reassembled File Content:")
            #print(reassembled_data.decode())  # Assuming the content is in string format, adjust the decoding method accordingly if necessary

            with open(file_option, "wb") as reassembled_file:
                reassembled_file.write(reassembled_data)

            if num_of_ends == num_of_senders:
                break
        else:
            # Print data receipt information
            print("DATA Packet")
            print(f"recv time: {curTime}")
            print(f"sender addr: {sender_address[0]}:{sender_address[1]}")
            print(f"sequence: {sequence_number}")
            print(f"length: {payload_length}")
            print(f"payload: {payload[:4]}\n\n")
            
            # update total data packets and bytes
            summary_info[sender_address[1]][0] += 1
            summary_info[sender_address[1]][1] += payload_length
        
        sequence_number += payload_length
    
    # Close the socket
    sock.close()

main()