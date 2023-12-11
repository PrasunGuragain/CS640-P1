import socket

def routetrace(routetrace_port, source_hostname, source_port, destination_hostname, destination_port, debug_option):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((socket.gethostname(), routetrace_port))
    host_ip = socket.gethostbyname(socket.gethostname())
    packet_host_ip = socket.inet_aton(host_ip)
    # packet_host_up = int.from_bytes(packed_host_ip, byteorder='big)

def createRouteTracePacket(ttl, source_hostname, source_port, destination_hostname, destination_port):
    
