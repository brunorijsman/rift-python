import enum
import logging
import socket

import interface
import node
import scheduler

class Rift:

    class ActiveNodes(enum.Enum):
        ALL_NODES = 1
        ONLY_PASSIVE_NODES = 2
        ALL_NODES_EXCEPT_PASSIVE_NODES = 3

    def __init__(self, active_nodes, config):
        logging.basicConfig(
            filename = 'rift.log', 
            format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s', 
            level = logging.DEBUG)
        self._active_nodes = active_nodes
        self._config = config
        self._nodes = {}
        self.create_configuration()

    def create_configuration(self):
        if 'shards' in self._config:
            for shard_config in self._config['shards']:
                self.create_shard(shard_config)

    def create_shard(self, shard_config):
        if 'nodes' in shard_config:
            for node_config in shard_config['nodes']:
                self.create_node(node_config)

    def create_node(self, node_config):
        new_node = node.Node(self, node_config)
        self._nodes[new_node.name] = new_node

    def run(self):
        scheduler.scheduler.run() 

    @property
    def active_nodes(self):
        return self._active_nodes

# TODO: Remove this once every existing user knows they are supposed to run main.py

if __name__ == "__main__":

    print("SORRY! I changed the code. Run main.py instead of rift.py")