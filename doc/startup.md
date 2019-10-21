# Startup Instructions

## Starting RIFT

Go into the rift-fsm directory that was created when you cloned the git repository:

<pre>
$ <b>cd ~/rift-python</b>
</pre>

Make sure the Python environment that you created during the installation is activated. This is 
needed to make sure you run the right version of Python 3 and that the right versions of all
dependency modules can be found:

<pre>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

Start the RIFT protocol engine in interactive mode (i.e. using stdin and stdout for the CLI) as
follows:

<pre>
(env) $ <b>python rift --interactive topology/two_by_two_by_two.yaml</b>
agg_101>
</pre>

You can now enter CLI commands, for example:

<pre>
agg_101> <b>show interfaces</b>
+-------------+-----------------------+-----------+-----------+
| Interface   | Neighbor              | Neighbor  | Neighbor  |
| Name        | Name                  | System ID | State     |
+-------------+-----------------------+-----------+-----------+
| if_101_1    | core_1:if_1_101       | 1         | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_1001 | edge_1001:if_1001_101 | 1001      | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_1002 | edge_1002:if_1002_101 | 1002      | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_2    | core_2:if_2_101       | 2         | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
</pre>

Exit the RIFT CLI and terminate the RIFT engine as follows:

<pre>
agg_101> <b>exit</b>
(env) $ 
</pre>