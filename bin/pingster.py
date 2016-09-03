#!/usr/bin/python3

import os,re,sys,signal
import json, time
import threading, queue
import shlex, subprocess
from pprint import pprint


#########################################################

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
LIGHT_PURPLE = '\033[94m'
PURPLE = '\033[95m'
END = '\033[0m'

#########################################################

DEFAULT_PING_INTERVAL = 10
DEFAULT_PING_TIMEOUT = 10
DEFAULT_PING_CMD = "/usr/bin/ping"

DEFAULT_START_STATE = False

## 64 bytes from plain1.example.redbridge.se (127.0.0.1): icmp_seq=1 ttl=64 time=0.039 ms
PING_OK = r"^[0-9]+\s+bytes.+time=[0-9\.]+\s+ms"

#########################################################
stdoutQueue = queue.Queue()
stderrQueue = queue.Queue()
timerQueue  = queue.Queue()
stateQueue  = queue.Queue()
actionQueue  = queue.Queue()
#########################################################

threadsRunning = True

stateStore = {}

def signal_int_handler(signal, frame):
    global threadsRunning
    print('You pressed Ctrl+C!')
    threadsRunning = False

signal.signal( signal.SIGINT, signal_int_handler )


#########################################################
def is_boolean( data ):
    if data in (True, False):
        return True
    return False

def is_string( data ):
    if type( data ).__name__ == 'str':
        return True
    return False

def is_integer( data ):
    if type( data ).__name__ == 'int':
        return True
    return False

def is_dict( data ):
    if type( data ).__name__ == 'dict':
        return True
    return False

#########################################################

def read_json( filename, **options ):
	'''
		Read a json file
		filename: filename
		options:
			- debug : toggle debugging
		Returns: term
	'''
	data = []

	debug = False
	if 'debug' in options and options['debug'] in [True, False]: debug = options['debug']

	if debug: print("DEBUG: Reading file %(fn)s" % {'fn': filename } )

	try:

		for line in open( filename, "r"):
			data.append( line.rstrip().lstrip() )

	except Exception as error:
		pprint(error)

	if debug: print("DEBUG: Read %(ln)s lines from %(fn)s" % {'ln': len( data ), 'fn': filename } )
	if debug:
		pprint( data )

	return json.loads( "\n".join( data ) )



def queue_sizes():
    return {
        "stateQueue" : stateQueue.qsize(),
        "actionQueue": actionQueue.qsize(),
        "stdoutQueue": stdoutQueue.qsize(),
        "stderrQueue": stderrQueue.qsize(),
        "timerQueue":  timerQueue.qsize()
    }

def ping_ok_parser( line ):

    if re.match( PING_OK, line ):
        return True
    return False

def ping_thread( options ):
    global threadsRunning
    debug = False

    hostname = options['hostname']
    timeout = DEFAULT_PING_TIMEOUT
    interval = DEFAULT_PING_INTERVAL

    if "debug" in options: debug = options['debug']
    if "timeout" in options: timeout = options['timeout']
    if "interval" in options: interval = options['interval']

    cmd_arr = [ DEFAULT_PING_CMD ]
#    cmd_arr.append( "-i "+interval.__str__() )
    cmd_arr.append( hostname )

    if debug: stdoutQueue.put( "DEBUG: COMMAND: '%(cmd)s'" % {'cmd': " ".join( cmd_arr ) } )

    proc = subprocess.Popen( cmd_arr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=128 )
    while threadsRunning:

        line = proc.stdout.readline().lstrip().rstrip()
        if len( line ) > 0:
            if  ping_ok_parser( line ):
                stateQueue.put( { "hostname": hostname, "state": True, "config": options } )
            else:
                stateQueue.put( { "hostname": hostname, "state": False , "config": options } )



def action_thread( options ):
    global threadsRunning
    debug = False
    if "debug" in options: debug = options['debug']

    while threadsRunning:

        try:
            data = actionQueue.get( block=True, timeout=1 )
            config = data['config']
            name = ""
            if 'name' in config:
                name = config['name']


            state_str = "n/a"
            if data['to_state']:
                state_str = "%(col)s %(str)s %(nc)s" % { "col": GREEN, "str": data['to_state'], "nc": END }
            else:
                state_str = "%(col)s %(str)s %(nc)s" % { "col": RED, "str": data['to_state'], "nc": END }

            hostname_str = "%(col)s %(str)s %(nc)s" % { "col": PURPLE, "str": data['hostname'], "nc": END }
            name_str = "%(col)s %(str)s %(nc)s" % { "col": PURPLE, "str": name, "nc": END }


            stdoutQueue.put( "%(host)-32s %(name)-32s %(st)s" % { 'host': hostname_str, 'name': name_str, 'st': state_str } )

        except queue.Empty:
            pass




def timer_thread( options ):
    global threadsRunning

    debug = False
    if "debug" in options: debug = options['debug']

    waittime = 1
    if 'wait' in options:
        waittime = options['wait']

    while waittime > 0 and threadsRunning:
        time.sleep( 1 )
        waittime -= 1



def state_thread( options ):
    global threadsRunning

    debug = False
    if "debug" in options: debug = options['debug']

    global stateStore
    while threadsRunning:
        try:
            data = stateQueue.get( block=True, timeout=1)

            hostname = data['hostname']
            newState = data['state']
            oldState = stateStore[ hostname ]['state']

            stateStore[ hostname ]['state'] = newState

            if oldState != newState:
                actionQueue.put( { "hostname":hostname, "from_state": oldState, "to_state": newState, "config": data['config'] } )



        except queue.Empty:
            pass



def print_stdout_thread( options ):
    global threadsRunning
    debug = False
    if "debug" in options: debug = options['debug']

    while threadsRunning:

        try:
            data = stdoutQueue.get( block=True, timeout=1 )

            if is_dict( data ):
                pprint( data )
            else:
                print( data )

        except queue.Empty:
            pass

def print_stderr_thread( options ):
    global threadsRunning
    debug = False
    if "debug" in options: debug = options['debug']

    while threadsRunning:

        try:
            data = stderrQueue.get( block=True, timeout=1 )
            if is_dict( data ):
                pprint( data )
            else:
                print( data )

        except queue.Empty:
            pass





if __name__ == "__main__":

    options = {}
    options['debug'] = False

    options['script'] = sys.argv.pop(0)
    options['filename'] = None

    if len( sys.argv ) > 0:

        threads = {}
        threads['stdout'] = threading.Thread( target=print_stdout_thread, args=(options,) )
        threads['stderr'] = threading.Thread( target=print_stderr_thread, args=(options,) )
        threads['status'] = threading.Thread( target=state_thread, args=(options,) )
        threads['action'] = threading.Thread( target=action_thread, args=(options,) )

        for t in threads: threads[t].start()

        options['filename'] = sys.argv.pop(0)

        try:

            config = read_json( options['filename'] )

            hostlist = config
            if 'hostlist' in config:
                hostlist = config['hostlist']

            for c in hostlist:

                c['debug'] = options['debug']
                stateStore[ c['hostname'] ] = { "hostname": c['hostname'], "state": DEFAULT_START_STATE, "config": c }

                kname = "ping_%s" % ( c['hostname'] )
                threads[ kname ] = threading.Thread( target=ping_thread, args=( c ,) )
                threads[ kname ].start()

                if options['debug']: print(">>>> Started %s" % ( kname ) )


        except Exception as error:
            pprint( error )


        time.sleep(30)
        threadsRunning = False

        pprint( stateStore )

        for t in threads: threads[t].join()

    else:
        print("No config file ...")
