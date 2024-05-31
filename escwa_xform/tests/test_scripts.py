import sys
from escwa_xform.scripts import xform

def test_xform():
    sys.argv = ['--arg=test']
    xform.run()