import struct
import sys
import socket

def main():
    print("sent1")
    # Parse command line arguments
    
    # Port
    if '-p' in sys.argv:
        p = sys.argv.index('-p')
        port = sys.argv[p + 1]
        if port > 2049 and port < 65536:
            print("Sender port should be in this range: 2049 < port < 65536")
            sys.exit(1)
    else:
        print("Port argument (-p) is missing.")
        sys.exit(1)
        
    # Requester port
    if '-g' in sys.argv:
        g = sys.argv.index('-g')
        requester_port = sys.argv[g + 1]
    else:
        print("Requester port argument (-g) is missing.")
        sys.exit(1)

    # Rate
    if '-r' in sys.argv:
        r = sys.argv.index('-r')
        rate = sys.argv[r + 1]
    else:
        print("Rate argument (-r) is missing.")
        sys.exit(1)

    # Sequence number
    if '-q' in sys.argv:
        q = sys.argv.index('-q')
        seq_no = sys.argv[q + 1]
    else:
        print("Seq_no argument (-q) is missing.")
        sys.exit(1)

    # Length
    if '-l' in sys.argv:
        l = sys.argv.index('-l')
        length = sys.argv[l + 1]
    else:
        print("Length argument (-l) is missing.")
        sys.exit(1) 
        
    # Open the file
    with open('split.txt', 'rb') as file:
        fileData = file.read()
    
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    
    # Create a packet
    packetType = 'D'.encode()
    header = struct.pack('!cI', packetType, seq_no)
    packet = header + fileData
    
    print("sent1")
    # Send the packets to receiver
    sock.sendto(packet, ('localhost', requester_port))
    
    print("Sent")
    # Close the socket
    # sock.close()
        
main()
print("sent1")
        