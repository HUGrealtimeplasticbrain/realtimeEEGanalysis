from soma import aims
from scipy import spatial
import numpy as np

def closest_node(node, nodes):
    closest_index = spatial.distance.cdist([node], nodes).argmin()
    return nodes[closest_index]

def nearestVertexForLeds(mesh1, leds)
    m1 = aims.read(mesh1)
    v = np.array(m1.vertex())
    out = []
    for l in leds:
        o.append(closest_node(l, v))
    return out



