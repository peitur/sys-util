import sys,os,re,traceback
from os.path import isfile, join
from pprint import pprint


############# CONSTANTS
PROCINFO_DIR="/proc"
PROCINFO_FILE="status"
PROCINFO_FIELDS={
    "Name": { 'type':"string" },
    "State": { 'type':"list" },
    "Tgid": { 'type':"int" },
    "Ngid": { 'type':"int" },
    "Pid": { 'type':"int" },
    "PPid": { 'type':"int" },
    "TracerPid": { 'type':"int" },
    "Uid": { 'type':"list" },
    "Gid": { 'type':"list" },
    "FDSize": { 'type':"int" },
    "Groups": { 'type':"list" },
    "Threads": { 'type':"int" },
    "SigQ": { 'type':"part", 'sep':"/" }
}
########################

class ProcessInfo:
    '''
    '''
    def __init__( self, **options ):
        self.__info = None
        self.__filename = None

        self.__is_dirty = True

        if "filename" in options: self.__filename = options['filename']

    def parse_content( self, data ):

        fields = PROCINFO_FIELDS.keys()

        result_data = {}
        for delem in data:
            dval = re.split( r"\s+", re.sub( r":", "", delem ) )

#            pprint( dval )
            dkey = dval.pop(0)
            if dkey in fields:

                if 'type' in PROCINFO_FIELDS[ dkey ] and PROCINFO_FIELDS[ dkey]['type'] == "string":
                    result_data[ dkey.lower() ] = dval[0]

                if 'type' in PROCINFO_FIELDS[ dkey ] and PROCINFO_FIELDS[ dkey]['type'] == "list":
                    result_data[ dkey.lower() ] = ",".join( dval )

                if 'type' in PROCINFO_FIELDS[ dkey ] and PROCINFO_FIELDS[ dkey]['type'] == "int":
                    result_data[ dkey.lower() ] = dval[0]

                if 'type' in PROCINFO_FIELDS[ dkey ] and PROCINFO_FIELDS[ dkey]['type'] == "part":
                    result_data[ dkey.lower() ] = ",".join( re.split( PROCINFO_FIELDS[ dkey ]['sep'] , dval[0] ) )

        return result_data

    def load_file( self, filename=None ):

        loadfilename = self.__filename


        if filename:
            loadfilename = filename

        if not os.path.exists( loadfilename ):
            tb = sys.exc_info()[2]
            raise FileNotFoundError( "PID %(p)s state not found " % {'p': self.__info['pid'] } ).with_traceback(tb)

        try:

            data = []
            fd = open( loadfilename, "r" )
            for line in fd:
                data.append( line.lstrip().rstrip() )
            fd.close()

            self.__info = self.parse_content( data )

            return self.__info

        except Exception as error:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)

        return None

    def get_by( self, key ):
        return self.__info[ key ]

    def get_info( self ):
        return self.__info



class ProcessUtil:
    '''
    '''

    def __init__( self , **options ):

        self.debug = False
        self.test = False

#        self.__proc_cache__ = { dirty = True }

        if 'debug' in options and options['debug'] in [True, False]: self.debug = options['debug']
        if 'test' in options and options['test'] in [True, False]: self.test = options['test']



    def scan_proclist( self, path=PROCINFO_DIR ):
        rx = re.compile( "^[0-9]+$" )

        plist = []

        for f in os.listdir( path ):
            try:

                if rx.match( f ):
                    statusfile = path+"/"+f+"/"+PROCINFO_FILE

                    if self.debug: print("DEBUG: Loading process status %(pf)s" % {'pf': statusfile} )

                    pd = ProcessInfo( filename=path+"/"+f+"/"+PROCINFO_FILE , debug=self.debug, test=self.test )
                    ddata = pd.load_file( statusfile )
                    plist.append( ddata )

            except Exception as error:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
                pprint( error )
                pass

        return plist

    def proc_tree( self, proclist ):
        pass

    def proc_by( self, key, filter, **options ):
        '''
            Get all processes by name
        '''

        plist = self.scan_proclist()

        for p in plist:
            k = p.get_by( key )
            if k == key:
                result_data.append( p.get_info() )

        result_data = []

        return result_data

if __name__ == "__main__":



    pi = ProcessUtil( debug=True )
    pprint( pi.scan_proclist() )
