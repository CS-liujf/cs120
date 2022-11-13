from phy_layer import *

node1 = MAC(NodeType.TRANSMITTER)
node1.start()

stream = init_stream()
stream.start()

