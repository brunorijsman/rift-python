import argparse
import logging
import socket

import config
import interface
import node
import scheduler

class Rift:

    _next_node_nr = 1

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
                node_nr = self._next_node_nr
                self._next_node_nr += 1
                if not 'name' in node_config:
                    node_config['name'] = socket.gethostname().split('.')[0] + str(node_nr)
                self.create_node(node_config)

    def create_node(self, node_config):
        name = node_config['name']
        self._nodes[name] = node.Node(node_config)

    def run(self):
        scheduler.scheduler.run() 

if __name__ == "__main__":
    rift = Rift()
    rift.run()