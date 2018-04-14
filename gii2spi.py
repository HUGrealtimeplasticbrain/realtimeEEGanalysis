# 
# Load a gifti mesh and convert it as a SPI file for Cartool
#

from soma import aims

m = aims.read("/home/manik/full.gii")

idx = 0
f = open("/home/manik/full.spi", "w")
for v in m.vertex():
   f.write(str(v[0]-93.0)+ "     "+str(-v[1]-167+283) + "      " + str(-v[2]-163+264) + "     LAS"+str(idx)+"\n")
   idx += 1

f.close()


