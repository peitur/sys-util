
import os,re,sys
import unittest

sys.path.append("../lib")
import mem.Memory

MEMINFO_FILE="/proc/meminfo"

class MemoryTest(unittest.TestCase):

    def test_memory_list( self ):
        pass


if __name__ == "__main__":
    unittest.main()
