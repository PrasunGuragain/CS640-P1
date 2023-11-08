import struct
import sys
import socket
import time
from datetime import datetime

def main():
    '''
    Packet Type:   'D'
    Sequence Number: seqNo
    Length: packetLength
    Payload: 'fileData'
    '''
    
    #request packet
    '''
    Packet Type:   'R'
    Sequence Number: 0
    Length: 0
    Payload: 'file1.txt'
    '''
    
    #end packet
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
     
    # Send Data packets
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
