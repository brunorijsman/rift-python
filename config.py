import argparse
import cerberus
import ipaddress
import pprint
import yaml

schema = {
    'const': {
        'type': 'dict',
        'nullable': True,
        'schema': {
            'rx_mcast_address': {
                'type': 'ipv4address'
            },
            'lie_mcast_address': {
                'type': 'ipv4address'
            }
        },
    },
    'shards': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {
                    'required': True,
                    'type': 'integer',
                    'min': 0,
                },
                'nodes': {
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'name': {
                                'type': 'string',
                            },
                            'passive': {
                                'type': 'boolean',
                            },
                            'level': {
                                'type': 'level',
                            },
                            'systemid': {
                                'type': 'integer',
                                'min': 0
                            },
                            'rx_lie_mcast_address': {
                                'type': 'ipv4address'
                            },
                            'rx_lie_v6_mcast_address': {
                                'type': 'ipv6address'
                            },
                            'rx_lie_port': {
                                'type': 'port'
                            },
                            'state_thrift_services_port': {
                                'type': 'port'
                            },
                            'config_thrift_services_port': {
                                'type': 'port'
                            },
                            'v4prefixes': {
                                'type': 'list',
                                'schema': {
                                    'type': 'dict',
                                    'schema': {
                                        'address': {
                                            'required': True,
                                            'type': 'ipv4address',
                                        },
                                        'mask': {
                                            'required': True,
                                            'type': 'ipv4mask',
                                        },
                                        'metric': {
                                            'type': 'integer',
                                            'min': 1
                                        }
                                    }
                                }
                            },
                            'v6prefixes': {
                                'type': 'list',
                                'schema': {
                                    'type': 'dict',
                                    'schema': {
                                        'address': {
                                            'required': True,
                                            'type': 'ipv6address',
                                        },
                                        'mask': {
                                            'required': True,
                                            'type': 'ipv6mask',
                                        },
                                        'metric': {
                                            'type': 'integer',
                                            'min': 1
                                        }
                                    }
                                }
                            },
                            'interfaces': {
                                'type': 'list',
                                'schema': {
                                    'type': 'dict',
                                    'schema': {
                                        'name': {
                                            'required': True,
                                            'type': 'string',
                                        },
                                        'metric': {
                                            'type': 'integer',
                                            'min': 1
                                        },
                                        'bandwidth': {
                                            'type': 'integer',
                                            'min': 1
                                        },
                                        'tx_lie_port': {
                                            'type': 'port'
                                        },
                                        'rx_lie_port': {
                                            'type': 'port'
                                        },
                                        'rx_tie_port': {
                                            'type': 'port'
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
}

def default_interface_name():
    # TODO: use eth0 on Linux
    return 'en0'

default_config = {
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
        except:
            return False
        else:
            return True

    def _validate_type_ipv4mask(self, value):
        try:
           mask = int(value)
        except:
            return False
        else:
            return (mask >= 0) and (mask <= 32)

    def _validate_type_ipv6address(self, value):
        try:
           ipaddress.IPv6Address(value)
        except:
            return False
        else:
            return True

    def _validate_type_ipv6mask(self, value):
        try:
           mask = int(value)
        except:
            return False
        else:
            return (mask >= 0) and (mask <= 128)

    def _validate_type_port(self, value):
        try:
           port = int(value)
        except:
            return False
        else:
            return (port >= 1) and (port <= 65535)

    def _validate_type_level(self, value):
        if isinstance(value, str) and value.lower() in ['undefined', 'leaf', 'spine', 'superspine']:
            return True
        try:
           level = int(value)
        except:
            return False
        else:
            return (level >= 0) and (level <= 3)

def parse_configuration(filename):
    if filename:
        with open(filename, 'r') as stream:
            try:
                config = yaml.load(stream)
            except yaml.YAMLError as exception:
                raise exception
    else:
        config = default_config
    validator = RiftValidator(schema)
    if not validator.validate(config, schema):
        # TODO: Better error handling (report in human-readable format and don't just exit)
        pp = pprint.PrettyPrinter()
        pp.pprint(validator.errors)
        exit(1)
    return config
