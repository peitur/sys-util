import os,sys,re
from pprint import pprint

############# CONSTANTS
MEMINFO_FILE="/proc/meminfo"
MEMINFO_FIELDS=[
    { 'name': "MemTotal", 'unit':"kB" },
    { 'name': "MemFree", 'unit':"kB" },
    { 'name': "MemAvailable", 'unit':"kB" },
    { 'name': "Buffers", 'unit':"kB" },
    { 'name': "Cached", 'unit':"kB" },
    { 'name': "SwapCached", 'unit':"kB" },
    { 'name': "Active", 'unit':"kB" },
    { 'name': "Inactive", 'unit':"kB" },
    { 'name': "Active_anon", 'unit':"kB" },
    { 'name': "Inactive_anon", 'unit':"kB" },
    { 'name': "Active_file", 'unit':"kB" },
    { 'name': "Inactive_file", 'unit':"kB" },
    { 'name': "Unevictable", 'unit':"kB" },
    { 'name': "Mlocked", 'unit':"kB" },
    { 'name': "SwapTotal", 'unit':"kB" },
    { 'name': "SwapFree", 'unit':"kB" },
    { 'name': "Dirty", 'unit':"kB" },
    { 'name': "Writeback", 'unit':"kB" },
    { 'name': "AnonPages", 'unit':"kB" },
    { 'name': "Mapped", 'unit':"kB" },
    { 'name': "Shmem", 'unit':"kB" },
    { 'name': "Slab", 'unit':"kB" },
    { 'name': "SReclaimable", 'unit':"kB" },
    { 'name': "SUnreclaim", 'unit':"kB" },
    { 'name': "KernelStack", 'unit':"kB" },
    { 'name': "PageTables", 'unit':"kB" },
    { 'name': "NFS_Unstable", 'unit':"kB" },
    { 'name': "Bounce", 'unit':"kB" },
    { 'name': "WritebackTmp", 'unit':"kB" },
    { 'name': "CommitLimit", 'unit':"kB" },
    { 'name': "Committed_AS", 'unit':"kB" },
    { 'name': "VmallocTotal", 'unit':"kB" },
    { 'name': "VmallocUsed", 'unit':"kB" },
    { 'name': "VmallocChunk", 'unit':"kB" },
    { 'name': "HardwareCorrupted", 'unit':"kB" },
    { 'name': "AnonHugePages", 'unit':"kB" },
    { 'name': "HugePages_Total", "unit": None },
    { 'name': "HugePages_Free", "unit": None },
    { 'name': "HugePages_Rsvd", "unit": None },
    { 'name': "HugePages_Surp", "unit": None },
    { 'name': "Hugepagesize", 'unit':"kB" },
    { 'name': "DirectMap4k", 'unit':"kB" },
    { 'name': "DirectMap2M", 'unit':"kB" }
]
#############


class MemoryInfo:

    def __init__( self, fd = None, **options ):

        self.debug = False
        self.test = False

        if 'debug' in options and options['debug'] in [True, False]: self.debug = options['debug']
        if 'test' in options: self.test and options['test'] in [True, False]= options['test']
