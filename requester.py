import socket
import sys

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
    # Parse command line arguments
    
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
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    
    data, sender_address = sock.recvfrom(1024)
    
    tracker_info = parse_tracker("./tracker.txt")
    
    print("Current data: ", tracker_info)
    
    

main()