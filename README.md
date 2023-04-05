# DataCommsLab3

Issue with "Bad news travel slow"
* Check what happens after nodeC changes it path to nodeB to another node.
  The code checks if there is a loop by looking at the nextHop, but what happens after one of the nodes exits this loop? --> infinite loop
  
*Check involvement of the third node (nodeB), how it changes during the loop between nodeA and nodeC
