#
# LED setup editor for PlasticBrain
#
# (c) 2017 Manik Bhattacharjee
#


import plasticbrain
import sys
from soma import aims
from brainvisa import axon

from brainvisa.configuration import neuroConfig
neuroConfig.gui = True
from brainvisa import anatomist
import json, time
import pdb
import os

from soma.qt_gui.qt_backend import uic, QtGui, QtCore
from soma.qt_gui.qt_backend.QtCore import QThread

class LocateLeds(QtGui.QDialog):
    def __init__(self, app = None):
        QtGui.QDialog.__init__(self)
        self.ui = uic.loadUi("locateleds.ui", self)
        self.pb = plasticbrain.PlasticBrain()
        self.ui.startLocaButton.clicked.connect(self.start)
        self.ui.loadMeshButton.clicked.connect(self.loadMesh)
        self.ui.deviceCombo.currentIndexChanged.connect(self.updatedDeviceCombo)
        self.ui.saveButton.clicked.connect(self.save)
        self.ui.nextLedButton.clicked.connect(self.nextLed)
        self.ui.previousLedButton.clicked.connect(self.previousLed)
        self.a = anatomist.Anatomist('-b') #Batch mode (hide Anatomist window)
        self.a.onCursorNotifier.add(self.clickHandler)
        

        
        self.axWindow = self.a.createWindow( 'Axial' )
        
        layoutAx = QtGui.QHBoxLayout( self.frame )        
        self.axWindow.setParent(self.frame)
        layoutAx.addWidget( self.axWindow.getInternalRep() )
        self.currentElec = 0
        self.coords = [[0,0,0],]
        
    def loadMesh(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Mesh", "", "All meshes(*.gii *.mesh)"))
        if not path:
            return
        obj = self.a.loadObject(path)
        pdb.set_trace()
        self.a.addObjects(obj, self.axWindow)
        self.mesh = obj
        
    def start(self):
        """Light up the first led"""
        self.coords = [[0,0,0],]
        self.currentElect = 0
        self.ui.currentLedLabel.setText("current LED : %i"%self.currentElec)
        self.pb.open()
        self.pb.lightOne(0)
        self.currentElec = 0
        self.dispCoords(self.coords[self.currentElec])
        
    def updatedDeviceCombo(self):
        print("no done yet")
    
    def nextLed(self):
        self.currentElec = self.currentElec + 1
        self.ui.currentLedLabel.setText("current LED : %i"%self.currentElec)
        
        if self.currentElec >= len(self.coords):
            self.coords.append([0,0,0])
            
        self.dispCoords(self.coords[self.currentElec])
        self.pb.lightOne(self.currentElec)
    
    def previousLed(self):
        if self.currentElec == 0:
            return
        self.currentElec = self.currentElec - 1
        self.ui.currentLedLabel.setText("current LED : %i"%self.currentElec)
        self.dispCoords(self.coords[self.currentElec])
        self.pb.lightOne(self.currentElec)
    
    def clickHandler(self, eventName, params):
        coords = self.a.linkCursorLastClickedPosition().items()
        self.dispCoords(coords)
        self.coords[self.currentElec] = coords
        
    def dispCoords(self, coords):
        self.ui.currentCoordsLabel.setText("Coords: "+ repr(["%.02f"%coords[x] for x in [0,1,2]]))
    
    def save(self):
        path = str(QtGui.QFileDialog.getSaveFileName(self, "Save LED location", "", "LED location (*.leds)"))
        if not path:
            return
        # If there is no extension, add the standard one !
    
        if os.path.splitext(path)[1] == '':
            path = path+'.leds'

        fileout = open(path, 'wb')
        fileout.write(json.dumps({'leds':self.coords, 'timestamp':time.time()}))
        fileout.close()

    def load(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open LED location", "", "All led locations(*.leds)"))

        if not path:
            return
        # Check if we have a PTS/TXT/elecimplant file
        filein = open(path, 'rb')
        dic = json.loads(filein.read())
        filein.close()
        if not 'leds' in dic:
            print("Could not find leds in file")
            return
        else:
            self.currentElec = 0
            self.coords = dic['leds']
     
def main(noapp=0):
     app = None
     if noapp == 0:
      print "NO APP"
      app = QtGui.QApplication(sys.argv)
      axon.initializeProcesses()
      ll = LocateLeds(app=app)
      ll.show()      
     
     if noapp == 0:
      sys.exit(app.exec_())
  

if __name__ == "__main__":

     QtCore.pyqtRemoveInputHook()
     main()

            