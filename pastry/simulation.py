from .node import Node
import random

# --- Educational Comments: The Simulation Environment ---
#
# This script creates a "centralized simulation" of a decentralized network.
# While this sounds like a contradiction, it's a powerful tool for learning.
#
# **Why Simulate This Way?**
# - **Global View:** The `PastryNetwork` class acts as an "oracle." It knows
#   about every node in the system, which allows us to do things that are
#   impossible in a real P2P network, like easily updating every node's
#   leaf set after a join.
# - **Clarity:** It separates the logic of the Pastry node (`node.py`) from
#   the logic of the network simulation. This makes the code cleaner and
#   easier to understand.
# - **Control:** We can orchestrate the simulation step-by-step: create the
#   network, add nodes one by one, trace their join paths, and then perform
#   `put` and `get` operations, observing the results at each stage.
#
# The goal is to clearly demonstrate the *algorithms* of Pastry without the
# complexities of real-world network programming (like handling sockets,
# timeouts, or packet loss).

class PastryNetwork:
    """
    Simulates the Pastry network, managing all nodes and facilitating
    communication. This class is a centralized helper for the simulation.
    """
    def __init__(self):
        """Initializes the network with an empty list of nodes."""
        self.nodes = []

    def add_node(self, node):
        """
        Adds a node to the network and keeps the list sorted by nodeId.
        This is a simulation convenience for easily calculating leaf sets.
        """
        self.nodes.append(node)
        self.nodes.sort(key=lambda n: n.node_id)

    def get_bootstrap_node(self):
        """
        Selects a random existing node to help a new node join the network.
        """
        return random.choice(self.nodes) if self.nodes else None

    def get_path(self, key, start_node):
        """
        Traces the complete routing path for a key, showing the step-by-step
        hops a message would take through the network.
        """
        path = [start_node]
        current_node = start_node

        while True:
            next_hop = current_node.route(key)
            if next_hop == current_node:
                # The path ends when a node routes to itself.
                break
            path.append(next_hop)
            current_node = next_hop

        return path

    def get_destination_node(self, key, start_node):
        """
        Finds the final destination node for a given key by routing.
        """
        path = self.get_path(key, start_node)
        return path[-1]

def run_simulation(num_nodes=20, num_items=5):
    """
    Runs a step-by-step simulation of the 16-bit Pastry network.
    """
    print("--- 16-Bit Pastry DHT Simulation ---")

    # --- Step 1: Create the network ---
    network = PastryNetwork()

    # --- Step 2: Add the first node ---
    # The first node has no others to connect to, so its tables are empty.
    print("\n1. Adding the first node...")
    first_node = Node()
    network.add_node(first_node)
    first_node.join(None, network)
    print(f"   - Added: {first_node}")

    # --- Step 3: Add the rest of the nodes ---
    # Each new node contacts a random "bootstrap" node to join.
    print("\n2. Adding subsequent nodes...")
    for i in range(num_nodes - 1):
        new_node = Node()
        bootstrap_node = network.get_bootstrap_node()
        print(f"\n   - Joining new node: {new_node} (using bootstrap: {bootstrap_node})")

        # The join process routes to find the new node's place and updates tables.
        new_node.join(bootstrap_node, network)

        # We can trace the path the "join" message took to see routing in action.
        print(f"     - Joined. Path to new node's ID was:")
        path = network.get_path(new_node.node_id, bootstrap_node)
        print("       -> " + " -> ".join(map(str, path)))


    print(f"\n--- Network of {len(network.nodes)} nodes created. ---")

    # --- Step 4: Store data in the DHT ---
    # Any node can initiate a `put` request. The network routes it to the correct node.
    print("\n3. Storing data in the DHT...")
    for i in range(num_items):
        key = f"data_item_{i}"
        value = f"some_value_{i}"
        start_node = network.get_bootstrap_node()
        print(f"\n   - Storing '{key}':'{value}' (initiated from {start_node})")
        start_node.put(key, value, network)

    # --- Step 5: Retrieve data from the DHT ---
    # Any node can also initiate a `get` request.
    print("\n4. Retrieving data from the DHT...")
    for i in range(num_items):
        key = f"data_item_{i}"
        start_node = network.get_bootstrap_node()
        print(f"\n   - Retrieving '{key}' (initiated from {start_node})")
        start_node.get(key, network)

if __name__ == "__main__":
    # To run the simulation, execute this file as a module from the parent directory:
    # python -m pastry.simulation
    run_simulation()