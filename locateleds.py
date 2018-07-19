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
import math

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
        self.ui.StopReceiveData.clicked.connect(self.StopReceiveData)
        self.a = anatomist.Anatomist('-b') #Batch mode (hide Anatomist window)
        self.a.onCursorNotifier.add(self.clickHandler)
        pix = QtGui.QPixmap( 'control.xpm' )
        self.app =app
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
        self.aimsMesh = None
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
        self.aimsMesh = None
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
        self.VertexLed = []
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
                
                if self.aimsMesh is None:
                    self.aimsMesh = self.a.toAimsObject(self.mesh)

                poly = win.polygonAtCursorPosition(x, y, self.currentObj)
                if poly != 0xffffff and poly >= 0 and poly < len(self.aimsMesh.polygon()):
                    ppoly = self.aimsMesh.polygon()[poly]
                    vert = self.aimsMesh.vertex()
                    v = ppoly[np.argmin([(vert[p]-coords).norm() for p in ppoly])]
                    self.updateMeshTexture(v,self.aimsMesh)
                    
        self.dispCoords(coords)
        self.coords[self.currentElec] = coords
#j'en suis la
        intermediaire = self.texture2[0].arraydata()
        intermediaire[np.where(intermediaire>=15)]=0
        self.VertexLed.append()
        
        
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
        
    def StopReceiveData(self):
        
        self.mustStop = True
    
    def ReceiveAndDisplayEEG(self,lowfreq=1,highfreq=81,band=[10,20]):
        
        if self.currentObj is None:
            print("no mesh")
            return
        try:
            invMat = scipy.io.loadmat('/home/neuropsynov/hugHackathon/Manik_actiCHamp64_5000.mat')
        except:
            print("can't open the inv mat")
            return
        
        try:
            spi2gii = np.load('/home/neuropsynov/hugHackathon/spi2fullGii.npy')
        except:
            print("can't open the spi2gii file")
            return
        
        print("looking for an EEG stream...")
        streams = resolve_byprop('type', 'EEG',timeout=5.0)
        if len(streams)==0:
            print("no eeg signal found")
            return
        
        #check number of contact match invMat size
        if streams[0].channel_count() != invMat["x"].shape[1]:
            print("invMat and channel_count doesn't match")
        
        #check if we have EOG for eye artefact removal
        
        
        #prepare the texture object
        if self.aimsMesh is None:
            self.aimsMesh = self.a.toAimsObject(self.mesh)
        
        self.texture[0].assign([0]*len(self.aimsMesh.vertex()))
        
        currentIndex=0
        buffSize=500
        buff = np.zeros([buffSize, streams[0].channel_count()])
        
        #est-ce qu'on fait un buffer "normalisation" avec le signal en degageant du signal tout ce qui est >5 la MAD ?
        
        self.EEGAnalysisParam = {}
        nyq=0.5*streams[0].nominal_srate()
        low = lowfreq / nyq
        high = highfreq / nyq
        paramFil = scipy.signal.butter(6, [low, high], btype='band')
        
        # create a new inlet to read from the stream
        inlet = StreamInlet(streams[0])
        self.mustStop = False
        self.TextObj.setPalette(palette = 'Blue-Red')
    
        while not self.mustStop:
            print(currentIndex)
            np.roll(buff, -1, 0)
            buff[buffSize - 1, :], timestamp = inlet.pull_sample()
            
            if currentIndex>=500:
                filtSample = scipy.signal.filtfilt(paramFil[0],paramFil[1],buff,method="gust",axis=0)
                #il faudrait faire une fastICA ici
            
                
                #on prend juste le milieu du signal ?
                f_welch, S_xx_welch=scipy.signal.welch(filtSample[math.floor(buffSize/4):math.floor(buffSize/4)*3,:],fs=streams[0].nominal_srate(),nfft=math.floor(2*streams[0].nominal_srate()/2.5),nperseg=math.floor(streams[0].nominal_srate()/5.0),axis=0,scaling="density")
                
                freqKept=(f_welch >= band[0]) & (f_welch <= band[1])
            
                
                DataToProject= np.mean(S_xx_welch[freqKept,:],axis=0)
                #DataToProject = buff[250,:]
                invsolmat = np.sqrt(np.multiply(np.dot(invMat["x"],DataToProject),np.dot(invMat["x"],DataToProject)) + np.multiply(np.dot(invMat["y"],DataToProject),np.dot(invMat["y"],DataToProject)) + np.multiply(np.dot(invMat["z"],DataToProject),np.dot(invMat["z"],DataToProject)))
                #if currentIndex % 500 == 0:
                #   plt.plot(filtSample[:,5], 'b-')
                #   plt.plot(buff[:,5], 'r-')
                #   plt.show()
                fullTexture = np.dot(spi2gii,invsolmat)
                self.texture2[0].assign(fullTexture)
                self.TextObj.setTexture(self.texture2,True)
                self.TextObj.notifyObservers()
                self.app.processEvents()
                
                
                #mapping avec les leds
                
            
            currentIndex += 1
        
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

            