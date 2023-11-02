import socket
import sys

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
    
# Queue size
if '-q' in sys.argv:
    q = sys.argv.index('-q')
    queue_size = int(sys.argv[q + 1])
else:
    print("Queue size argument (-q) is missing.")
    sys.exit(1)

# Filename
if '-f' in sys.argv:
    f = sys.argv.index('-f')
    filename = int(sys.argv[f + 1])
else:
    print("Filename argument (-f) is missing.")
    sys.exit(1)

# Log
if '-l' in sys.argv:
    l = sys.argv.index('-l')
    log = int(sys.argv[l + 1])
else:
    print("Log argument (-l) is missing.")
    sys.exit(1)

# Create a socket for the requester
requester_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
requester_socket.bind(('0.0.0.0', port))

# Listen from server
