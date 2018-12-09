import os
import subprocess

import rift_expect_session

def test_visualize_log_file():
    # Briefly run RIFT to produce a valid log file
    res = rift_expect_session.RiftExpectSession("2n_l0_l1")
    res.stop()
    # If rift.log.html still exists from a previous run, remove it
    html_file_name = "rift.log.html"
    if os.path.exists(html_file_name):
        os.remove(html_file_name)
    # Run the visualization tool, and makes sure it exits without an error
    return_code = subprocess.call("rift/visualize_log.py")
    assert return_code == 0
    # Check that a visualization file was indeed produced
    assert os.path.exists(html_file_name)
    # We can't really check that the visualization "looks good" So, instead we just check that there
    # is at least <svg ...> and </svg> tags, which is a decent indication that the tool ran to
    # completion.
    found_start = False
    found_end = False
    with open(html_file_name) as infile:
        for line in infile:
            if line.startswith("<svg"):
                found_start = True
            if line.startswith("</svg>"):
                found_end = True
    assert found_start
    assert found_end
