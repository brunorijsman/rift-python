## Configuration File

If you start the RIFT protocol engine without any command-line arguments it will start a single RIFT node which
runs on Ethernet interface "en0".

Note: en0 is the name of the Ethernet interface on a Macbook. A future version of the code will pick the default 
Ethernet interface in a more portable way.

You can provide the name of a configuration file when you start the RIFT protocol engine:

<pre>
(env) $ <b>python main.py two_by_two_by_two.yaml</b>
Command Line Interface (CLI) available on port 49178
</pre>

The configuration file specifies a specifies the configuration attributes for the RIFT protocol instance,
including the attribute of the RIFT node and the RIFT interfaces.

It is also possible to configure multiple RIFT nodes in the configurion file. This is used to build simulated
network topologies that can be tested on a single physical computer. In the above example, the configurion
file "two_by_two_by_two.yaml" contains 10 simulated nodes with names core_1, core_2, agg_101, agg_102, etc.

The exact syntax of the configuration file is provided in the next section.


# Command-Line Options

"python main.py --help" provides you a list of all command line options:

<pre>
(env) $ <b>python main.py --help</b>
usage: main.py [-h] [-p | -n] [configfile]

Routing In Fat Trees (RIFT) protocol engine

positional arguments:
  configfile         Configuration filename

optional arguments:
  -h, --help         show this help message and exit
  -p, --passive      Run only the nodes marked as passive
  -n, --non-passive  Run all nodes except those marked as passive
</pre>

TODO: Finish this. Explain each command-line option.