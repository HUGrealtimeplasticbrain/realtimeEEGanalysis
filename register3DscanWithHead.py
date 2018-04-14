from pycpd import rigid_registration
from soma import aims
import numpy as np
import pdb
def register3DscanWithHead(f1, f2):
    m1 = aims.read(f1)
    m2 = aims.read(f2)
    pdb.set_trace()
    tr = rigid_registration(np.array(m1.vertex()), np.array(m2.vertex()))
    return tr

if __name__ == "__main__":
    register3DscanWithHead("/home/manik/test.gii.mesh", "/home/manik/full.gii")
    pdb.set_trace()

