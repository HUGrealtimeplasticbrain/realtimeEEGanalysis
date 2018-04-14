#
# LED setup editor for PlasticBrain
#
# (c) 2017 Manik Bhattacharjee
#

from PyQt4.QtWidgets import QDialog, QApplication, QFileDialog, QMessageBox
from PyQt4 import uic, QtCore
import plasticbrain
from brainvisa import anatomist
import json, time

class LocateLeds(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.ui = uic.loadUi("locateleds.ui", self)
        self.pb = plasticbrain.PlasticBrain()
        self.ui.startButton.clicked.connect(self.start)
        self.a = anatomist.Anatomist('-b') #Batch mode (hide Anatomist window)
        self.a.onCursorNotifier.add(self.clickHandler)
        self.axWindow = self.a.createWindow( 'Axial' )
        self.axWindow.setParent(self.frame)
        self.ui.frame.layout().addWidget( self.axWindow.getInternalRep() )
        self.currentElec = 0
        self.coords = [[0,0,0],]
        
    def loadMesh(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Mesh", "", "All meshes(*.gii *.mesh)"))
        if not path:
            return
        obj = self.a.loadObject(path)
        self.a.addObjects(obj, self.axWindow)
        
    def start(self):
        """Light up the first led"""
        self.pb.lightOne(0)
        self.currentElec = 0
        self.dispCoords(self.coords[self.currentElec])
    
    def next(self):
        self.currentElec = self.currentElec + 1
        if self.currentElec >= len(self.coords):
            self.coords.append([0,0,0])
        self.dispCoords(self.coords[self.currentElec])
        self.pb.lightOne(self.currentElec)
    
    def previous(self):
        if self.currentElec == 0:
            return
        self.currentElec = self.currentElec - 1
        self.dispCoords(self.coords[self.currentElec])
        self.pb.lightOne(self.currentElec)
    
    def clickHandler(self, eventName, params):
        coords = self.a.linkCursorLastClickedPosition().items()
        self.dispCoords(coords)
        self.coords[self.currentElec] = coords
        
    def dispCoords(self, coords):
        self.ui.currentCoordsLabel.setText("Coords: "+repr(coords))
    
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
            
            