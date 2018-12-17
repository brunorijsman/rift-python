import re

import kernel

# pylint: disable=line-too-long
# pylint: disable=bad-continuation

def test_show_kernel_links():
    kern = kernel.Kernel(log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # We assume the loopback interface (lo) is always there, and we look for something like this:
    # +-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
    # | Interface | Interface | Hardware          | Hardware          | Link Type | MTU   | Flags     |
    # | Name      | Index     | Address           | Broadcast         |           |       |           |
    # |           |           |                   | Address           |           |       |           |
    # +-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
    # | lo        | 1         | 00:00:00:00:00:00 | 00:00:00:00:00:00 |           | 65536 | UP        |
    # ...
    tab_str = kern.cli_links_table().to_string()
    pattern = (r"[|] Interface +[|] +Interface +[|] +Hardware +[|] +Hardware  +[|] +Link Type +[|] +MTU   +[|] +Flags +[|]\n"
                "[|] Name      +[|] +Index     +[|] +Address  +[|] +Broadcast +[|] +          +[|] +      +[|] +      +[|]\n"
                "[|]           +[|] +          +[|] +         +[|] +Address   +[|] +          +[|] +      +[|] +      +[|]\n"
                "(.|[\n])*"
                "[|] lo +[|] +[0-9]+ +[|] +[0-9:]+ +[|] +[0-9:]+ +[|] + +[|] +[0-9 ]+[|] +UP +[|]\n")
    assert re.search(pattern, tab_str) is not None
