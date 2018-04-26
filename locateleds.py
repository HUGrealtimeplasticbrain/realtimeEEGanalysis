#
# LED setup editor for PlasticBrain
#
# (c) 2017 Manik Bhattacharjee
#


import plasticbrain
import sys
from soma import aims, aimsalgo
from brainvisa import axon

from brainvisa.configuration import neuroConfig
neuroConfig.gui = True
from brainvisa import anatomist
import anatomist.direct.api as anatomistControl
import json, time
import pdb
import os
from scipy import spatial
import numpy as np

from soma.qt_gui.qt_backend import uic, QtGui, QtCore
from soma.qt_gui.qt_backend.QtCore import QThread

from pylsl import StreamInlet, resolve_stream, resolve_byprop
import scipy.io
import scipy.signal

class MyAction( anatomistControl.cpp.Action ):
    def name( self ):
      return 'MyAction'
  
    def activateVirtualLed( self, x, y, globx, globy ):
        
        print 'coucou', x,y

        w = self.view().aWindow()
        obj = w.objectAtCursorPosition( x, y )
        if obj is not None:
          print 'object:', obj, obj.name()
          poly = w.polygonAtCursorPosition( x, y, obj )
          mesh = anatomistControl.cpp.AObjectConverter.aims( obj )
          
          if poly == 0xffffff or poly < 0 or poly >= len( mesh.polygon() ):
              return
          #print 'polygon:', poly

          #print 'mesh:', mesh
          ppoly = mesh.polygon()[poly]
          vert = mesh.vertex()

          #print 'poly:', poly, ppoly
          pos = aims.Point3df()
          pos = w.positionFromCursor( x, y )
          #print 'pos:', pos
          v = ppoly[ np.argmin( [ (vert[p]-pos).norm() for p in ppoly ] ) ]
          print 'vertex:', v, vert[v]
          
          



class MyControl( anatomistControl.cpp.Control ):
  def __init__( self, prio = 25 ):
    anatomistControl.cpp.Control.__init__( self, prio, 'MyControl' )
    
  def eventAutoSubscription( self, pool ):

    key = QtCore.Qt
    NoModifier = key.NoModifier
    ShiftModifier = key.ShiftModifier
    ControlModifier = key.ControlModifier
    AltModifier = key.AltModifier
  
    self.mousePressButtonEventSubscribe(key.LeftButton, NoModifier,
      pool.action( 'MyAction' ).activateVirtualLed )

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
        self.ui.ReceiveLSLButton.clicked.connect(self.ReceiveAndDisplayEEG)
        self.a = anatomist.Anatomist('-b') #Batch mode (hide Anatomist window)
        self.a.onCursorNotifier.add(self.clickHandler)
        pix = QtGui.QPixmap( 'control.xpm' )
        
        anatomistControl.cpp.IconDictionary.instance().addIcon( 'MyControl',pix )
        ad = anatomistControl.cpp.ActionDictionary.instance()
        ad.addAction( 'MyAction', lambda: MyAction() )
        cd = anatomistControl.cpp.ControlDictionary.instance()
        cd.addControl( 'MyControl', lambda: MyControl(), 25 )
        cm = anatomistControl.cpp.ControlManager.instance()
        cm.addControl( 'QAGLWidget3D', '', 'MyControl' )

        
        self.axWindow = self.a.createWindow( 'Axial' )
        
        layoutAx = QtGui.QHBoxLayout( self.frame )        
        self.axWindow.setParent(self.frame)
        layoutAx.addWidget( self.axWindow.getInternalRep() )
        self.currentElec = 0
        self.coords = [[0,0,0],]
        self.mesh = None
        self.texture = None
        self.currentObj = None
        self.TextObj = None
        
    def loadMesh(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Mesh", "", "All meshes(*.gii *.mesh)"))
        if not path:
            return
        
        
        obj = self.a.loadObject(path)
        #self.a.addObjects(obj, self.axWindow)
        self.mesh = obj
        texture = aims.TimeTexture('S16')
        texture2 = aims.TimeTexture('FLOAT')
        AimsMesh = self.mesh.toAimsObject()
        #gp = aims.GeodesicPath(AimsMesh, 0, 0)
        newTextureObj = texture[0]  
        newTextureObj.reserve(len(AimsMesh.vertex()))
        newTextureObj2 = texture2[0]  
        newTextureObj2.reserve(len(AimsMesh.vertex()))        
        self.texture=texture
        self.texture2=texture2
        
        
        self.texture2[0].assign([0]*len(AimsMesh.vertex()))
        if self.TextObj is None:
          self.TextObj=self.a.toAObject(self.texture2)
          self.TextObj.setPalette(palette = "RED-ufusion")

          newFusionObj = self.a.fusionObjects([self.mesh, self.TextObj], method='FusionTexSurfMethod')
        #set palette to Blue-Red-fusion_invert
          self.a.addObjects(newFusionObj,self.axWindow)
          self.currentObj=newFusionObj        
        
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
        
        #   pdb.set_trace()
        coords = params['position'][:3]
        #coords = self.a.linkCursorLastClickedPosition().items()
        if self.mesh is not None:
            #self.updateMeshTexture(coords)
            
            win = params['window']
            pos2d = aims.Point3df()
            win.view().cursorFromPosition(coords, pos2d)
            x, y = pos2d[:2]
            obj = win.objectAtCursorPosition(x, y)
            MeshObj=[iterobj for iterobj in obj if iterobj==self.mesh]
            
            if len(MeshObj)>0: #obj == self.currentObj:
                
                mesh = self.a.toAimsObject(self.mesh)
                poly = win.polygonAtCursorPosition(x, y, self.currentObj)
                if poly != 0xffffff and poly >= 0 and poly < len(mesh.polygon()):
                    ppoly = mesh.polygon()[poly]
                    vert = mesh.vertex()
                    v = ppoly[np.argmin([(vert[p]-coords).norm() for p in ppoly])]
                    self.updateMeshTexture(v,mesh)
                    
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
            
    def updateMeshTexture(self,center,AimsMesh):
        

        self.texture[0].assign([0]*len(AimsMesh.vertex()))
        self.texture[0][center] = 12
        self.texture2 = aims.meshdistance.MeshDistance(AimsMesh, self.texture, True)
        self.texture2[0].arraydata()[np.where(self.texture2[0].arraydata()>=15)]=0
        #if self.TextObj is None:
        #  self.TextObj=self.a.toAObject(self.texture2)
        #  self.TextObj.setPalette(palette = "RED-ufusion")

        #  newFusionObj = self.a.fusionObjects([self.mesh, self.TextObj], method='FusionTexSurfMethod')
        #set palette to Blue-Red-fusion_invert
        #  self.a.addObjects(newFusionObj,self.axWindow)
        #  self.currentObj=newFusionObj
        #else:
        self.TextObj.setTexture(self.texture2,True)
        self.TextObj.notifyObservers()
        
        #find all vertex within 2 cm geodesic distance
        
        #AimsTextureRegularization c'est quoi ca deja ?
        #AimsTextureDilation
        #AimsTextureErosion
        #VipDistanceMap
        
    def ReceiveAndDisplayEEG(self):
        
        if self.currentObj is None:
            print("no mesh")
            return
        try:
            invMat = scipy.io.loadmat('/home/neuropsynov/hugHackathon/MNI_actiCHamp64.mat')
        except:
            print("can't open the inv mat")
            return
        print("looking for an EEG stream...")
        streams = resolve_byprop('type', 'EEG',timeout=5.0)
        if len(streams)==0:
            print("no eeg signal found")
            return
        
        #check number of contact match invMat size
        if streams[0].channel_count() != invMat["x"].shape[1]:
            print("invMat and channel_count doesn't match")
        
        sefl.EEGAnalysisParam = {}
        nyq=0.5*streams[0].nominal_srate()
        low = 1 / nyq
        high = 81 / nyq
        paramFil = scipy.signal.butter(6, [low, high], btype='band')
        
    
        while True:
            print("coucou")
        
        pdb.set_trace()
     
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

            