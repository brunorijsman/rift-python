# Log Visalization

The Python RIFT protocol engine write all logs for all nodes in a topology to a single log file rift.log in the same directory where from where the engine was started.

By default, the engine logs at level INFO, which only reports unusual events and not common expected events such as normal FSM transitions.

However, if you start the Python RIFT protocol engine, you can use the "--log-level debug" or "-l debug" command line option to report at debug level.

For example:

<pre>
(env) $ <b>python rift --log-level debug topology/2n_l0_l1.yaml</b>
Command Line Interface (CLI) available on port 58995
</pre>

This will cause Python RIFT to write messages to the log for common events, including all sent and received messages, and all FSM transitions. Note that it will also cause the log file to become very large.

These debug log messages are very detailed and very structured, which allows them to be processed by automated tools, including for example grep.

The tools directory in the Github repository contains a log visualization tools that converts the raw log file (rift.log) into an HTML file (rift.log.html) which provides a graphical ladder diagram showing all the events. This HTML file can be viewed with any web browser.

[This example diagram](http://bit.ly/rift-visualization-example-1) shows a simple example where 2 RIFT nodes establish a 3-way example.

This visualization tools has proven to be indispensable to understand what is happening in complex multi-node scenarios.

Right now the visualization tool is somewhat basic. Hopefully I will be able to enhance it in the future with various controls to filter on specific events of interest, to provide more details when you hover over specific items, etc. etc.