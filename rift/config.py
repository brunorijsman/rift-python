import ipaddress
import pprint
import sys

import cerberus
import yaml

SCHEMA = {
    'const': {
        'type': 'dict',
        'nullable': True,
        'schema': {
            'tx_src_address': {'type': 'ipv4address'},
            'tx_v6_src_address': {'type': 'ipv6address'},
            'rx_mcast_address': {'type': 'ipv4address'},
            'lie_mcast_address': {'type': 'ipv4address'}
        },
    },
    'shards': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'min': 0},
                'nodes': {
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'name': {'type': 'string'},
                            'passive': {'type': 'boolean'},
                            'level': {'type': 'level'},
                            'systemid': {'type': 'integer', 'min': 0},
                            'rx_lie_mcast_address': {'type': 'ipv4address'},
                            'tx_lie_mcast_address': {'type': 'ipv4address'},
                            'rx_lie_v6_mcast_address': {'type': 'ipv6address'},
                            'tx_lie_v6_mcast_address': {'type': 'ipv6address'},
                            'rx_lie_port': {'type': 'port'},
                            'tx_lie_port': {'type': 'port'},
                            'rx_tie_port': {'type': 'port'},
                            'state_thrift_services_port': {'type': 'port'},
                            'config_thrift_services_port': {'type': 'port'},
                            'v4prefixes': {
                                'type': 'list',
                                'schema': {
                                    'type': 'dict',
                                    'schema': {
                                        'address': {'required': True, 'type': 'ipv4address'},
                                        'mask': {'required': True, 'type': 'ipv4mask'},
                                        'metric': {'type': 'integer', 'min': 1},
                                    }
                                }
                            },
                            'v6prefixes': {
                                'type': 'list',
                                'schema': {
                                    'type': 'dict',
                                    'schema': {
                                        'address': {'required': True, 'type': 'ipv6address'},
                                        'mask': {'required': True, 'type': 'ipv6mask'},
                                        'metric': {'type': 'integer', 'min': 1},
                                    }
                                }
                            },
                            'interfaces': {
                                'type': 'list',
                                'schema': {
                                    'type': 'dict',
                                    'schema': {
                                        'name': {'required': True, 'type': 'string'},
                                        'metric': {'type': 'integer', 'min': 1},
                                        'bandwidth': {'type': 'integer', 'min': 1},
                                        'rx_lie_mcast_address': {'type': 'ipv4address'},
                                        'tx_lie_mcast_address': {'type': 'ipv4address'},
                                        'rx_lie_v6_mcast_address': {'type': 'ipv6address'},
                                        'tx_lie_v6_mcast_address': {'type': 'ipv6address'},
                                        'rx_lie_port': {'type': 'port'},
                                        'tx_lie_port': {'type': 'port'},
                                        'rx_tie_port': {'type': 'port'},
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

def default_interface_name():
    # TODO: use eth0 on Linux
    return 'en0'

DEFAULT_CONFIG = {
    'shards': [
        {
            'id': 0,
            'nodes': [
                {
                    'interfaces': [
                        {
                            'name': default_interface_name()
                        }
                    ]
                }
            ]
        }
    ]
}

class RiftValidator(cerberus.Validator):

    def _validate_type_ipv4address(self, value):
        try:
            ipaddress.IPv4Address(value)
        except ValueError:
            return False
        else:
            return True

    def _validate_type_ipv4mask(self, value):
        try:
            mask = int(value)
        except ValueError:
            return False
        else:
            return 0 <= mask <= 32

    def _validate_type_ipv6address(self, value):
        try:
            ipaddress.IPv6Address(value)
        except ValueError:
            return False
        else:
            return True

    def _validate_type_ipv6mask(self, value):
        try:
            mask = int(value)
        except ValueError:
            return False
        else:
            return 0 <= mask <= 128

    def _validate_type_port(self, value):
        try:
            port = int(value)
        except ValueError:
            return False
        else:
            return 1 <= port <= 65535

    def _validate_type_level(self, value):
        if isinstance(value, str) and value.lower() in ['undefined', 'leaf', 'spine', 'top-of-fabric']:
            return True
        try:
            level = int(value)
        except ValueError:
            return False
        else:
            return 0 <= level <= 3

def apply_inheritance(config):
    if 'shards' in config:
        for shard_config in config['shards']:
            if 'nodes' in shard_config:
                for node_config in shard_config['nodes']:
                    node_apply_inheritance(node_config)

def node_apply_inheritance(node_config):
    if 'interfaces' in node_config:
        for interface_config in node_config['interfaces']:
            interface_apply_inheritance(interface_config, node_config)

def interface_apply_inheritance(interface_config, node_config):
    intf_inherit_attr_from_node(interface_config, 'rx_lie_mcast_address', node_config)
    intf_inherit_attr_from_node(interface_config, 'tx_lie_mcast_address', node_config)
    intf_inherit_attr_from_node(interface_config, 'rx_lie_ipv6_mcast_address', node_config)
    intf_inherit_attr_from_node(interface_config, 'tx_lie_ipv6_mcast_address', node_config)
    intf_inherit_attr_from_node(interface_config, 'rx_lie_port', node_config)
    intf_inherit_attr_from_node(interface_config, 'tx_lie_port', node_config)

def intf_inherit_attr_from_node(interface_config, attribute, node_config):
    if (not attribute in interface_config) and (attribute in node_config):
        interface_config[attribute] = node_config[attribute]

def apply_inferences(config):
    if 'shards' in config:
        for shard_config in config['shards']:
            if 'nodes' in shard_config:
                for node_config in shard_config['nodes']:
                    node_apply_inferences(node_config, config)

def node_apply_inferences(node_config, config):
    if 'interfaces' in node_config:
        for interface_config in node_config['interfaces']:
            interface_apply_inferences(interface_config, config)

def interface_apply_inferences(interface_config, config):
    neighbor_interface_config = interface_find_neighbor_config(interface_config, config)
    if not neighbor_interface_config:
        return
    intf_infer_att_from_neighbor(
        interface_config, 'rx_lie_mcast_address', neighbor_interface_config, 'tx_lie_mcast_address')
    intf_infer_att_from_neighbor(
        interface_config, 'tx_lie_mcast_address', neighbor_interface_config, 'rx_lie_mcast_address')
    intf_infer_att_from_neighbor(
        interface_config, 'rx_lie_v6_mcast_address', neighbor_interface_config,
        'tx_lie_v6_mcast_address')
    intf_infer_att_from_neighbor(
        interface_config, 'tx_lie_v6_mcast_address', neighbor_interface_config,
        'rx_lie_v6_mcast_address')
    intf_infer_att_from_neighbor(
        interface_config, 'rx_lie_port', neighbor_interface_config, 'tx_lie_port')
    intf_infer_att_from_neighbor(
        interface_config, 'tx_lie_port', neighbor_interface_config, 'rx_lie_port')
    intf_infer_att_from_neighbor(
        interface_config, 'rx_tie_port', neighbor_interface_config, 'tx_tie_port')

def interface_find_neighbor_config(interface_config, config):
    if 'rx_lie_port' in interface_config:
        neighbor_interface = find_remote_intf_config_by_att(
            config, 'tx_lie_port', interface_config['rx_lie_port'])
    elif 'tx_lie_port' in interface_config:
        neighbor_interface = find_remote_intf_config_by_att(
            config, 'rx_lie_port', interface_config['tx_lie_port'])
    else:
        neighbor_interface = None
    return neighbor_interface

def find_remote_intf_config_by_att(config, attr_name, attr_value):
    if 'shards' in config:
        for shard_config in config['shards']:
            if 'nodes' in shard_config:
                for node_config in shard_config['nodes']:
                    if 'interfaces' in node_config:
                        for interface_config in node_config['interfaces']:
                            if ((attr_name in interface_config) and
                                    (interface_config[attr_name] == attr_value)):
                                return interface_config
    return None

def intf_infer_att_from_neighbor(intf_config, intf_attribute, neighbor_intf_config,
                                 neighbor_intf_attribute):
    if intf_attribute in intf_config:
        # Interface attribute is already known, make sure it is consistent with the neighbor
        if neighbor_intf_attribute in neighbor_intf_config:
            if intf_config[intf_attribute] != neighbor_intf_config[neighbor_intf_attribute]:
                print("Configuration error: {} for interface {} ({}) must be same "
                      "as {} for interface {} ({})".format(
                          intf_attribute,
                          intf_config['name'],
                          intf_config[intf_attribute],
                          neighbor_intf_attribute,
                          neighbor_intf_config['name'],
                          neighbor_intf_config[intf_attribute]))
                sys.exit(1)
    else:
        # Interface attribute is not already known, infer it from the neighbor's configuration
        # if possible
        if neighbor_intf_attribute in neighbor_intf_config:
            intf_config[intf_attribute] = neighbor_intf_config[neighbor_intf_attribute]

def parse_configuration(filename):
    if filename:
        with open(filename, 'r') as stream:
            try:
                config = yaml.load(stream)
            except yaml.YAMLError as exception:
                raise exception
    else:
        config = DEFAULT_CONFIG
    validator = RiftValidator(SCHEMA)
    if not validator.validate(config, SCHEMA):
        # TODO: Better error handling (report in human-readable format and don't just exit)
        pretty_printer = pprint.PrettyPrinter()
        pretty_printer.pprint(validator.errors)
        exit(1)
    apply_inheritance(config)
    apply_inferences(config)
    return config
