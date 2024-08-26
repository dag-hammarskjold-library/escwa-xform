import sys, os
from escwa_xform.scripts import xform

def test_xform():
    with open('test.mrk', 'w') as f:
        sys.argv = [sys.argv[0]] + ['--connect=dummy', '--database=test', '--input_file=test.mrk']
        xform.run()

    os.remove('test.mrk')