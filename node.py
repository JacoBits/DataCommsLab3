import socket
import json
import operator
import sys
import binascii
import struct
import threading
import configparser


def SendInfo(socket, obj):
    for link in obj:
        if link != 'node':
            socket.sendto(bytes(json.dumps(obj),'utf8'),(obj[link]['ip'],int(config_dict[link]['port'])))
        

def UpdateRouteCost(obj, node, cost):
    for k in obj:
        if node == obj[k]['name']:
            obj[k]['cost'] = cost
        


def print_table(obj):
    print('>>>> ' + obj['node']['name'] + ' routing table <<<<')
    print('-------------------------------------------------------')
    print('|   destination   |    link cost    |    next hop     |')
    print('|    %-13s|    %-13s|    %-13s|' % (obj['link1']['name'],obj['link1']['cost'],obj['link1']['name']))
    print('|    %-13s|    %-13s|    %-13s|' % (obj['link2']['name'],obj['link2']['cost'],obj['link2']['name']))
    print('-------------------------------------------------------')

#def ReconstructRoutingTable(obj):
    

def listen_thread(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    while True:
        data, addr = s.recvfrom(1024)
        print(data)

def send(str,ip,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(bytes(str,'utf8'),(ip,port))

class RecvThread(threading.Thread):
    def __init__(self,port):
        super(RecvThread, self).__init__()
        self.port = port
        self.received_dict = None

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", self.port))
        while True:
            data, addr = s.recvfrom(1024)
            print("Recv: ")
            received_dict = json.loads(str(data,encoding='utf-8'))
            print_table(received_dict)
            #print_table(json.loads(str(data,encoding='utf-8')))
            print("Input command(FirstLoad, FirstSend, Bye, or MyRoutingTable):")

class MyParser(configparser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(d[k])
            d[k].pop('__name__', None)
        return d

if len(sys.argv) != 2:
    print("Useage: python " + sys.argv[0] + " <config file>")
    sys.exit(-1)

def load_ini(file):
    cf = MyParser()
    cf.read(file)
    return cf.as_dict()

config_dict = load_ini(sys.argv[1])
listen_port = int(config_dict['node']['port'])
#run recv thread
t = RecvThread(int(listen_port))
t.setDaemon(True)
t.start()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    print("Input command(FirstLoad, FirstSend, Bye, or MyRoutingTable):")
    text, *params = sys.stdin.readline().strip().split()
    if text == "FirstSend":
        SendInfo(s, config_dict)
        #send to link1
        #s.sendto(bytes(json.dumps(config_dict),'utf8'),(config_dict['link1']['ip'],int(config_dict['link1']['port'])))
        #send to link2
        #s.sendto(bytes(json.dumps(config_dict),'utf8'),(config_dict['link2']['ip'],int(config_dict['link2']['port'])))
        print("Send config finished")
    elif text == "FirstLoad":
        config_dict = load_ini(sys.argv[1])
        print("Load config file finished")
    elif text == "Bye":
        break
    elif text == "MyRoutingTable":
        print_table(config_dict)
    elif text == "UpdateRouteCosts":
        if len(params) != 2:
            print("Usage: UpdateRouteCost <node> <newcost>")
        else:
            node, newCost = params
            UpdateRouteCost(config_dict, node, newCost)
            
    else:
        print("Invalid command")
