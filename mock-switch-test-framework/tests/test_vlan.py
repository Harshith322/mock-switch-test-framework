"""VLAN configuration tests - set/get round trip and edge cases."""

import pytest


@pytest.mark.functional
def test_default_vlan_is_one(switch):
    assert switch.get_vlan(1) == 1


@pytest.mark.functional
@pytest.mark.parametrize("vlan_id", [10, 100, 4094])
def test_set_and_get_vlan(switch, vlan_id):
    switch.set_vlan(5, vlan_id)
    assert switch.get_vlan(5) == vlan_id


@pytest.mark.functional
def test_vlan_is_per_port(switch):
    switch.set_vlan(1, 20)
    switch.set_vlan(2, 30)
    assert switch.get_vlan(1) == 20
    assert switch.get_vlan(2) == 30
