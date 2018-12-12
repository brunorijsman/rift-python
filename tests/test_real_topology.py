#import platform
import subprocess

def test_ls():
    assert subprocess.call(["ls"]) == 0

def test_ip_route():
    #assert platform.system() == "Linux"
    assert subprocess.call(["ip", "route"]) == 0

def test_brctl():
    #assert platform.system() == "Linux"
    assert subprocess.call(["brctl"]) == 0

def test_brctl_show():
    #assert platform.system() == "Linux"
    assert subprocess.call(["brctl", "show"]) == 0

def test_brctl_add():
    #assert platform.system() == "Linux"
    assert subprocess.call(["brctl", "addbr", "foo"]) == 0
