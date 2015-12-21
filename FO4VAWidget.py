import os
from PyQt5 import  QtCore, uic, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import socketserver
from .. import widgets
from widgets.shared import settings
class FO4VaWidget(widgets.WidgetBase):
    _signalPipWorldLocationsUpdated = QtCore.pyqtSignal()

    def __init__(self, mhandle, parent):
        super().__init__('FO4VA', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'fo4va.ui'))
        self.widget.btnStart.clicked.connect(self._startserver)
        self.widget.chkStart.clicked.connect(self.autoConnectToggled)
        self.settings = settings
        self.setWidget(self.widget)
        self.FO4Connected = False
        self.serverRun = False
        self._locations_dict = {}

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self._app = app
        if self._app.settings.value('FO4VaWidget/lasthost'):
            host = self._app.settings.value('FO4VaWidget/lasthost')
        if self._app.settings.value('FO4VaWidget/lastport'):
            port = self._app.settings.value('FO4VaWidget/lastport')
        if int(self._app.settings.value('FO4VaWidget/autoconnect', 0)):
            self.widget.chkStart.setChecked(True)
            self.autoStart = True
        self.widget.txtIP.setText(host)
        self.widget.txtPort.setText(str(port))

    @QtCore.pyqtSlot(bool)
    def autoConnectToggled(self, value):
       self._app.settings.setValue('FO4VaWidget/autoconnect', int(value))

    def _onPipRootObjectEvent(self, rootObject):
        self.rootObject = rootObject
        self.FO4Connected = True
        if self.autoStart:
            self._startserver()


    def _startserver(self):
        if not self.serverRun :
            if self.FO4Connected:
                try:
                    host = self.widget.txtIP.text()
                    port = int(self.widget.txtPort.text())
                    print('port = %s' % port)

                    self.server = socket_server(host, port,  self.rootObject , self.dataManager)
                    self.server.start()
                    self.serverRun = True

                except ValueError as e:
                    QtWidgets.QMessageBox.warning(self, 'Connection to host failed',
                            'Caught exception while parsing port: ' + str(e),
                            QtWidgets.QMessageBox.Ok)
                self._app.settings.setValue('FO4VaWidget/lastport',str(port))
                self._app.settings.setValue('FO4VaWidget/lasthost',str(host))
            else:
                QtWidgets.QMessageBox.about(self, 'Error!',
                                            "Must Connect to Fallout 4 first")
        else:
            QtWidgets.QMessageBox.about(self, 'Error!',
                                            "Server is Already Running")


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
        sName_Raw = str(self.data.decode()).split(';')
        sCommand = sName_Raw[0]
        sName = sName_Raw[1]
        print (self.server.pipRootObj)
        if sCommand == 'FastTravel':
            self.sSafeMode = False
            return_message =  self.VAFastTravel(sName)
        elif sCommand == 'Directions':
            return_message = self.GetDirections(sName, 'LocationDirections')
        elif sCommand == 'QuestDirections':
            return_message = self.GetDirections(sName, 'QuestDirections')
        elif sCommand == 'MonitorHP':
            self.MonitorHP()
        if not return_message:
            return_message = 'Error'
        self.request.sendall(return_message.encode('utf-8'))
        self.request.close()

    def MonitorHP(self):
        """Just a WIP
        """
        if self.server.pipRootObj:
            pipPlayerObject = self.server.pipRootObj.child('PlayerInfo')
            if pipPlayerObject:
                currHp = pipPlayerObject.child('CurrHP')
            if currHp:
                print('Current Health: ', currHp.value())
                return currHp

    def VAFastTravel(self, sName):
            """
                 Takes the sent map location name(sName) and issues fast travel rpc command to go there
                And returns a stauts message to VA
            Args:
                sName:

            Returns:

            """
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



    def GetDirections(self, sName, sType):
        """
        Args:
            sName: Name of location or quest sent from VA
            sType: either LocationDirections or QuestDirections to determine type of location lookup

        Returns:
            compass_direction in a english response
        """
        strFound = False
        if self.server.pipRootObj:
                pipMapObject = self.server.pipRootObj.child('Map')
                pipMapWorldObject = pipMapObject.child('World')
                if pipMapWorldObject:
                    pipPlayerLocation = pipMapWorldObject.child('Player')
                    if sType == "LocationDirections":
                        pipLocations = pipMapWorldObject.child('Locations')
                    elif sType == "QuestDirections":
                        pipLocations = pipMapWorldObject.child('Quests')
                    print("Direction to %s" % sName)
                    for k in pipLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                                        print('curKey ' + str(curKey))
                if strFound:
                    ToLocation = pipLocations.child(curKey)
                    PlayerY = float(pipPlayerLocation.child('Y').value())
                    PlayerX = float(pipPlayerLocation.child('X').value())
                    LocationX =float(ToLocation.child('X').value()) #18232.314453125
                    LocationY = float(ToLocation.child('Y').value())#14378.2109375

                    from math import degrees, atan2

                    angle = degrees(atan2(LocationY - PlayerY, LocationX - PlayerX))
                    bearing = (90 - angle) % 360
                    dirs = ["North", "North by northEast", "North East", "East by NorthEast", "East", "East by SouthEast", "SouthEast", "South by SsouthEast",
                     "Ssouth", "South by SsouthWest", "SouthWest", "West by SsouthWest", "West", "WestNorthWest", "NorthWest", "North by NorthWest"]
                    ix = int((bearing + 11.25)/22.5)
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


