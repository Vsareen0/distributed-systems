import hashlib
import random

# --- Educational Comments: A Simplified 16-Bit Pastry DHT ---
#
# Welcome to this educational implementation of the Pastry DHT!
#
# **What is Pastry?**
# Pastry is a structured peer-to-peer overlay network that provides a Distributed
# Hash Table (DHT). In simple terms, it's a way for a group of computers to
# self-organize and create a massive, fault-tolerant dictionary where you can
# store and retrieve data using keys.
#
# **Why 16-Bit?**
# A real-world Pastry network uses 128-bit identifiers, which are enormous numbers.
# To make the core concepts easier to grasp, this implementation uses a tiny
# 16-bit ID space (from 0 to 65535, or 0x0000 to 0xffff in hex).
#
# This simplification has several advantages for learning:
# - **Readable IDs:** Node IDs are short and easy to compare (e.g., 'a1b2').
# - **Small Routing Tables:** The main data structure for routing is a small 4x16 table,
#   which is easy to visualize.
# - **Understandable Hashing:** We can see how any piece of data (like a filename)
#   is hashed into a 16-bit key that fits within our small network.
#
# **Key Concepts in this File:**
# 1.  **Node ID:** A random 16-bit number assigned to each node.
# 2.  **Key:** A 16-bit hash of a piece of data.
# 3.  **Routing:** The process of finding the node with an ID "numerically closest"
#     to a given key. Pastry does this in very few hops (O(log N) time).
# 4.  **Routing Table:** A table that helps make large jumps across the network
#     by matching prefixes of the key.
# 5.  **Leaf Set:** A set of nodes with the numerically closest IDs. This ensures
#     routing accuracy and network resilience.

class Node:
    """
    Represents a node in a 16-bit Pastry DHT network.
    """
    def __init__(self, node_id=None):
        """
        Initializes a new Node with a 16-bit ID.
        """
        if node_id is None:
            self.node_id = random.getrandbits(16)
        else:
            self.node_id = node_id

        # Routing table size is 4x16 for a 16-bit (4-digit hex) ID space.
        self.routing_table = [[None for _ in range(16)] for _ in range(4)]

        # Leaf set stores numerically close nodes.
        self.leaf_set = []

        # Local data store for key-value pairs.
        self.data_store = {}

    def __repr__(self):
        """Provides a readable 4-digit hex representation of the node ID."""
        return f"Node({self.node_id:04x})"

    @staticmethod
    def generate_node_id(key):
        """
        Generates a 16-bit ID from a key using SHA-1 and truncation.
        """
        sha1 = hashlib.sha1()
        sha1.update(str(key).encode('utf-8'))
        # Truncate hash to 4 hex digits (16 bits).
        return int(sha1.hexdigest()[:4], 16)

    @staticmethod
    def get_digit(number, position):
        """
        Gets the hex digit at a specific position (0-3) from a 16-bit number.
        """
        hex_str = f"{number:04x}"
        if 0 <= position < 4:
            return int(hex_str[position], 16)
        return None

    @staticmethod
    def common_prefix_length(id1, id2):
        """
        Calculates the length of the common prefix in hex digits for two 16-bit IDs.
        """
        hex_id1 = f"{id1:04x}"
        hex_id2 = f"{id2:04x}"
        length = 0
        while length < 4 and hex_id1[length] == hex_id2[length]:
            length += 1
        return length

    def route(self, key):
        """
        Routes a message towards the node responsible for the given 16-bit key.
        """
        # Step 1: Check if the key is in our leaf set's range.
        if self.leaf_set:
            min_leaf = min(n.node_id for n in self.leaf_set)
            max_leaf = max(n.node_id for n in self.leaf_set)
            if min_leaf <= key <= max_leaf:
                closest_node = min(self.leaf_set, key=lambda n: abs(n.node_id - key))
                if abs(self.node_id - key) < abs(closest_node.node_id - key):
                    return self
                return closest_node

        # Step 2: Use the routing table.
        prefix_len = self.common_prefix_length(self.node_id, key)
        if prefix_len == 4: # Key matches this node's ID
            return self

        next_digit = self.get_digit(key, prefix_len)
        if next_digit is not None and self.routing_table[prefix_len][next_digit] is not None:
            return self.routing_table[prefix_len][next_digit]

        # Step 3: Fallback routing (search all known nodes).
        all_known_nodes = [node for row in self.routing_table for node in row if node is not None] + self.leaf_set

        better_prefix_nodes = [
            node for node in all_known_nodes
            if self.common_prefix_length(node.node_id, key) >= prefix_len
        ]

        if better_prefix_nodes:
            closest_node = min(better_prefix_nodes, key=lambda n: abs(n.node_id - key))
        elif all_known_nodes:
            closest_node = min(all_known_nodes, key=lambda n: abs(n.node_id - key))
        else:
            return self # No other nodes known

        if abs(self.node_id - key) < abs(closest_node.node_id - key):
            return self

        return closest_node

    def join(self, bootstrap_node, network):
        """
        Joins the Pastry network using a bootstrap node.
        """
        if bootstrap_node is None:
            # This is the first node, nothing to do.
            return

        # Route to find the node closest to our ID.
        closest_node = network.get_destination_node(self.node_id, bootstrap_node)

        # Copy state from the closest node (simplified for simulation).
        self.leaf_set = closest_node.leaf_set[:]
        for i in range(4):
            for j in range(16):
                self.routing_table[i][j] = closest_node.routing_table[i][j]

        # Add self to the network and update all other nodes.
        network.add_node(self)
        for node in network.nodes:
            node.update_routing_table(self)
            node.update_leaf_set(network.nodes)

    def update_routing_table(self, new_node):
        """
        Updates the routing table with a new node if it's a better fit.
        """
        prefix_len = self.common_prefix_length(self.node_id, new_node.node_id)
        digit = self.get_digit(new_node.node_id, prefix_len)

        if digit is not None:
            current_entry = self.routing_table[prefix_len][digit]
            if current_entry is None or abs(new_node.node_id - self.node_id) < abs(current_entry.node_id - self.node_id):
                self.routing_table[prefix_len][digit] = new_node

    def update_leaf_set(self, all_nodes, leaf_set_size=4):
        """
        Updates the leaf set from a global list of nodes (for simulation).
        A smaller leaf set size is suitable for a smaller network.
        """
        sorted_nodes = sorted(all_nodes, key=lambda n: n.node_id)

        try:
            my_index = sorted_nodes.index(self)
        except ValueError:
            return

        num_nodes = len(sorted_nodes)
        predecessors = []
        successors = []

        # Get L/2 predecessors and L/2 successors.
        for i in range(1, leaf_set_size // 2 + 1):
            predecessors.append(sorted_nodes[(my_index - i + num_nodes) % num_nodes])

        for i in range(1, leaf_set_size // 2 + 1):
            successors.append(sorted_nodes[(my_index + i) % num_nodes])

        self.leaf_set = list(dict.fromkeys(predecessors + successors))
        self.leaf_set.sort(key=lambda n: n.node_id)

    def put(self, key, value, network):
        """
        Stores a key-value pair in the DHT.
        """
        data_key = self.generate_node_id(key)
        destination_node = network.get_destination_node(data_key, self)
        destination_node.data_store[key] = value
        print(f"Stored '{key}' at {destination_node}")

    def get(self, key, network):
        """
        Retrieves a value from the DHT by its key.
        """
        data_key = self.generate_node_id(key)
        destination_node = network.get_destination_node(data_key, self)
        value = destination_node.data_store.get(key)

        if value is not None:
            print(f"Found '{key}' at {destination_node}: {value}")
        else:
            print(f"Could not find '{key}' in the network.")
        return value