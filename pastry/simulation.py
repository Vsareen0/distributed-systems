from .node import Node
import random

# --- Educational Comments: Simulation Purpose ---
#
# This script simulates the behavior of a Pastry DHT. Unlike a real-world,
# decentralized network, this simulation is "centralized." It uses a single
# `PastryNetwork` object to manage all nodes and their interactions. This
# approach has several benefits for learning:
#
# 1.  **Global View:** We can easily see the entire state of the network,
#     including all nodes and their routing tables, which is impossible in a
#     real distributed system.
#
# 2.  **Simplified State Management:** In a real network, nodes must discover
#     each other and exchange state through complex protocols. Here, we can
#     simplify processes like updating leaf sets by giving nodes a direct reference
#     to the global list of all nodes.
#
# 3.  **Controlled Environment:** We can deterministically add nodes, store data,
#     and trace routing paths to observe exactly how the Pastry algorithm works
#     step-by-step.
#
# The goal is not to build a production-ready DHT, but to provide a clear,
# understandable model of how Pastry operates.

class PastryNetwork:
    """
    Simulates the Pastry network, managing all nodes and facilitating
    communication between them. This class acts as a centralized "god object"
    for the simulation, which would not exist in a real P2P network.
    """
    def __init__(self):
        """Initializes the network with an empty list of nodes."""
        self.nodes = []

    def add_node(self, node):
        """
        Adds a node to the network and keeps the list sorted by nodeId. This
        is a simulation convenience to easily find neighbors.
        """
        self.nodes.append(node)
        self.nodes.sort(key=lambda n: n.node_id)

    def get_bootstrap_node(self):
        """
        Selects a random node from the network to act as a "bootstrap" node
        for a new node that wants to join.
        """
        return random.choice(self.nodes) if self.nodes else None

    def get_path(self, key, start_node):
        """
        Traces the complete routing path for a key from a starting node.
        This demonstrates the step-by-step process of Pastry routing.

        Returns:
            list[Node]: A list of nodes representing the hops taken.
        """
        path = [start_node]
        current_node = start_node

        while True:
            next_hop = current_node.route(key)
            if next_hop == current_node:
                # The current node believes it is the destination.
                break
            path.append(next_hop)
            current_node = next_hop

        return path

    def get_destination_node(self, key, start_node):
        """
        Finds the final destination node for a given key by tracing the path.
        """
        path = self.get_path(key, start_node)
        return path[-1]

def run_simulation(num_nodes=20, num_items=5):
    """
    Runs a step-by-step simulation of the Pastry network.

    The simulation demonstrates:
    1.  Network formation (nodes joining one by one).
    2.  DHT `put` operations (storing data).
    3.  DHT `get` operations (retrieving data).
    """
    print("--- Pastry DHT Simulation ---")

    # --- Step 1: Create the network object ---
    network = PastryNetwork()

    # --- Step 2: Add the first node ---
    # The first node in the network has no other nodes to connect to. It becomes
    # the initial bootstrap node for all subsequent nodes.
    print("\n1. Adding the first node...")
    first_node = Node()
    network.add_node(first_node)
    first_node.join(None, network) # The 'join' is trivial for the first node.
    print(f"   - Added: {first_node}")

    # --- Step 3: Add subsequent nodes ---
    # Each new node joins by contacting a random existing node (the bootstrap node).
    # It then routes a "join" request to find its correct place in the network.
    print("\n2. Adding subsequent nodes...")
    for i in range(num_nodes - 1):
        new_node = Node()
        bootstrap_node = network.get_bootstrap_node()
        print(f"\n   - Joining new node: {new_node}")
        print(f"     - Using bootstrap: {bootstrap_node}")

        # The join process updates the new node's state and notifies others.
        new_node.join(bootstrap_node, network)

        # We can trace the path the "join" message took.
        print(f"     - Joined. Path to new node's ID was:")
        path = network.get_path(new_node.node_id, bootstrap_node)
        for hop in path:
            print(f"       -> {hop}")

    print(f"\n--- Network of {len(network.nodes)} nodes created. ---")

    # --- Step 4: Store data in the DHT ---
    # To store data, any node can initiate a `put` request. The network will
    # automatically route the request to the correct node responsible for the data's key.
    print("\n3. Storing data in the DHT...")
    for i in range(num_items):
        key = f"item_{i}"
        value = f"value_for_item_{i}"

        # Pick a random node to start the `put` operation.
        start_node = network.get_bootstrap_node()

        print(f"\n   - Storing '{key}': '{value}' (initiated from {start_node})")
        start_node.put(key, value, network)

    # --- Step 5: Retrieve data from the DHT ---
    # Similarly, any node can retrieve data. It sends a `get` request, and Pastry
    # routes it to the node that stores the data.
    print("\n4. Retrieving data from the DHT...")
    for i in range(num_items):
        key = f"item_{i}"

        # Pick a random node to start the `get` operation.
        start_node = network.get_bootstrap_node()

        print(f"\n   - Retrieving '{key}' (initiated from {start_node})")
        start_node.get(key, network)

if __name__ == "__main__":
    # To run the simulation, execute this file as a module:
    # python -m pastry.simulation
    run_simulation()