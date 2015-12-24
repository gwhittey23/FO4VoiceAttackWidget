import socketserver
from PyQt5 import  QtCore
from .pipboyActions import RadioControl, InvetoryControl, MapControl
import logging

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
        self.server._logger.debug('Msg from VoiceAttack : ' + str(self.data.decode()))
        sCommand = sName_Raw[0]
        sName = sName_Raw[1]

        if sCommand == 'FastTravel':
            self.SafeMode = False
            self.mapControl = MapControl(self.server.pipdataManager , self.server.pipRootObj)
            return_message = self.mapControl.onFastTravel(sName)
        elif sCommand == 'Directions':
            self.mapControl = MapControl(self.server.pipdataManager , self.server.pipRootObj)
            return_message = self.mapControl.getDirections(sName)
        elif sCommand == 'MonitorHP':
            self.monitorHP()
        elif sCommand == "RadioToggle":
            self.radioControl = RadioControl(self.server.pipdataManager , self.server.pipRootObj)
            return_message = self.radioControl.toggleRadio()
        elif sCommand == "ChangeStation":
            self.radioControl = RadioControl(self.server.pipdataManager , self.server.pipRootObj)
            return_message = self.radioControl.changeStation(sName)
        elif sCommand == "NextStation":
            self.radioControl = RadioControl(self.server.pipdataManager , self.server.pipRootObj)
            return_message = self.radioControl.nextStation()
        elif sCommand == "EquipWeapon":
            self.invControl = InvetoryControl(self.server.pipdataManager , self.server.pipRootObj)
            return_message = self.invControl.useInventoryItemByName(sName,'43')
        elif sCommand == "NextGrenade":
            self.invControl = InvetoryControl(self.server.pipdataManager , self.server.pipRootObj)
            return_message = self.invControl.equipNextGrendae()
        elif sCommand == 'GrenadeEquip':
             self.invControl = InvetoryControl(self.server.pipdataManager , self.server.pipRootObj)
             return_message = self.invControl.useInventoryItemByName(sName,'43')
        elif sCommand == 'EatFood':
             self.invControl = InvetoryControl(self.server.pipdataManager , self.server.pipRootObj)
             return_message = self.invControl.useInventoryItemByName(sName,'48')
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
        self._logger = logging.getLogger('pypipboyapp.llhookey')
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
        print(self.pipDataManager)
        self.tcpServer = MiddelWareServer((self.HOST, self.PORT), MyTCPHandler, self.pipObj, self.pipDataManager)
        self.tcpServer.serve_forever()
