import hashlib
import random

# --- Educational Comments: Pastry DHT Concepts ---
#
# Pastry is a peer-to-peer (P2P) structured overlay network, which provides a
# Distributed Hash Table (DHT). Here are the key concepts:
#
# 1.  **Node ID Space:** Each node in the network is assigned a unique 128-bit
#     `nodeId`. This ID determines the node's position in a circular ID space
#     (from 0 to 2^128 - 1).
#
# 2.  **Keys:** Every piece of data stored in the DHT is associated with a key,
#     which is also a 128-bit value. Pastry maps keys to nodes based on
#     "numerical closeness." The node with the `nodeId` numerically closest to
#     the key is responsible for storing that data.
#
# 3.  **Routing:** Pastry's core function is to efficiently route messages from
#     any node to the node responsible for a given key. It does this in
#     O(log N) steps, where N is the number of nodes in the network.
#
# 4.  **State Tables:** To achieve efficient routing, each node maintains two
#     key data structures:
#     -   **Routing Table:** Organizes known nodes by the length of their shared
#         prefix with the current node's ID. This allows for quickly "homing in"
#         on a destination by matching prefixes.
#     -   **Leaf Set:** Contains the nodes with the numerically closest `nodeId`s
#         (both smaller and larger). This ensures reliable routing, especially
#         for messages destined for nearby nodes.
#
# This implementation uses a base-16 (hexadecimal) representation for node IDs,
# where each digit is 4 bits. A 128-bit ID thus has 32 hexadecimal digits.

class Node:
    """
    Represents a node in the Pastry DHT network. Each node has a unique ID,
    a routing table, a leaf set, and a local data store.
    """
    def __init__(self, node_id=None):
        """
        Initializes a new Node.

        Args:
            node_id (int, optional): The 128-bit node ID. If None, a random ID
                                     is generated, simulating a new node joining
                                     the network.
        """
        if node_id is None:
            # In a real network, a new node would generate its ID randomly.
            self.node_id = random.getrandbits(128)
        else:
            self.node_id = node_id

        # The routing table is a key component for efficient message routing.
        # It's a 2D array where:
        # - Rows correspond to the length of the common prefix with our node ID.
        #   For a 128-bit ID (32 hex digits), there are 32 rows (0-31).
        # - Columns correspond to the value of the next digit (0-15 for hex).
        # Each entry stores a `Node` object that matches this profile.
        # Example: routing_table[3][A] would be a node whose ID shares the
        # first 3 digits with ours, and whose 4th digit is 'A'.
        self.routing_table = [[None for _ in range(16)] for _ in range(32)]

        # The leaf set ensures reliable routing by keeping track of our direct
        # neighbors in the circular ID space. It contains a small number of
        # nodes with IDs numerically smaller and larger than our own.
        self.leaf_set = []

        # Each node in the DHT is responsible for storing a portion of the
        # network's data. This dictionary simulates that local storage.
        self.data_store = {}

    def __repr__(self):
        """Provides a readable representation of the node, showing its ID in hex."""
        return f"Node({self.node_id:032x})"

    @staticmethod
    def generate_node_id(key):
        """
        Generates a 128-bit ID from a given key (e.g., a filename or string)
        using a hash function (SHA-1). This ensures that data keys are mapped
        to the same ID space as node IDs.
        """
        sha1 = hashlib.sha1()
        sha1.update(str(key).encode('utf-8'))
        # We use the first 32 hex characters of the hash for our 128-bit ID.
        return int(sha1.hexdigest()[:32], 16)

    @staticmethod
    def get_digit(number, position, base=16):
        """
        A helper function to extract a specific hexadecimal digit from a 128-bit
        number. Position 0 is the most significant digit.
        """
        hex_str = f"{number:032x}"
        if 0 <= position < 32:
            return int(hex_str[position], 16)
        return None

    @staticmethod
    def common_prefix_length(id1, id2):
        """
        Calculates the length of the common prefix (in hex digits) between two IDs.
        This is fundamental for routing table-based decisions.
        """
        hex_id1 = f"{id1:032x}"
        hex_id2 = f"{id2:032x}"
        length = 0
        while length < 32 and hex_id1[length] == hex_id2[length]:
            length += 1
        return length

    def route(self, key):
        """
        Routes a message towards the node responsible for the given key. This
        method implements the core Pastry routing algorithm.

        The algorithm proceeds in three steps:
        1. Check the leaf set.
        2. Use the routing table.
        3. Fallback to a more general search if the first two fail.

        Args:
            key (int): The 128-bit key to route to.

        Returns:
            Node: The next hop node in the path to the key's destination.
        """
        # --- Step 1: Check the Leaf Set ---
        # The leaf set is ideal for short-range routing. If the key falls
        # within the ID range of our leaf set, we can forward the message
        # to the leaf node with the ID closest to the key.
        if self.leaf_set:
            min_leaf = min(n.node_id for n in self.leaf_set)
            max_leaf = max(n.node_id for n in self.leaf_set)
            if min_leaf <= key <= max_leaf:
                closest_node = min(self.leaf_set, key=lambda n: abs(n.node_id - key))
                # If this node is numerically closer, we are the destination.
                if abs(self.node_id - key) < abs(closest_node.node_id - key):
                    return self
                return closest_node

        # --- Step 2: Use the Routing Table ---
        # The routing table enables long-range routing by jumping across the
        # network, progressively matching more of the key's prefix.
        prefix_len = self.common_prefix_length(self.node_id, key)

        # If the key is identical to our ID, we are the destination.
        if prefix_len == 32:
            return self

        # Get the next digit of the key that differs from our ID.
        next_digit = self.get_digit(key, prefix_len)

        # Look up the appropriate entry in our routing table.
        if next_digit is not None and self.routing_table[prefix_len][next_digit] is not None:
            # We found a node that shares a longer prefix with the key.
            return self.routing_table[prefix_len][next_digit]

        # --- Step 3: Fallback Routing (Rare Case) ---
        # If neither the leaf set nor the routing table provides a better next
        # hop, we perform a more general search. This handles cases where our
        # tables are not perfectly up-to-date. We look for any known node
        # that shares a prefix with the key at least as long as ours and is
        # numerically closer.
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
            # If we don't know any other nodes, we must be the destination.
            return self

        # If we are closer than the best node we found, we are the destination.
        if abs(self.node_id - key) < abs(closest_node.node_id - key):
            return self

        return closest_node

    def join(self, bootstrap_node, network):
        """
        Handles a new node joining the Pastry network.

        The process involves:
        1. Routing a "join" request to the node with an ID closest to our own.
        2. Receiving state information (leaf set, routing table) from this node.
        3. Announcing our presence to the network so other nodes can update their tables.

        Args:
            bootstrap_node (Node): An existing node to start the join process.
            network (PastryNetwork): The simulation object to access all nodes.
        """
        if bootstrap_node is None:
            # This is the first node, so it has no one to join.
            return

        # Route a message with our own ID as the key. This will find the node
        # currently responsible for our ID.
        path = network.get_path(self.node_id, bootstrap_node)
        closest_node = path[-1]

        # In a real system, this would involve a multi-step state exchange.
        # For this simulation, we simplify by copying state from the closest node.
        self.leaf_set = closest_node.leaf_set[:]

        # Copy the routing table, which serves as a good starting point.
        for i in range(32):
            for j in range(16):
                self.routing_table[i][j] = closest_node.routing_table[i][j]

        # Add ourself to the network.
        network.add_node(self)

        # Announce our arrival to all other nodes so they can update their state.
        for node in network.nodes:
            node.update_routing_table(self)
            node.update_leaf_set(network.nodes)

    def update_routing_table(self, new_node):
        """
        Updates the routing table when a new node joins the network.
        """
        prefix_len = self.common_prefix_length(self.node_id, new_node.node_id)
        digit = self.get_digit(new_node.node_id, prefix_len)

        if digit is not None:
            # Check if the new node is a better fit for this routing table entry.
            current_entry = self.routing_table[prefix_len][digit]
            if current_entry is None or abs(new_node.node_id - self.node_id) < abs(current_entry.node_id - self.node_id):
                self.routing_table[prefix_len][digit] = new_node

    def update_leaf_set(self, all_nodes, leaf_set_size=8):
        """
        Updates the leaf set based on the current list of all nodes.
        In a real network, this would be done via gossip or other P2P protocols.
        For this simulation, we simplify by using a global view of the network.
        """
        sorted_nodes = sorted(all_nodes, key=lambda n: n.node_id)

        try:
            my_index = sorted_nodes.index(self)
        except ValueError:
            return

        num_nodes = len(sorted_nodes)
        predecessors = []
        successors = []

        # Find L/2 predecessors and L/2 successors in the sorted list.
        for i in range(1, leaf_set_size // 2 + 1):
            predecessors.append(sorted_nodes[(my_index - i + num_nodes) % num_nodes])

        for i in range(1, leaf_set_size // 2 + 1):
            successors.append(sorted_nodes[(my_index + i) % num_nodes])

        self.leaf_set = list(dict.fromkeys(predecessors + successors))
        self.leaf_set.sort(key=lambda n: n.node_id)

    def put(self, key, value, network):
        """
        Stores a key-value pair in the DHT. This is the "write" operation.
        """
        # First, hash the user-friendly key (e.g., "my_document") to get a
        # 128-bit data key that fits into the Pastry ID space.
        data_key = self.generate_node_id(key)

        # Route a message to find the node responsible for this data key.
        destination_node = network.get_destination_node(data_key, self)

        # Store the actual key-value pair on that destination node.
        destination_node.data_store[key] = value
        print(f"Stored '{key}' at {destination_node}")

    def get(self, key, network):
        """
        Retrieves a value from the DHT. This is the "read" operation.
        """
        # Hash the key to find where the data *should* be stored.
        data_key = self.generate_node_id(key)

        # Route to the responsible node.
        destination_node = network.get_destination_node(data_key, self)

        # Attempt to retrieve the data from that node's local store.
        value = destination_node.data_store.get(key)

        if value is not None:
            print(f"Found '{key}' at {destination_node}: {value}")
        else:
            print(f"Could not find '{key}' in the network.")

        return value