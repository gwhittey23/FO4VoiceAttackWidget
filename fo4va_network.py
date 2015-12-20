#!/usr/bin/env python

import socket, threading

class ClientThread(threading.Thread):

    def __init__(self, ip, port, socket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.socket = socket
        print ("[+] New thread started for "+ip+":"+str(port))

    def run(self):
        # use self.socket to send/receive

        print ("Connection from : "+ip+":"+str(port))
        txtMsg="\nWelcome to the server\n\n"
       # clientsock.send(txtMsg.encode('utf-8'))

        data = "dummydata"

        while len(data):
            data = clientsock.recv(2048)
            print ("Client sent : %s" %(data.decode()))
            strRtrMsg = "OK It Worked"
            clientsock.send(strRtrMsg.encode('utf-8'))

        print ("Client disconnected...")

host = "0.0.0.0"
port = 8089

tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

tcpsock.bind((host,port))
threads = []


while True:
    tcpsock.listen(4)
    print ("\nListening for incoming connections...")
    (clientsock, (ip, port)) = tcpsock.accept()
    newthread = ClientThread(ip, port, clientsock)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()