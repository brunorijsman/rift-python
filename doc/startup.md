# Startup Instructions

## Starting RIFT

Go into the rift-fsm directory that was created when you cloned the git repository:

<pre>
$ <b>cd rift-fsm</b>
</pre>

Make sure the Python environment that you created during the installation is activated. This is needed to make sure you 
run the right version of Python 3 and that the right versions of all depencency modules can be found:

<pre>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

Start the RIFT protocol engine by runnning the rift-python package: 

<pre>
(env) $ <b>python rift-python</b>
Command Line Interface (CLI) available on port 49178
</pre>

Note that you can simply type python instead of python3 because activing the environment automatically selected the 
right version of Python:

<pre>
(env) $ <b>which python</b>
/Users/brunorijsman/rift-fsm/env/bin/python
(env) $ <b>python --version</b>
Python 3.5.1
</pre>

After you start RIFT, there should be a single line of output reporting that the Command Line Interface (CLI) is 
available on a particular TCP port (in this example port 49178):

<pre>
Command Line Interface (CLI) available on port 49178
</pre>
