#!/usr/bin/python

import socket
from socket import *
import sys
import os
import re
import threading
import urllib2
import time
from Crypto.PublicKey import RSA

RECV_BUFFER_SIZE = 1024

def client(server,port,end_server,iterations):
        # Create a TCP/IP socket
        sock = socket(AF_INET, SOCK_STREAM)


        # Connect the socket to the port where the server is listening
        server_address = (server, int(port))
        print >>sys.stderr, 'connecting to %s port %s' % server_address
        sock.settimeout(100)
        sock.connect(server_address)
        
        try:

            # Send data
            message =end_server + ',' + str(iterations)
            print >>sys.stderr, 'sending "%s"' % message
            sock.sendall(message)

            try:
                data = sock.recv(RECV_BUFFER_SIZE)
            except socket.timeout:
                   print 'timeout,try again'
                   exit(0)

            print >>sys.stderr, 'received "%s"' % data

        finally:
            print >>sys.stderr, 'closing socket'
            sock.close()

        return data

def read_argv():
    return (sys.argv[sys.argv.index("-e") +1] ,sys.argv[sys.argv.index("-r")+1])

def init_lists(end_servers,relay_nodes):
        with open(end_servers) as end_servers_file:
                lines = end_servers_file.readlines()

        end_dict = {}
        for line in lines[:-1]:
                tupl = line.split(',')
                tupl[0] = tupl[0].replace("\n","").replace(" ","").replace("\r","")
                tupl[1] = tupl[1].replace("\n","").replace(" ","").replace("\r","")
                end_dict[tupl[1]] = tupl[0]

        with open(relay_nodes) as relay_nodes_file:
                lines = relay_nodes_file.readlines()

	relay_dict = []
        for line in lines:
                tupl = line.split(',')
                relay_dict.append([tupl[0].replace("\n","").replace(" ","").replace("\r","")
					,tupl[1].replace("\n","").replace(" ","").replace("\r","")
					,tupl[2].replace("\n","").replace(" ","").replace("\r","")])

        return end_dict,relay_dict

def read_info():
	alias = raw_input("Alias name: ")
	way = raw_input("latency or hops: ")
	no_of = raw_input("Number of ping: ")

   	return alias.strip() , int(no_of), way.strip()


def Ping(alias,number_of):
	return  os.popen("ping -c "+ str(number_of) + " "+ alias).read().split('\n')

def traceroute(alias):
 	return (os.popen("traceroute " + alias).read()).split('\n')

def break_ping_info(info):
	try:
		return float(info[-2].split('/')[4])
	except IndexError:
		print "Cannot connect to end server"
		return -1

def break_traceroute_info(info):
	return int(re.search(r'\d+',info[-2]).group())

global results_ping
global results_traceroute
results_ping = []
results_traceroute = []

threadLock = threading.Lock()

def relay_mode(lista,alias,iterator):
        global relay_data
	x=y=errorflag=0;
	if lista[0] not in 'DM':
	        x,y = client(lista[1],lista[2],alias,iterator).split(',')

        print "Ping to {}, {} times".format(lista[0],iterator)
	ping_no = break_ping_info(Ping(lista[1],iterator))

        print "Traceroute to {}".format(lista[0])
	traceroute_no = break_traceroute_info(traceroute(lista[1]))
       
	if(float(x)==-1 or ping_no==-1): 
		errorflag=1
		print "Error connecting to end server"
        
	ping_no += float(x)
        traceroute_no += int(y)
	print "Latency for {} is {} and hops is {}".format(lista[0],ping_no,traceroute_no)
        threadLock.acquire()
	if(errorflag==0):
	        results_ping.append([lista[0],ping_no])
	results_traceroute.append([lista[0],traceroute_no])
        threadLock.release()

def find_min(lista):
	m = 0
	for i in range(len(lista)):
		if lista[m][1] > lista[i][1]:
			m=i

	return str(lista[m][0])

def read_what_to_download():
        filename = raw_input("Which file to download: ")
	ext = filename.split('.')[-1]
	return filename,ext

def download_file(server,port,filename,ext):
	start = time.time()

        # Create a TCP/IP socket
        sock = socket(AF_INET, SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (server, int(port))
        print >>sys.stderr, 'connecting to %s port %s' % server_address
        sock.connect(server_address)

        try:

                # Send data
                message= filename+','+ 'download'
                sock.sendall(message)
                # Look for the response
                fileimg=open("downloaded_file_RM."+ext,'wb')
                while 1:
                        data = sock.recv(RECV_BUFFER_SIZE)
                        if data not in "done":
                                fileimg.write(data)
                        else:  
				print"Received file:\n {}\n from relay {}".format(filename,server)
				break

                fileimg.close()

        finally:
                print >>sys.stderr, 'closing socket'
                sock.close()
	
        end = time.time()
        print('Took {} seconds to download the file.'.format(end - start))

def main():
	end_server_file,relay_nodes_file = read_argv()
	end_server_list,relay_nodes_list = init_lists(end_server_file,relay_nodes_file)
	alias , iteration, way = read_info()

	relay_nodes_list.append(['DM',end_server_list[alias],0])
                
        threads = []
	for lists in relay_nodes_list:
                t= threading.Thread(target=relay_mode, args=(lists,end_server_list[alias],iteration))
                t.setDaemon(True)
                threads.append(t)
                t.start()
        
        for t in threads:
                t.join()

	if way in 'hops':
		best_opt = find_min(results_traceroute)
	else:
		best_opt = find_min(results_ping)


	filename,ext = read_what_to_download()

	for l in relay_nodes_list:
		if(best_opt in l[0]):
			best_opt = l
			break;

	print "Best option is: {} with latency: {} and hops: {}".format(best_opt[0],best_opt[1],best_opt[2])

	if best_opt[0] in 'DM':
	        start = time.time()
		response = urllib2.urlopen(filename)
		img = response.read()
		with open("download_DM_file."+ext,'wb') as fileimg:
			fileimg.write(img)
	else:
		download_file(best_opt[1],best_opt[2],filename,ext)
	
        end = time.time()
        print('Took {} seconds to download the file.'.format(end - start))
main()
