#
# Convert SPI file coordinates to Anatomist MRI coordinates as a list of 3d points
#
def spi2Anatomist(spifile, offset = [93, 116, 101]):
    anat = []
    with open(spifile, "r") as f:
        for line in f:
            v = line.split()
            anat.append([float(v[0]) + offset[0], offset[1] - float(v[1]), offset[2] - float(v[2])])
    return anat

