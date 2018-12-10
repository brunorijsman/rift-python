import pytest

import constants

def test_direction_str():
    assert constants.direction_str(constants.DIR_SOUTH) == "South"
    assert constants.direction_str(constants.DIR_NORTH) == "North"
    assert constants.direction_str(constants.DIR_EAST_WEST) == "East-West"
    with pytest.raises(Exception):
        constants.direction_str(999)

def test_reverse_dir():
    assert constants.reverse_dir(constants.DIR_SOUTH) == constants.DIR_NORTH
    assert constants.reverse_dir(constants.DIR_NORTH) == constants.DIR_SOUTH
    assert constants.reverse_dir(constants.DIR_EAST_WEST) == constants.DIR_EAST_WEST
    with pytest.raises(Exception):
        constants.reverse_dir(999)

def test_address_family_str():
    assert constants.address_family_str(constants.ADDRESS_FAMILY_IPV4) == "IPv4"
    assert constants.address_family_str(constants.ADDRESS_FAMILY_IPV6) == "IPv6"
    with pytest.raises(Exception):
        constants.address_family_str(999)

def test_owner_str():
    assert constants.owner_str(constants.OWNER_S_SPF) == "South SPF"
    assert constants.owner_str(constants.OWNER_N_SPF) == "North SPF"
    with pytest.raises(Exception):
        constants.owner_str(999)
