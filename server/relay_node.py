import socket
import sys
import os
import re
import time
import urllib2

RECV_BUFFER_SIZE = 1024 

def Ping(alias,number_of):
	print"Ping to {} , {} times".format(alias,number_of)
	return os.popen("ping -c "+ str(number_of) + " "+ alias).read()

def traceroute(alias):
	print"Traceroute to {}".format(alias)
	return os.popen("traceroute " + alias).read()

def break_ping_info(info):
	try:
		return float(info.split('\n')[-2].split('/')[4])
	except IndexError:
		print "Cannot connect to end server"
		return -1

def break_traceroute_info(info):
	return int(re.search(r'\d+',info.split('\n')[-2]).group())

def download_file(filename,ext):
        start = time.time()
	response = urllib2.urlopen(filename)
        img = response.read()
        end = time.time()
        print('Took {} seconds to download the file.'.format(end - start))
	return img

def server():

	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Bind the socket to the port
	
	#By setting the host name to the empty string, it tells the bind() method to fill in the address of the current machine.

	server_address = ('', int(sys.argv[1]))
	print >>sys.stderr, 'starting up on %s port %s' % server_address
	sock.bind(server_address)

	# Listen for incoming connections
	sock.listen(1)

	while True:
	    # Wait for a connection
	    print >>sys.stderr, 'waiting for a connection'
	    connection, client_address = sock.accept()
	
	    try:
	        print >>sys.stderr, 'connection from', client_address

	        # Receive the data in small chunks and retransmit it
        	while True:
	        	data = connection.recv(RECV_BUFFER_SIZE)
			print >>sys.stderr, 'received "%s"' % data
			if(data):
				if(data.split(',')[1] in 'download'):
					print"Downloading file:\n"+data[0]
					data=data.split(',')
					ext= data[0].split('.')[-1]						
					msg=download_file(data[0],ext)
					with open("download_RM."+ext,'wb') as d:
						d.write(msg)
					print"Sending file back to client"
					with open("download_RM."+ext,'rb') as d:
						connection.send(d.read())
						connection.send("done")
				else:
					server,iterations = data.split(',')
					data = str(break_ping_info(Ping(server,iterations))) + ',' + str(break_traceroute_info(traceroute(server)))
					print"Sending file back to client"
					connection.sendall(data)	
				break
	            
	    finally:
	        # Clean up the connection
        	connection.close()

server()
