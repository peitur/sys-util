#!/usr/bin/python3

import os,re,sys,signal
import json, time, datetime
import threading, queue
import shlex, subprocess
from pprint import pprint


#########################################################

END = '\033[0m'

BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
ORANGE = '\033[33m'
BLUE = '\033[34m'
PURPLE = '\033[35m'
CYAN = '\033[36m'
YELLOW = '\033[93m'
PINK = '\033[95m'
DARKGRAY = '\033[90m'

LIGHTGRAY = '\033[37m'
LIGHTRED = '\033[91m'
LIGHTGREEN = '\033[92m'
LIGHTBLUE = '\033[94m'
LIGHTCYAN = '\033[96m'

#########################################################

DEFAULT_PING_INTERVAL = 10
DEFAULT_PING_TIMEOUT = 10
DEFAULT_PING_CMD = "ping"

DEFAULT_START_STATE = None

## 64 bytes from plain1.example.redbridge.se (127.0.0.1): icmp_seq=1 ttl=64 time=0.039 ms
PING_OK = [ r"^[0-9]+\s+bytes.+time=[0-9\.]+\s+ms" ]
PING_SKIP = [ r"^PING.+" ]

#########################################################
stdoutQueue = queue.Queue()
stderrQueue = queue.Queue()
timerQueue  = queue.Queue()
stateQueue  = queue.Queue()
actionQueue  = queue.Queue()
#########################################################

threadsRunning = True

stateStore = {}
threadInfo = {}

def signal_int_handler(signal, frame):
    global threadsRunning
    print('You pressed Ctrl+C!')
    threadsRunning = False

def signal_hup_handler(signal, frame):
    pass

signal.signal( signal.SIGINT, signal_int_handler )
signal.signal( signal.SIGHUP, signal_hup_handler )


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



def status_list( status, frame="" ):
    result = []

    timestamp_now = datetime.datetime.now()

    result.append(frame)
    result.append( "%(col)s%(str)-48s %(time)s %(end)s" % { 'col': YELLOW, 'end': END, 'str': "Time:", 'time': timestamp_now } )
    for s in status:
        data = status[s]
        config = data['config']

        name = ""
        if 'name' in config:
            name = config['name']

        state_str = "n/a"
        if data['state']:
            state_str = "%(col)s %(str)s %(nc)s" % { "col": GREEN, "str": "Online", "nc": END }
        else:
            state_str = "%(col)s %(str)s %(nc)s" % { "col": RED, "str": "Offline", "nc": END }

        hostname_str = "%(col)s %(str)s %(nc)s" % { "col": PURPLE, "str": data['hostname'], "nc": END }
        name_str = "%(col)s %(str)s %(nc)s" % { "col": PURPLE, "str": name, "nc": END }
        result.append( "%(host)-32s %(name)-32s %(st)s" % { 'host': hostname_str, 'name': name_str, 'st': state_str } )

    result.append(frame)

    return result


def queue_sizes():
    return {
        "stateQueue" : stateQueue.qsize(),
        "actionQueue": actionQueue.qsize(),
        "stdoutQueue": stdoutQueue.qsize(),
        "stderrQueue": stderrQueue.qsize(),
        "timerQueue":  timerQueue.qsize()
    }

def ping_ok_parser( line ):
    for r in PING_OK:
        if re.match( r, line ):
            return True
    return False

def ping_skip_parser( line ):
    for r in PING_SKIP:
        if re.match( r, line ):
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
        if len( line ) > 0 and not ping_skip_parser( line ):
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
            if "mode" in data and data['mode'] == "change":

                config = data['config']
                name = ""
                if 'name' in config:
                    name = config['name']

                state_str = "n/a"
                if data['to_state']:
                    state_str = "%(col)s %(str)s %(nc)s" % { "col": GREEN, "str": "Online", "nc": END }
                else:
                    state_str = "%(col)s %(str)s %(nc)s" % { "col": RED, "str": "Offline", "nc": END }

                hostname_str = "%(col)s %(str)s %(nc)s" % { "col": PURPLE, "str": data['hostname'], "nc": END }
                name_str = "%(col)s %(str)s %(nc)s" % { "col": PURPLE, "str": name, "nc": END }
                stdoutQueue.put( "%(host)-32s %(name)-32s %(st)s" % { 'host': hostname_str, 'name': name_str, 'st': state_str } )

            elif "mode" in data and data['mode'] == "summary":
                stdoutQueue.put( "\n".join( status_list( stateStore, "============================================================" ) ) )

        except queue.Empty:
            pass




def timer_thread( options ):
    global threadsRunning

    debug = False
    if "debug" in options: debug = options['debug']

    waittime = 900
    if 'wait' in options:
        waittime = options['wait']

    initialTime = 10
    firstRun = True
    while threadsRunning:
        tt = waittime

        if firstRun:
            tt = initialTime
            firstRun = False

        while tt > 0 and threadsRunning:
            time.sleep( 1 )
            tt -= 1

        actionQueue.put( { "mode": "summary" } )



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
                actionQueue.put( { "mode": "change", "hostname":hostname, "from_state": oldState, "to_state": newState, "config": data['config'] } )



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

    threadInfo = {}

    if len( sys.argv ) > 0:

        threadInfo['stdout'] = threading.Thread( target=print_stdout_thread, args=(options,) )
        threadInfo['stderr'] = threading.Thread( target=print_stderr_thread, args=(options,) )
        threadInfo['status'] = threading.Thread( target=state_thread, args=(options,) )
        threadInfo['action'] = threading.Thread( target=action_thread, args=(options,) )
        threadInfo['timer'] = threading.Thread( target=timer_thread, args=(options,) )

        for t in threadInfo: threadInfo[ t ].start()

        options['filename'] = sys.argv.pop(0)

        try:

            config = read_json( options['filename'] )

            hostlist = config
            if 'hostlist' in config:
                hostlist = config['hostlist']

            for c in hostlist:

                c['debug'] = options['debug']
                name = ""
                if 'name' in c: name = c['name']
                stateStore[ c['hostname'] ] = { "hostname": c['hostname'], "state": DEFAULT_START_STATE, "config": c }

                kname = "ping_%s" % ( c['hostname'] )
                threadInfo[ kname ] = threading.Thread( target=ping_thread, args=( c ,) )
                threadInfo[ kname ].start()

                if options['debug']: print(">>>> Started %s" % ( kname ) )


        except Exception as error:
            pprint( error )


        for t in threadInfo: threadInfo[ t ].join()

    else:
        print("No config file ...")
