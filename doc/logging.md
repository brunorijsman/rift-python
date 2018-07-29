# Logging

The RIFT protocol engine writes log messages to the file rift.log in the same directory as where the RIFT protocol 
engine was started.

Note: when the RIFT protocol engine starts, it does not erase the existing rift.log file, it just appends to it.
If you log at level DEBUG (see below) the rift.log file can become extremely large and fill up your disk. It is 
recommended to configure log rotation (e.g. using Linux logrotate).

It is useful to monitor the log file as the RIFT protocol engine is running using the <b>tail -f</b> command:

<pre>
(env) $ <b>tail -f rift.log</b>
2018-07-29 13:03:20,682:INFO:node.fsm:[2001] Start FSM, state=COMPUTE_BEST_OFFER
2018-07-29 13:03:20,682:INFO:node.fsm:[2001] FSM push event, event=COMPUTATION_DONE
2018-07-29 13:03:20,682:INFO:node:[2002] Create node
2018-07-29 13:03:20,682:INFO:node.if:[2002-if_2002_201] Create interface
2018-07-29 13:03:20,682:INFO:node.if.fsm:[2002-if_2002_201] Create FSM
2018-07-29 13:03:20,682:INFO:node.if:[2002-if_2002_202] Create interface
2018-07-29 13:03:20,682:INFO:node.if.fsm:[2002-if_2002_202] Create FSM
2018-07-29 13:03:20,683:INFO:node.fsm:[2002] Create FSM
2018-07-29 13:03:20,683:INFO:node.fsm:[2002] Start FSM, state=COMPUTE_BEST_OFFER
2018-07-29 13:03:20,683:INFO:node.fsm:[2002] FSM push event, event=COMPUTATION_DONE
2018-07-29 13:05:38,323:INFO:node:[1] Create node
2018-07-29 13:05:38,324:INFO:node.if:[1-if_1_101] Create interface
2018-07-29 13:05:38,324:INFO:node.if.fsm:[1-if_1_101] Create FSM
2018-07-29 13:05:38,324:INFO:node.if:[1-if_1_102] Create interface
2018-07-29 13:05:38,325:INFO:node.if.fsm:[1-if_1_102] Create FSM
...
</pre>

By default, the RIFT protocol engine only writes log messages at severity INFO and higher to the log file.
This eliminates log messages at severity DEBUG which are used to report very common non-interesting events such
timer tick processing, receiving and sending periodic messages, etc.

The command-line option "<b>-l</b> <i>LOG_LEVEL</i>" or "<b>--log-level</b> <i>LOG_LEVEL</i>" logs messages at the 
specified <i>LOG_LEVEL</i> or higher. Valid values for <i>LOG_LEVEL</i> are <b>debug</b>, <b>info</b>,
<b>warning</b>, <b>error</b>, or <b>critical</b>.