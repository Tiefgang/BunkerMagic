import socket

# Set up the UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

message = b"Hello, broadcast!"
broadcast_address = ('10.13.37.255', 12345)  # Replace with the correct broadcast address

# Send the message
sock.sendto(message, broadcast_address)

print(f"Sent message: {message} to {broadcast_address}")

