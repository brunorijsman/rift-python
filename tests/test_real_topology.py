import platform
import subprocess

def test_real_topology():
    # Skip this test if we are not running on Linux
    if platform.system() != "Linux":
        return
    # If we are running on Linux, we insist that the "ip" command is available
    assert subprocess.call(["ip", "route"]) == 0
