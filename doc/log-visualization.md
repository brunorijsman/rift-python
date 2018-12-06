# Log Visualization

## Debug logs

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

## Log visualization

The following script converts a log file (which is assumed to be named rift.log) into a HTML file (name rift.log.html) that visualizes the events in the log in an easy-to-understand graphical way.

<pre>
(env) $ <b>rift/visualize_log.py</b>
</pre>

On an Apple Mac the generated HTML file can be viewed in the default web browser as follows:

<pre>
(env) $ <b>open rift.log.html</b>
</pre>

Note: the generated HTML file produces graphics using Structured Vector Graphics (SVG). If the log is long (more than a few minutes of running RIFT), the HTML file can become extremely large and
rendering the file in the browser can become extremely slow and memory intensive.

[This example diagram](http://bit.ly/rift-visualization-example-1) shows a simple example where 2 RIFT nodes establish a 3-way example.

This visualization tools has proven to be indispensable to understand what is happening in complex multi-node scenarios.

The visualization shows the following:
 * One vertical black line to represent each node
 * One vertical black line to represent each interface
 * Orange dots on the node line to represent events on the node FSM (= ZTP FSM)
 * Red dots on the interface line to represent events on the interface FSM (= LIE FSM)
 * Blue dots on the interface line to represent sent and received messages (with a line between the TX and RX dot)
 * Bright orange dots to report log messages at severity WARNING or higher

You can hover the cursor over any blue dot to get a detailed decode of the message.

You can select or unselect the buttons at the top of the visualization to filter specific elements of interest (to make the diagram less cluttered)
