import socket
import struct
import argparse

def routetrace(routetrace_port, source_ip, source_port, destination_ip, destination_port, debug_option):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((socket.gethostname(), routetrace_port))
    host_ip = socket.gethostbyname(socket.gethostname())
    packet_host_ip = socket.inet_aton(host_ip)
    # packet_host_up = int.from_bytes(packed_host_ip, byteorder='big)
    
    ttl = 0 # Time to live
    while True:
        sendingPacket = createRouteTracePacket(ttl, host_ip, routetrace_port, source_ip, source_port, destination_ip, destination_port)
        s.sendto(sendingPacket, (source_ip, source_port))
        
        if debug_option == 1:
            print(f"Debug. Sent Packet:")
            print(f"TTL: {ttl}")
            print(f"Source IP: {source_ip}")
            print(f"Source Port: {source_port}")
            print(f"Destination IP: {destination_ip}")
            print(f"Destination Port: {destination_port}\n")

        packet, address = s.recvfrom(5000)

        print("PACKET RECEIVED HERE\n")
        
        packetInfo = parsePacket(packet)
        
        received_ttl = packetInfo["ttl"]
        received_source_ip = packetInfo["source_ip"]
        received_source_port = packetInfo["source_port"]
        received_destination_ip = packetInfo["destination_ip"]
        received_destination_port = packetInfo["destination_port"]
        
        print(f"Received from IP: {source_ip}, Port: {source_port}\n")
        
        if debug_option == 1:
            print(f"Debug. Received Packet:")
            print(f"TTL: {received_ttl}")
            print(f"Source IP: {received_source_ip}")
            print(f"Source Port: {received_source_port}")
            print(f"Destination IP: {received_destination_ip}")
            print(f"Destination Port: {received_destination_port}\n")
            
        if received_source_ip == destination_ip and received_source_port[0] == destination_port:
            print(f"Destination reached")
            break
        
        ttl += 1

def createRouteTracePacket(ttl, host_ip, routetrace_port, source_ip, source_port, destination_ip, destination_port):
    print(f"routetrace_port: {routetrace_port}\n")
    sendingPacketType = struct.pack('c', 'T'.encode('utf-8'))
    sendingTTL = struct.pack('I', ttl)
    sendingOgIp = struct.pack('4s', socket.inet_aton(host_ip))
    sendingOgPort = struct.pack('H', routetrace_port)
    sendingSourceIp = struct.pack('4s', socket.inet_aton(source_ip))
    sendingSourcePort = struct.pack('H', source_port)
    sendingDestinationIp = struct.pack('4s', socket.inet_aton(destination_ip))
    sendingDestinationPort = struct.pack('H', destination_port)
    
    packet = sendingPacketType + sendingTTL + sendingOgIp + sendingOgPort + sendingSourceIp + sendingSourcePort + sendingDestinationIp + sendingDestinationPort
    
    return packet

def parsePacket(packet):
    typeFormat = 'c'
    ttlFormat = 'I'
    ipFormat = '4s'
    portFormat = 'H'
    
    packetType = struct.unpack(typeFormat, packet[:struct.calcsize(typeFormat)])
    packet = packet[struct.calcsize(typeFormat):]
    
    ttl = struct.unpack(ttlFormat, packet[:struct.calcsize(ttlFormat)])
    packet = packet[struct.calcsize(ttlFormat):]
    
    ogIp = struct.unpack(ipFormat, packet[:struct.calcsize(ipFormat)])
    packet = packet[struct.calcsize(ipFormat):]
    
    ogPort = struct.unpack(portFormat, packet[:struct.calcsize(portFormat)])
    packet = packet[struct.calcsize(portFormat):]
    
    source_ip = socket.inet_ntoa(struct.unpack(ipFormat, packet[:struct.calcsize(ipFormat)])[0])
    packet = packet[struct.calcsize(ipFormat):]
    
    source_port = struct.unpack(portFormat, packet[:struct.calcsize(portFormat)])
    packet = packet[struct.calcsize(portFormat):]
    
    destination_ip = socket.inet_ntoa(struct.unpack(ipFormat, packet[:struct.calcsize(ipFormat)])[0])
    packet = packet[struct.calcsize(ipFormat):]
    
    destination_port = struct.unpack(portFormat, packet[:struct.calcsize(portFormat)])
    packet = packet[struct.calcsize(portFormat):]
    
    packetInfo = {
        'ttl': ttl,
        'source_ip': source_ip,
        'source_port': source_port,
        'destination_ip': destination_ip,
        'destination_port': destination_port
    }
    
    return packetInfo
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', type=int, required=True)
    parser.add_argument('-b', type=str, required=True)
    parser.add_argument('-c', type=int, required=True)
    parser.add_argument('-d', type=str, required=True)
    parser.add_argument('-e', type=int, required=True)
    parser.add_argument('-f', type=int, required=True)
    
    args = parser.parse_args()
    
    routetrace(args.a, args.b, args.c, args.d, args.e, args.f)