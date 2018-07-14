import argparse
import logging
import socket

import config
import interface
import node
import scheduler

class Rift:

    def __init__(self):
        logging.basicConfig(
            filename = 'rift.log', 
            format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s', 
            level = logging.DEBUG)
        self._nodes = {}
        self.parse_command_line_arguments()
        self.parse_configuration()
        self.create_configuration()

    def parse_command_line_arguments(self):
        parser = argparse.ArgumentParser(description='Routing In Fat Trees (RIFT) protocol engine')
        parser.add_argument('configfile', nargs='?', default='', help='Configuration filename')
        self._args = parser.parse_args()
        return self._args

    def parse_configuration(self):
        self._config = config.parse_configuration(self._args.configfile)

    def create_configuration(self):
        if 'shards' in self._config:
            for shard_config in self._config['shards']:
                self.create_shard(shard_config)

    def create_shard(self, shard_config):
        if 'nodes' in shard_config:
            for node_config in shard_config['nodes']:
                self.create_node(node_config)

    def create_node(self, node_config):
        new_node = node.Node(node_config)
        self._nodes[new_node.name] = new_node

    def run(self):
        scheduler.scheduler.run() 

if __name__ == "__main__":
    rift = Rift()
    rift.run()