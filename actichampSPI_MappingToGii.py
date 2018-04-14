import spi2anatomist
from ledNearestVertex import closest_node
from soma import aims
import numpy as np
#import pdb

spiA = spi2anatomist.spi2Anatomist("Manik_actiCHamp64_5000_LSMAC.spi")
gii = aims.read("full.gii")
vertA = gii.vertex()
out = np.zeros((len(vertA), len(spiA)))
for idx, v in enumerate(vertA):
    #pdb.set_trace()
    out[idx, closest_node(v, spiA)] = 1

np.save("spi2fullGii", out)



