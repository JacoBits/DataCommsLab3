import socket
import json
import operator
import sys
import binascii
import struct
import threading
import configparser


def SendUpdate(socket, obj):
    for link in obj:
        if link != 'node':
            socket.sendto(bytes(json.dumps(obj),'utf8'),(obj[link]['ip'],int(config_dict[link]['port'])))
        

def UpdateRouteCost(obj, obj_links, direct, node, cost):
    if node in obj_links.keys():
        link = obj_links[node]
        obj[link]['cost'] = cost
        direct[node] = cost
        obj['node']['updated'] = True
    
def HandleMessage(neighbor, obj, object_links, direct_costs, socket):
    print_table(neighbor)
    ReconstructRoutingTable(obj, object_links, neighbor, direct_costs)
    if obj['node']['updated'] :
        SendUpdate(socket, obj)
        obj['node']['updated'] = False

'''def BellmanFord(current, self_to_neighbor, neighbor_to_node):
    return min(current, self_to_neighbor + neighbor_to_node)'''
    
def print_table(obj):
    print('>>>> ' + obj['node']['name'] + ' routing table <<<<')
    print('-------------------------------------------------------')
    print('|   destination   |    link cost    |    next hop     |')
    for link in obj:
        if link != 'node':
            print('|    %-13s|    %-13s|    %-13s|' % (obj[link]['name'],obj[link]['cost'],obj[link]['nextHop']))
    print('-------------------------------------------------------')


def ReconstructRoutingTable(obj, obj_links, neighbor, direct_costs):  
    obj['node']['updated'] = False
    
    neighbor_links = make_links_dict(neighbor)
    
    neighbor_name = neighbor['node']['name']
    neighbor_link = obj_links[neighbor_name]
    
    self_name = obj['node']['name']
    link_to_self = neighbor_links[self_name]
    
    if neighbor[link_to_self]['cost'] != obj[neighbor_link]['cost']:
            #print(f"Cost from {obj['node']['name']} to {neighbor_name} changed from {obj[neighbor_link]['cost']} to {neighbor[link_to_self]['cost']}")    
            for link in obj:
                '''if link != 'node' and obj[link]['nextHop'] == neighbor_name and obj[link]['name'] != neighbor_name:
                    difference = int(neighbor[link_to_self]['cost']) - int(obj[neighbor_link]['cost'])
                    cost_to_link = int(obj[link]['cost']) + difference
                    obj[link]['cost'] = cost_to_link'''
            obj[neighbor_link]['cost'] = neighbor[link_to_self]['cost']
            direct_costs[neighbor_name] = neighbor[link_to_self]['cost']
            obj['node']['updated'] = True
            #SendInfo(s, obj)
    
    #link_text = 'link'
    #counter = len(obj)
    for n in neighbor:
        target_name = neighbor[n]['name']
        if neighbor[n]['name'] not in obj_links.keys():
            link_text += str(counter)
            counter += 1
            obj[link_text]['name'] = neighbor[n]['name']
            obj[link_text]['cost'] = int(neighbor[n]['cost']) + int(direct_costs[neighbor_name])
        else:
            #OB: fixed indentation
            if target_name != self_name and n != 'node':
                target_link = obj_links[target_name]
                neighbor_to_target = int(neighbor[n]['cost'])
                node_to_neighbor = int(direct_costs[neighbor_name])
                if obj[target_link]['nextHop'] == neighbor_name and int(neighbor[target_link]['cost']) + node_to_neighbor  > int(obj[target_link]['cost']):
                    obj_to_node = int(obj[target_link]['cost'])
                    obj_to_node += node_to_neighbor
                    obj[target_link]['cost'] = obj_to_node
                    if int(obj[target_link]['cost']) > int(direct_costs[target_name]):
                        obj[target_link]['cost'] = direct_costs[target_name]
                        obj[target_link]['nextHop'] = target_name
                        obj['node']['updated'] = True
                        
            else:
                #print(f"From {neighbor['node']['name']} to {node_name}, cost {neighbor_to_node}")
                #print(f"Current cost to {node_name}: {obj[node_link]['cost']}")
                #print(f"Current cost to {neighbor_name}: {int(obj[neighbor_link]['cost'])}")
                #print(f"From {obj['node']['name']} to {neighbor['node']['name']} to {node_name}, cost = {neighbor_to_node + int(obj[neighbor_link]['cost'])}")
                #obj_to_node = BellmanFord(int(obj[node_link]['cost']), neighbor_to_node, int(obj[neighbor_link]['cost']))
                obj_to_node = min(int(obj[target_link]['cost']), neighbor_to_target + node_to_neighbor)
                #print(f"Bellman-ford equation result: {obj_to_node}")
                if obj_to_node != int(obj[target_link]['cost']):
                    obj[target_link]['cost'] = obj_to_node
                    obj[target_link]['nextHop'] = neighbor_name
                    obj['node']['updated'] = True
                    #print_table(obj)
                

                
def make_links_dict(obj):
    links_dict = {obj[key]['name']: key for key in obj if 'cost' in obj[key]}
    return links_dict

def make_direct_costs_dict(obj):
    direct_costs = {obj[key]['name']: int(obj[key]['cost']) for key in obj if 'cost' in obj[key]}
    return direct_costs

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
 

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", self.port))
        while True:
            data, addr = s.recvfrom(1024)
            print("Recv: ")
            received_dict = json.loads(str(data,encoding='utf-8'))
            HandleMessage(received_dict, config_dict, config_links, direct_costs, s)
            #print_table(json.loads(str(data,encoding='utf-8')))
            print("Input command(FirstLoad, FirstSend, MyRoutingTable, UpdateRouteCosts <node> <cost>, Bye):")
            


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
    print("Input command(FirstLoad, FirstSend, MyRoutingTable, UpdateRouteCosts <node> <cost>, Bye):")
    text, *params = sys.stdin.readline().strip().split()
    if text == "FirstSend":
        SendUpdate(s, config_dict)
        #send to link1
        #s.sendto(bytes(json.dumps(config_dict),'utf8'),(config_dict['link1']['ip'],int(config_dict['link1']['port'])))
        #send to link2
        #s.sendto(bytes(json.dumps(config_dict),'utf8'),(config_dict['link2']['ip'],int(config_dict['link2']['port'])))
        print("Send config finished")
    elif text == "FirstLoad":
        config_dict = load_ini(sys.argv[1])
        config_dict['node']['updated'] = False
        for n in config_dict:
            if n != 'node':
                config_dict[n]['nextHop'] = config_dict[n]['name']
        print("Load config file finished")
        config_links = make_links_dict(config_dict)
        direct_costs = make_direct_costs_dict(config_dict)
    elif text == "Bye":
        break
    elif text == "MyRoutingTable":
        print_table(config_dict)
    elif text == "UpdateRouteCosts":
        if len(params) != 2:
            print("Usage: UpdateRouteCost <node> <newcost>")
        else:
            node, newCost = params
            UpdateRouteCost(config_dict, config_links, direct_costs, node, newCost)
            print_table(config_dict)
            SendUpdate(s, config_dict)
            config_dict['node']['updated'] = False
            
            
            
            
    else:
        print("Invalid command")
