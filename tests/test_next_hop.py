from ipaddress import IPv4Address, IPv6Address

from next_hop import NextHop

def test_next_hop_str():
    nhop = NextHop(False, None, None, None)
    assert str(nhop) == ""
    nhop = NextHop(False, "if1", None, None)
    assert str(nhop) == "if1"
    nhop = NextHop(False, "if2", IPv4Address("1.2.3.4"), None)
    assert str(nhop) == "if2 1.2.3.4"
    nhop = NextHop(False, "if2", IPv6Address("1111:1111::"), None)
    assert str(nhop) == "if2 1111:1111::"
    nhop = NextHop(False, "if3", IPv4Address("5.6.7.8"), 23)
    assert str(nhop) == "if3 5.6.7.8 (23)"
    nhop = NextHop(True, "if4", IPv4Address("9.9.9.9"), None)
    assert str(nhop) == "Negative if4 9.9.9.9"

def test_next_hop_ordering():
    # pylint:disable=unneeded-not
    # Negative is tie-breaker (one is None)
    nhop1 = NextHop(None, "if2", IPv4Address("2.2.2.2"), 22)
    nhop2 = NextHop(True, "if1", IPv4Address("1.1.1.1"), 11)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Negative is tie-breaker (neither is None)
    nhop1 = NextHop(False, "if2", IPv4Address("2.2.2.2"), 22)
    nhop2 = NextHop(True, "if1", IPv4Address("1.1.1.1"), 11)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Interface is tie-breaker (one is None)
    nhop1 = NextHop(False, None, IPv4Address("2.2.2.2"), 22)
    nhop2 = NextHop(False, "if2", IPv4Address("1.1.1.1"), 11)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Interface is tie-breaker (neither is None)
    nhop1 = NextHop(False, "if1", IPv4Address("2.2.2.2"), 22)
    nhop2 = NextHop(False, "if2", IPv4Address("1.1.1.1"), 11)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Address is tie-breaker (one is None)
    nhop1 = NextHop(False, "if1", None, 44)
    nhop2 = NextHop(False, "if1", IPv4Address("2.2.2.2"), 33)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Address is tie-breaker (neither is None, same address family)
    nhop1 = NextHop(False, "if1", IPv4Address("1.1.1.1"), 44)
    nhop2 = NextHop(False, "if1", IPv4Address("2.2.2.2"), 33)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Address is tie-breaker (neither is None, different address families)
    nhop1 = NextHop(False, "if1", IPv4Address("2.2.2.2"), 44)
    nhop2 = NextHop(False, "if1", IPv6Address("1111:1111::"), 33)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Weight is tie-breaker (one is None)
    nhop1 = NextHop(False, "if1", IPv4Address("1.1.1.1"), None)
    nhop2 = NextHop(False, "if1", IPv4Address("1.1.1.1"), 22)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Weight is tie-breaker (neither is None)
    nhop1 = NextHop(False, "if1", IPv4Address("1.1.1.1"), 11)
    nhop2 = NextHop(False, "if1", IPv4Address("1.1.1.1"), 22)
    assert nhop1 < nhop2
    assert not nhop1 > nhop2
    # Same
    nhop1 = NextHop(False, "if1", IPv4Address("1.1.1.1"), 11)
    nhop2 = NextHop(False, "if1", IPv4Address("1.1.1.1"), 11)
    assert not nhop1 < nhop2
    assert not nhop1 > nhop2
