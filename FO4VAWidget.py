import os
from PyQt5 import  QtCore, uic
import socketserver
from .. import widgets


class FO4VaWidget(widgets.WidgetBase):
    _signalPipWorldLocationsUpdated = QtCore.pyqtSignal()

    def __init__(self, mhandle, parent):
        super().__init__('FO4VA', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'fo4va.ui'))
        self.widget.btnStart.clicked.connect(self._startserver)
        self.setWidget(self.widget)
        self.FO4Connected = False
        self._locations_dict = {}

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)

    def _onPipRootObjectEvent(self, rootObject):
        self.rootObject = rootObject
        self.pipMapObject = rootObject.child('Map')
        self.pipMapWorldObject = self.pipMapObject.child('World')
        self.FO4Connected = True
        if self.pipMapWorldObject:
            self.pipWorldLocations = self.pipMapWorldObject.child('Locations')

    def _startserver(self):
        if self.FO4Connected:
            self.server = socket_server("localhost",8089,  self.rootObject , self.dataManager)
            self.server.start()
        else:
            print("Not Connected")



class MyTCPHandler(socketserver.BaseRequestHandler):


    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        return_message = ""
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        self.SafeMode = True
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        sName_Raw = str(self.data.decode()).split(';')
        sCommand = sName_Raw[0]

        print("Command =%s" %(sCommand))
        sName = sName_Raw[1]
        print (self.server.pipRootObj)
        if sCommand == '1':
            print('Fastravel')
            self.sSafeMode = False
            return_message =  self.VAFastTravel(sName)
        elif sCommand == '2':
            print("Directions")
            return_message = self.GetDirections(sName)
        if not return_message:
            return_message = 'Error'
        # just send back the same data, but upper-cased
        self.request.sendall(return_message.encode('utf-8'))
        self.request.close()

    def VAFastTravel(self, sName):
            strFound = False
            if self.server.pipRootObj:
                pipMapObject = self.server.pipRootObj.child('Map')
                pipMapWorldObject = pipMapObject.child('World')
                if pipMapWorldObject:
                    pipWorldLocations = pipMapWorldObject.child('Locations')
                    if pipWorldLocations:
                        print(sName)
                        for k in pipWorldLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                                        print('curKey ' + str(curKey))
                if strFound:
                    curPoint = pipWorldLocations.child(curKey)
                    print("curPoint = %s" % curPoint)
                    discovered = pipWorldLocations.child(curKey).child('Discovered').value()
                    print(curPoint.pipId)
                    print("discovered =%s" % discovered)
                    if discovered:
                        print("True")

                        self.server.pipDataManager.rpcFastTravel(curPoint)
                        self.data = "Fast Travel Location " + sName + " Successful"
                    else:
                        print("False")
                        self.data = "Location " + sName + " Has Not Been Discovered yet"
                else:
                   self.data = "Fast Travel Location " + sName + " unSuccessful"
                return self.data

    def GetDirections(self, sName):
        strFound = False
        if self.server.pipRootObj:
                pipMapObject = self.server.pipRootObj.child('Map')
                pipMapWorldObject = pipMapObject.child('World')
                if pipMapWorldObject:
                    pipWorldLocations = pipMapWorldObject.child('Locations')
                    pipPlayerLocation = pipMapWorldObject.child('Player')
                    print("Direction to %s" % sName)
                    for k in pipWorldLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                                        print('curKey ' + str(curKey))
                if strFound:
                    ToLocation = pipWorldLocations.child(curKey)
                    PlayerY = float(pipPlayerLocation.child('Y').value())
                    PlayerX = float(pipPlayerLocation.child('X').value())
                    LocationX =float(ToLocation.child('X').value()) #18232.314453125
                    LocationY = float(ToLocation.child('Y').value())#14378.2109375
                    print("pipPlayerLocation is % s" % pipPlayerLocation.child('Y').value())

                    from math import degrees, atan2

                    angle = degrees(atan2(LocationY - PlayerY, LocationX - PlayerX))
                    bearing1 = (angle + 360) % 360
                    bearing2 = (90 - angle) % 360
                    print ("gb: x=%2d y=%2d angle=%6.1f bearing1=%5.1f bearing2=%5.1f" % (
                        PlayerX, PlayerY, angle, bearing1, bearing2))
                    dirs = ["North", "North by northEast", "North East", "East by NorthEast", "East", "East by SouthEast", "SouthEast", "South by SsouthEast",
                     "Ssouth", "South by SsouthWest", "SouthWest", "West by SsouthWest", "West", "WestNorthWest", "NorthWest", "North by NorthWest"]
                    ix = int((bearing2 + 11.25)/22.5)
                    compass_direction = (dirs[ix % 16])
                    return compass_direction


class MiddelWareServer(socketserver.TCPServer):

    # This class just here to store values to be passed along to handler
    def __init__(self, server_address, RequestHandlerClass, pipObj, pipDataManager):
        socketserver.ThreadingTCPServer.__init__(self,
                                                 server_address,
                                                 RequestHandlerClass)
        self.pipRootObj = pipObj
        self.pipDataManager = pipDataManager



class socket_server(QtCore.QThread):
    def __init__(self, host, port, pipObj, pipDataManager):
        QtCore.QThread.__init__(self)
        self.HOST = host
        self.PORT = port
        self.pipObj = pipObj
        self.pipDataManager = pipDataManager

    def __del__(self):
        self.wait()

    def run(self):
        server = MiddelWareServer((self.HOST, self.PORT), MyTCPHandler, self.pipObj, self.pipDataManager)
        server.serve_forever()


