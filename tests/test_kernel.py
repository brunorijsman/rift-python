import kernel

def test_unsupported_platform_error():
    kern = kernel.Kernel()
    assert kern.platform_supported
    tab_str = kern.cli_links_table().to_string()
    assert tab_str == "foo"
