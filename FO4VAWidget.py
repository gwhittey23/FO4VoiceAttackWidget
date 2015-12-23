import os
from PyQt5 import  QtCore, uic, QtWidgets
import socketserver
from PyPipboyApp.widgets import widgets
from widgets.shared import settings

class FO4VaWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()

    def __init__(self, mhandle, parent):
        super().__init__('FO4VAWidget', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'fo4va.ui'))
        self.widget.btnStart.clicked.connect(self._startserver)
        self.widget.btnStop.clicked.connect(self._stopserver)
        self.widget.chkStart.clicked.connect(self.autoConnectToggled)
        self.settings = settings
        self.setWidget(self.widget)
        self.FO4Connected = False
        self.autoStart = False
        self.pipInventoryInfo = None
        self.pipRadioInfo = None
        self.serverThread = False
        self._signalInfoUpdated.connect(self._slotInfoUpdated)

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self._app = app
        host = "127.0.0.1"
        port = 8089
        if self._app.settings.value('FO4VaWidget/lasthost'):
            host = self._app.settings.value('FO4VaWidget/lasthost')
        if self._app.settings.value('FO4VaWidget/lastport'):
            port = self._app.settings.value('FO4VaWidget/lastport')
        if int(self._app.settings.value('FO4VaWidget/autoconnect', 0)):
            self.widget.chkStart.setChecked(True)
            self.autoStart = True
        self.widget.txtIP.setText(host)
        self.widget.txtPort.setText(str(port))
        self.networkchannel = datamanager.networkchannel
        self.networkchannel.registerConnectionListener(self._onConnectionStateChange)


    @QtCore.pyqtSlot(bool)
    def autoConnectToggled(self, value):
        self._app.settings.setValue('FO4VaWidget/autoconnect', int(value))

    def _onPipRootObjectEvent(self, rootObject):
        self.rootObject = rootObject
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self.pipRadioInfo = rootObject.child('Radio')
        if self.pipRadioInfo:
            self.pipRadioInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 2)
        self._signalInfoUpdated.emit()

        if self.autoStart:
            self._startserver()
        pass

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()

    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.serverThread._onUpdate(self.rootObject)



    def _onConnectionStateChange(self, state, errstatus, errmsg):
        if state:
            self.FO4Connected = True
        else:
            if errstatus != 0:
                self._stopserver()
                self.FO4Connected = False
            else:
                self.FO4Connected = False
                self._stopserver()

    def _startserver(self):
        if not self.serverThread:
            if self.FO4Connected:
                try:
                    host = self.widget.txtIP.text()
                    port = int(self.widget.txtPort.text())
                    self.serverThread = socket_serverThread(host, port,  self.rootObject , self.dataManager)
                    self.serverThread.start()
                    self.widget.lblServerState.setText("Server is On")
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

    def _stopserver(self):
        self.serverThread._onShutdown()
        self.serverThread.terminate()
        self.widget.lblServerState.setText("Server is Off")
        self.serverThread = False


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
        print(self.data)
        sCommand = sName_Raw[0]
        sName = sName_Raw[1]
        if sCommand == 'FastTravel':
            self.sSafeMode = False
            return_message = self.vaFastTravel(sName)
        elif sCommand == 'Directions':
            return_message = self.getDirections(sName, 'LocationDirections')
        elif sCommand == 'QuestDirections':
            return_message = self.getDirections(sName, 'QuestDirections')
        elif sCommand == 'MonitorHP':
            self.monitorHP()
        elif sCommand == "RadioToggle":
            return_message = self.radioControl(sName, 'ToggleRadio')
        elif sCommand == "ChangeStation":
            return_message = self.radioControl(sName, 'ChangeStation')
        elif sCommand == "NextStation":
            return_message = self.radioControl(sName, 'NextStation')
        elif sCommand == "EquipWeapon":
            return_message = self.useItemByName('43', sName)
        elif sCommand == "NextGrenade":
            return_message = self.grenadeControl(sName, 'NextGrenade')
        elif sCommand == 'GrenadeEquip':
            self.grenadeControl(sName, 'GrenadeEquip')
        else:
            return_message = "Could not process SentCommand %s" % sCommand
        if not return_message:
            return_message = 'Error'
        self.request.sendall(return_message.encode('utf-8'))
        self.request.close()

    def monitorHP(self):
        """Just a WIP
        """
        if self.server.pipRootObj:
            pipPlayerObject = self.server.pipRootObj.child('PlayerInfo')
            if pipPlayerObject:
                currHp = pipPlayerObject.child('CurrHP')
            if currHp:
                print('Current Health: ', currHp.value())
                return currHp

    def vaFastTravel(self, sName):
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
                        for k in pipWorldLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                if strFound:
                    curPoint = pipWorldLocations.child(curKey)
                    discovered = pipWorldLocations.child(curKey).child('Discovered').value()
                    if discovered:
                        self.server.pipdataManager.rpcFastTravel(curPoint)
                        data = "Fast Travel Location " + sName + " Successful"
                    else:
                        data = "Location " + sName + " Has Not Been Discovered yet"
                else:
                   data = "Fast Travel Location " + sName + " unSuccessful"
                return data

    def getDirections(self, sName, sType):
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
                    for k in pipLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                if strFound:
                    ToLocation = pipLocations.child(curKey)
                    PlayerY = float(pipPlayerLocation.child('Y').value())
                    PlayerX = float(pipPlayerLocation.child('X').value())
                    LocationX =float(ToLocation.child('X').value()) #18232.314453125
                    LocationY = float(ToLocation.child('Y').value())#14378.2109375

                    from math import degrees, atan2,hypot

                    angle = degrees(atan2(LocationY - PlayerY, LocationX - PlayerX))
                    bearing = (90 - angle) % 360
                    dirs = [
                            "North", "North by northEast", "North East", "East by NorthEast", "East",
                            "East by SouthEast", "SouthEast", "South by SouthEast", "South", "South by SouthWest",
                            "SouthWest", "West by SouthWest", "West", "WestNorthWest", "NorthWest", "North by NorthWest"
                            ]
                    ix = int((bearing + 11.25)/22.5)
                    dist = hypot(LocationX - PlayerX, LocationY - PlayerY)
                    compass_direction = (dirs[ix % 16])
                    rtMessage = compass_direction
                    return rtMessage




    def radioControl(self, newstation, stype):
        """Modified Code from hotkey.py  credit goes to  akamal """
        data = ""
        self.currentRadioStation = None
        self.availableRadioStations = []
        self.newstation = newstation
        if self.server.pipRootObj:
            self.pipRadioObject =  self.server.pipRootObj.child('Radio')
            if (self.pipRadioObject):
                for i in range(0, self.pipRadioObject.childCount()):
                    station = self.pipRadioObject.child(i)
                    if station.child('inRange').value():
                        self.availableRadioStations.append(station)
                    if station.child('active').value():
                        self.currentRadioStation = station

                if stype == 'ToggleRadio':
                     data = self.toggleRadio()
                elif stype == 'ChangeStation':
                    data = self.changeStation()
                elif stype == 'NextStation':
                    data = self.nextStation()

        return data

    def changeStation(self):
        """
            -Changes station to newstation
        """
        strFound = False
        if self.pipRadioObject:
            for k in self.pipRadioObject.value():
                for x in k.value():
                    if x == 'text':
                        curName = k.child(x).value()
                        if curName.lower() == self.newstation.lower():
                            curKey = k.pipParentKey
                            strFound = True
        if strFound:

            curStation = self.pipRadioObject.child(curKey)
            inRange = self.pipRadioObject.child(curKey).child('inRange').value()
            if inRange:
                self.server.pipdataManager.rpcToggleRadioStation(curStation)
                data = "Tune to " + self.newstation + " Successful"
            else:
                data = "Staion " + self.newstation + " is not in range"
        else:
            data = "Tune to " + self.newstation + " unSuccessful"
        return data

    def toggleRadio(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        if (self.currentRadioStation):
                data = ('toggleRadio: currentstation: ' + self.currentRadioStation.child('text').value())
                self.server.pipdataManager.rpcToggleRadioStation(self.currentRadioStation)
        else:
            data = ('toggleRadio: no current, trying station First aviable station')
            numStations = len(self.availableRadioStations)
            if numStations > 0:
                self.server.pipdataManager.rpcToggleRadioStation(self.availableRadioStations[0])
        return data
    def nextStation(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        getIndex = 0
        numStations = len(self.availableRadioStations)
        if self.currentRadioStation:
            txtResponse =('nextRadio: currentstation: ' + self.currentRadioStation.child('text').value())
            for i in range (0, numStations):
                if self.availableRadioStations[i].child('text').value() == self.currentRadioStation.child('text').value():
                    getIndex = i + 1
                    break

        if (getIndex >= numStations):
            getIndex = 0

        if (getIndex <= numStations):
            txtResponse =('tuning radio to: ' + self.availableRadioStations[getIndex].child('text').value())
            self.server.pipdataManager.rpcToggleRadioStation(self.availableRadioStations[getIndex])

        return txtResponse

    def grenadeControl(self, sName, stype):
        data = ""
        if self.server.pipRootObj:
            self.pipInventoryInfo = self.pipInventoryInfo = self.server.pipRootObj.child('Inventory')
            if (self.pipInventoryInfo):
                self.server.availableGrenades = []
                weapons = self.pipInventoryInfo.child('43')
                if(not weapons):
                    return
                for i in range(0, weapons.childCount()):
                    equipped = False
                    name = weapons.child(i).child('text').value()
                    if (name.lower().find('mine') > -1 or
                        name.lower().find('grenade') > -1 or
                            name.lower().find('molotov') > -1):
                        count = str(weapons.child(i).child('count').value())
                        if (weapons.child(i).child('equipState').value() == 3):
                            equipped = True
                            self.server.lastEquippedGrenade = name.lower()
                        self.server.availableGrenades.append([name.lower(), equipped])
                if stype == 'NextGrenade':
                    data = self.equipNextGrendae()
                elif stype == 'GrenadeEquip':
                    data = self.useItemByName('43', sName)
        return data

    def equipNextGrendae(self):
        """Modified Code from hotkey.py  credit goes to  akamal """

        nextIndex = -1
        lastIndex = -1
        self.server.availableGrenades.sort()
        numGrenades = len(self.server.availableGrenades)
        if (numGrenades > 0):
            for i in range(0, numGrenades):
                if (self.server.availableGrenades[i][1]):
                    nextIndex = i + 1
                    break
                if (self.server.availableGrenades[i][0] == self.server.lastEquippedGrenade):
                    lastIndex = i
            if (nextIndex == numGrenades):
                nextIndex = 0

            if (nextIndex < 0 and lastIndex >= 0):
                nextIndex = lastIndex

            if(nextIndex < 0):
                nextIndex = 0

            self.useItemByName("43", self.server.availableGrenades[nextIndex][0])
            data = self.server.availableGrenades[nextIndex][0]
        else:
            data = 'You have no grenades in your inventory'
        return data


    def useItemByName(self,inventorySection, itemName):
        """Modified Code from hotkey.py  credit goes to  akamal """
        if self.server.pipRootObj:
            self.server.pipInventoryInfo = self.server.pipRootObj.child('Inventory')
            itemName = itemName.lower()
            if (self.server.pipInventoryInfo):
                inventory = self.server.pipInventoryInfo.child(inventorySection)
                for i in range(0, inventory.childCount()):
                    name = inventory.child(i).child('text').value()
                    if name.lower() == itemName:
                        self.server.pipdataManager.rpcUseItem(inventory.child(i))
                        data = 'Item %s has been equipped' % itemName
                        return data
                data = 'Could not find %s in your inventory' %  itemName
                return data

class MiddelWareServer(socketserver.TCPServer):
    # This class just here to store values to be passed along to handler
    def __init__(self, server_address, RequestHandlerClass, pipObj, pipDataManager):
        socketserver.ThreadingTCPServer.__init__(self,
                                                 server_address,
                                                 RequestHandlerClass)
        self.pipRootObj = pipObj
        self.pipdataManager = pipDataManager
        self.pipInventoryInfo = None
        self.pipRadioInfo = None
        self.availableGrenades = []
        self.lastEquippedGrenade = ''
class socket_serverThread(QtCore.QThread):
    def __init__(self, host, port, pipObj, pipDataManager):
        QtCore.QThread.__init__(self)
        self.HOST = host
        self.PORT = port
        self.pipObj = pipObj
        self.pipDataManager = pipDataManager


    def __del__(self):
        self.wait()

    def _onShutdown(self):
        self.tcpServer.shutdown()
        self.tcpServer.server_close()
        self.tcpServer = ""

    def _onUpdate(self, newpipRootObj):
        self.tcpServer.pipRootObj = newpipRootObj

    def runMyTest(self):
        self.tcpServer.useItemByName('43','MyPistol')

    def run(self):
        self.tcpServer = MiddelWareServer((self.HOST, self.PORT), MyTCPHandler, self.pipObj, self.pipDataManager)
        self.tcpServer.serve_forever()
        self.tcpServer.shutdown()


