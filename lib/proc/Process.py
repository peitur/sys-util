import sys,os,re
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
        self.__info__ = None
        self.__filename__ = None

        if "filename" in options: self.__filename__ = options['filename']

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

    def load_file( self, filename ):

        try:
            data = []
            fd = open( filename, "r" )
            for line in fd: data.append( line.lstrip().rstrip() )
            fd.close()

            return self.parse_content( data )

        except Exception as error:
            pprint( error )




class ProcessUtil:
    '''
    '''

    def __init__( self , **options ):

        self.debug = False
        self.test = False

        if 'debug' in options and options['debug'] in [True, False]: self.debug = options['debug']
        if 'test' in options and options['test'] in [True, False]: self.test = options['test']



    def scan_proclist( self, path=PROCINFO_DIR ):
        rx = re.compile( "[0-9]+" )

        plist = []
        for f in os.listdir( path ):
            pd = ProcessInfo( filename=path+"/"+f+"/"+PROCINFO_FILE )
            plist.append( pd.load_file( path+"/"+f+"/"+PROCINFO_FILE ) )

        return plist

    def proc_tree( self, proclist ):
        pass

if __name__ == "__main__":

    pi = ProcessUtil( debug=True )
    pprint( pi.scan_proclist() )
