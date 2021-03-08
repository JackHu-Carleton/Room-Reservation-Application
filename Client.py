# Author: Zijun Hu
# Student number: 101037102
# This is the Client program for the reservation system.

import sys
from socket import *
import struct
from datetime import datetime

serverName = sys.argv[1]
serverPort = sys.argv[2]

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1)  # Set timeout to avoid message lose
multicast_group = (serverName, int(serverPort))

# Set the time-to-live for messages to 1 so they do not go past the local network segment.
ttl = struct.pack('b', 1)
clientSocket.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, ttl)

while True:
    message = input("\nPlease enter a command: ")  # Ask for input command
    if message == "quit":  # Quit client if user input quit
        break
    clientSendTime = datetime.utcnow()  # TimeStamp before send the message (Server's timeStamp should later or equal
    # than this one)
    clientSocket.sendto(message.encode(), multicast_group)
    while True:
        try:
            modifiedMessage, serverAddress = clientSocket.recvfrom(2048)  # Wait for the reply message
            ServerReceiveTime = datetime.strptime(modifiedMessage.decode().split("|")[0], "%Y-%m-%d %H:%M:%S.%f")
            if ServerReceiveTime >= clientSendTime:  # Avoid receive message from last prior request
                serverMessage = modifiedMessage.decode().split("|")[1]
                print(serverMessage)  # Output the message from server
                messageUnShowed = False
                break
        except timeout:
            print("Request timed out!")  # Print warning when timed out
            print("Trying to resend the message...\n")
            clientSendTime = datetime.utcnow()
            clientSocket.sendto(message.encode(), multicast_group)

clientSocket.close()
