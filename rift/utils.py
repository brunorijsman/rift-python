import socket

import netifaces

def interface_ipv4_address(interface_name):
    interface_addresses = netifaces.interfaces()
    if not interface_name in netifaces.interfaces():
        return None, None
    interface_addresses = netifaces.ifaddresses(interface_name)
    if not netifaces.AF_INET in interface_addresses:
        return None, None
    intf = interface_addresses[netifaces.AF_INET][0]
    return intf['addr'], intf['netmask']

def interface_ipv6_address(interface_name):
    interface_addresses = netifaces.interfaces()
    if not interface_name in netifaces.interfaces():
        return None
    interface_addresses = netifaces.ifaddresses(interface_name)
    if not netifaces.AF_INET6 in interface_addresses:
        return None
    return interface_addresses[netifaces.AF_INET6][0]['addr']

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except socket.error:
        return False
    return True

def system_id_str(system_id):
    # Heuristic: if the system_id < 1000000 then it is probably configured, otherwise it is probably
    # derived from the MAC address, the process ID, and the node nr.
    if system_id < 1000000:
        return "{:d}".format(system_id)
    else:
        return "{:016x}".format(system_id)

def secs_to_dmhs_str(secs):
    mins = 0
    hours = 0
    days = 0
    if secs >= 60.0:
        mins = int(secs / 60.0)
        secs -= mins * 60.0
    if mins >= 60:
        hours = mins // 60
        mins %= 60
    if hours >= 24:
        days = hours // 24
        hours %= 24
    return "{:d}d {:02d}h:{:02d}m:{:05.2f}s".format(days, hours, mins, secs)

def value_str(value, singular_units=None, plural_units=None):
    if value is None:
        return ""
    string = str(value)
    if singular_units is None:
        return string
    if isinstance(value, int) and value == 1:
        return string + " " + singular_units
    if plural_units is None:
        plural_units = singular_units + "s"
    return string + " " + plural_units
