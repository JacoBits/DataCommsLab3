import socket
import json
import operator
import sys
import binascii
import struct
import threading
import configparser

# This function sends an update to a neighbor node.
# The update is a JSON object that contains information about the entire network topology.
def SendUpdate(socket, obj):
    for link in obj:
        if 'port' in obj[link] and link != 'node':
            # Send the update to the neighbor node's IP address and port number.
            socket.sendto(bytes(json.dumps(obj),'utf8'),(obj[link]['ip'],int(config_dict[link]['port'])))
  
# This function updates the cost of a link between two nodes in the network.
def UpdateRouteCost(obj, direct, node, cost):
    # Create a dictionary that maps link names to their corresponding dictionary objects.
    obj_links = make_links_dict(obj)
    if node in obj_links.keys():
        # Get the name of the link that connects the current node to the given neighbor node.
        link = obj_links[node]
        # Update the cost of the link and the direct cost of the neighbor node.
        obj[link]['cost'] = cost
        direct[node] = cost
        # Set the 'updated' flag in the network topology object to True.
        obj['node']['updated'] = True
    
# This function handles an incoming message from a neighbor node.
def HandleMessage(neighbor, obj, socket):
    # Print the routing table for the neighbor node.
    print_table(neighbor)
    # Reconstruct the routing table for the entire network based on the new information.
    ReconstructRoutingTable(obj, neighbor, direct_costs)
    if obj['node']['updated']:
        # If the routing table was updated, send an update to all neighbor nodes.
        SendUpdate(socket, obj)
        obj['node']['updated'] = False
    
# This function prints a routing table for a given node in the network.
def print_table(obj):
    print('>>>> ' + obj['node']['name'] + ' routing table <<<<')
    print('-------------------------------------------------------')
    print('|   destination   |    link cost    |    next hop     |')
    for link in obj:
        if link != 'node':
            print('|    %-13s|    %-13s|    %-13s|' % (obj[link]['name'],obj[link]['cost'],obj[link]['nextHop']))
    print('-------------------------------------------------------')

# This function reconstructs the routing table for the entire network based on new information from a neighbor node.
def ReconstructRoutingTable(obj, neighbor, direct_costs):  
    # Set the 'updated' flag in the network topology object to False.
    obj['node']['updated'] = False
    
    # Create dictionaries that map link names to their corresponding dictionary objects for the current node and the neighbor node.
    obj_links = make_links_dict(obj)
    neighbor_links = make_links_dict(neighbor)
    
    # Get the name of the neighbor node and the name of the link that connects the current node to the neighbor node.
    neighbor_name = neighbor['node']['name']
    neighbor_link = obj_links[neighbor_name]
    
    # Get the name of the current node and the name of the link that connects the neighbor node to the current node.
    self_name = obj['node']['name']
    link_to_self = neighbor_links[self_name]
    
    if neighbor[link_to_self]['cost'] != obj[neighbor_link]['cost']:
        # If the cost of the link between the current node and the neighbor node has changed, update the cost in the network topology object.
        # Our cost to the neighbor is now the neighbor's link to us
        obj[neighbor_link]['cost'] = neighbor[link_to_self]['cost']
        direct_costs[neighbor_name] = neighbor[link_to_self]['cost']
        # Set the updated flag to true
        obj['node']['updated'] = True

    #loop through neighbor table
    for n in neighbor:
        # Our target is the neighbor's neighbor
        target_name = neighbor[n]['name']
        # If the neighbor's neighbor is not the current node and the neighbor's neighbor is not already in the current node's routing table, add it.
        if neighbor[n]['name'] not in obj_links.keys() and neighbor[n]['name'] != self_name:
            # Counter variable to add new link to current node's dict
            counter = len(obj)
            link_text = 'link' + str(counter)
            obj[link_text] = {'namme': neighbor[n]['name']}
            #the new cost is the neighbor's cost to the neighbor's neighbor plus the neighbor's cost to us
            obj[link_text]['cost'] = int(neighbor[n]['cost']) + int(direct_costs[neighbor_name])
            #update next hop in the current node's routing table
            obj[link_text]['nextHop'] = neighbor_name

        # If the link in the neighbor's table is not us and the link is not the current neighbor we received from
        elif target_name != self_name and n != 'node':
            # The target link is the link between the neighbor node, and the other node that is not the current node
            target_link = obj_links[target_name]
            #  Storing neighbors best cost to target 
            neighbor_to_target = int(neighbor[n]['cost'])
            # Storing our best cost to target
            node_to_neighbor = int(direct_costs[neighbor_name])
            # if the next hop is our neighbor and our link + the neighbor's best distance to the target node is greater than our current cost to tartget
            if obj[target_link]['nextHop'] == neighbor_name and int(neighbor[target_link]['cost']) + node_to_neighbor > int(obj[target_link]['cost']):
                    #update our cost to the node as the current link plus neighbor's link
                    obj[target_link]['cost'] = int(neighbor[target_link]['cost']) + node_to_neighbor

                    if target_name in direct_costs and int(obj[target_link]['cost']) > int(direct_costs[target_name]):
                            obj[target_link]['cost'] = direct_costs[target_name]
                            obj[target_link]['nextHop'] = target_name 
                    else:
                           obj[target_link]['cost'] = int(neighbor[target_link]['cost']) + node_to_neighbor
                    obj['node']['updated'] = True
            else:
                #our cost to the node is the minimum between our current best distance, or our current link plus their best distance
                obj_to_node = min(int(obj[target_link]['cost']), neighbor_to_target + node_to_neighbor)

                #ensuring that the costs and nexthop match up
                if obj_to_node != int(obj[target_link]['cost']):
                    obj[target_link]['cost'] = obj_to_node
                    obj[target_link]['nextHop'] = neighbor_name
                    #updated flag 
                    obj['node']['updated'] = True                

#takes in config dict as obj. Maps names and their cost in a non nested dict
def make_links_dict(obj):
    links_dict = {obj[key]['name']: key for key in obj if 'cost' in obj[key]}
    return links_dict

#makes a dict of a node's direct liknks
def make_direct_costs_dict(obj):
    direct_costs = {obj[key]['name']: int(obj[key]['cost']) for key in obj if 'cost' in obj[key]}
    return direct_costs

#UDP socket to run in background, prints data when received
def listen_thread(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    while True:
        data, addr = s.recvfrom(1024)
        print(data)

#function to send some data to a port at an ip
def send(str,ip,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(bytes(str,'utf8'),(ip,port))

#background process running separately, ensures data is always received
class RecvThread(threading.Thread):
    def __init__(self,port):
        super(RecvThread, self).__init__()
        self.port = port

    #main loop after program runs
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", self.port))
        while True:
            data, addr = s.recvfrom(1024)
            print("Recv: ")
            received_dict = json.loads(str(data,encoding='utf-8'))

            #function to rebuild and resend a routing table
            HandleMessage(received_dict, config_dict, s)
            print("Input command(FirstLoad, FirstSend, MyRoutingTable, UpdateRouteCosts <node> <cost>, Bye):")

#class to parse .ini files, returns a nested dictionary 
class MyParser(configparser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(d[k])
            d[k].pop('__name__', None)
        return d

#exception if program is not initialized correctly 
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

#Main socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    print("Input command(FirstLoad, FirstSend, MyRoutingTable, UpdateRouteCosts <node> <cost>, Bye):")
    text, *params = sys.stdin.readline().strip().split()
    if text == "FirstSend":
        SendUpdate(s, config_dict)
        print("Send config finished")
    elif text == "FirstLoad":
        config_dict = load_ini(sys.argv[1])
        #Sets the updated flag to false at the outset. 
        config_dict['node']['updated'] = False

        #looping through keys in config dict (node, link1, link2, updated)
        for n in config_dict:
            #if the key is a link
            if n != 'node':
                #set the next hop as the name of the link
                config_dict[n]['nextHop'] = config_dict[n]['name']
        print("Load config file finished")
        #dictionary for easy access to a node's links
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
            UpdateRouteCost(config_dict, direct_costs, node, newCost)
            print_table(config_dict)
            SendUpdate(s, config_dict)
            #manually set flag to false after each send 
            config_dict['node']['updated'] = False         
    else:
        print("Invalid command")
