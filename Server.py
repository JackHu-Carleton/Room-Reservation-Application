# Author: Zijun Hu
# Copyright © 2021 Zijun Hu. All rights reserved.
# This is the Server program for the reservation system.
import os.path
import sys
import threading
import time
import random
from socket import *
import socket
import struct
from datetime import datetime


def check_if_string_in_file(file_name, string_to_search):
    """ Check if any line in the file contains given string """
    # Open the file in read only mode
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string_to_search in line:
                return True
    return False


def processClientRequest(clientRequest):
    if clientRequest[0] == "days":  # Output the list of all days for which a reservation can be made
        f = open("days.txt", "r")
        outputMessage = "Here is the list of all days for which a reservation can be made:\n" + f.read()
        f.close()

    elif clientRequest[0] == "rooms":  # Output the list of all rooms for which reservations can be made
        f = open("rooms.txt", "r")
        outputMessage = "Here is the list of all rooms for which a reservation can be made:\n" + f.read()
        f.close()

    elif clientRequest[0] == "timeslots":  # Output the list of all timeslots for which a reservation can be made
        f = open("timeslots.txt", "r")
        outputMessage = "Here is the list of all timeslots for which a reservation can be made:\n" + f.read()
        f.close()

    elif clientRequest[0] == "check":  # Output all existing reservations for the input room
        if len(clientRequest) < 2:  # Check if the room information is missing
            outputMessage = "Missing room name!"
        else:
            # Filter all reservation information related to the input room.
            existReservation = [line for line in open('reservations.txt') if clientRequest[1] in line]
            if len(existReservation) > 0:  # Check if there are any reservation information related to the input room.
                outputMessage = "Here is all existing reservations for the room {}:\n".format(
                    clientRequest[1]) + ''.join(
                    existReservation)
            else:
                outputMessage = "There is no existing reservations for the room {}.".format(clientRequest[1])

    elif clientRequest[0] == "reserve":  # Direct reserve the room, write into reserve txt if reservation is available.
        if len(clientRequest) < 4:  # Check if all needed information was given and valid
            outputMessage = "Missing needed information!"
        elif not check_if_string_in_file('rooms.txt', clientRequest[1]):
            outputMessage = "Room entered is not valid, please reenter."
        elif not check_if_string_in_file('timeslots.txt', clientRequest[2]):
            outputMessage = "Time slots entered is not valid, please reenter."
        elif not check_if_string_in_file('days.txt', clientRequest[3]):
            outputMessage = "Day entered is not valid, please reenter."
        elif check_if_string_in_file('reservations.txt',
                                     "{} {} {}".format(clientRequest[1], clientRequest[2], clientRequest[3])):
            # Check if reservation is conflict with exist one
            outputMessage = "Reserve entered is conflict with an exist reservation, please reenter."
        else:
            reserveInfo = "{} {} {}".format(clientRequest[1], clientRequest[2], clientRequest[3])
            with open('reservations.txt', 'a') as f:
                f.write(reserveInfo + "\n")
            outputMessage = "Reserve for room {} at {} {} has been stored in reserved.txt.\n".format(clientRequest[1],
                                                                                                     clientRequest[2],
                                                                                                     clientRequest[3])
    elif clientRequest[0] == "delete":  # Delete reservation from reservations.txt
        reserveNeedDelete = "{} {} {}".format(clientRequest[1], clientRequest[2], clientRequest[3])
        if check_if_string_in_file('reservations.txt', reserveNeedDelete):  # Check if reservation exist in text file
            reservationLeft = [line for line in open('reservations.txt') if reserveNeedDelete not in line]
            with open('reservations.txt', 'w') as f:
                for item in reservationLeft:
                    f.write(item)
            outputMessage = "Reservation for {} removed from reserved.txt.".format(reserveNeedDelete)
        else:
            outputMessage = "Reservation entered don't exist, please check again."

    else:
        outputMessage = "Unknown Command, please retry"

    return outputMessage


class ClientThread(threading.Thread):
    def __init__(self, inMessage, add, threadID):
        threading.Thread.__init__(self)
        self.incomeMessage = inMessage
        self.address = add
        self.threadID = threadID

    def run(self):
        print("Start executing client thread: ", self.threadID)

        receiveTime = datetime.utcnow()  # TimeStamp when receive the message (This timestamp should be later or equal the Client sending timestamp)
        clientRequest = self.incomeMessage.decode().split(" ")
        outputMessage = processClientRequest(clientRequest)  # Start process message
        outputMessage = "{}".format(
            receiveTime) + "|" + outputMessage  # Add TimeStamp as header for Client side to check
        serverSocket.sendto(outputMessage.encode(), self.address)  # Server response

        timeToSleep = random.randint(5, 10)
        time.sleep(timeToSleep)
        print("End executing client thread: ", self.threadID)


multicast_group = sys.argv[1]
listenPort = sys.argv[2]

# Create a UDP socket
# Notice the use of SOCK_DGRAM for UDP packets
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Assign IP address and port number to socket
serverSocket.bind(('', int(listenPort)))

# Tell the operating system to add the socket to the multicast group on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
serverSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Check if all data storage file exist
if not (os.path.exists("days.txt") and os.path.exists("rooms.txt") and os.path.exists("timeslots.txt") and
        os.path.exists("reservations.txt")):
    raise Exception("Data storage file is missing!")

# Create threading needed variables
thread_count = 0
threads = []

while True:
    try:
        # Receive the client packet along with the address it is coming from
        incomeMessage, address = serverSocket.recvfrom(1024)
        thread_count += 1
        newThread = ClientThread(incomeMessage, address, thread_count)  # create thread
        newThread.start()
        threads.append(newThread)
    except error:
        for t in threads:
            t.join()
        break
