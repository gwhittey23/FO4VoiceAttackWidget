import os,sys
from PyQt5 import  QtCore, uic
from PyQt5.QtCore import (pyqtSignal, QByteArray, QDataStream, QIODevice,
        QThread)

from PyQt5.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
        QMessageBox, QPushButton, QVBoxLayout)
from PyQt5.QtNetwork import (QHostAddress, QNetworkInterface, QTcpServer,
        QTcpSocket, QAbstractSocket)

from .. import widgets

SIZEOF_UINT16 = 2
class FO4VaWidget(widgets.WidgetBase):
    _signalPipWorldLocationsUpdated = QtCore.pyqtSignal()
    error = pyqtSignal(QTcpSocket.SocketError)
    def __init__(self, mhandle, parent):
        super().__init__('FO4VA', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'fo4va.ui'))
        self.setWidget(self.widget)
        self._locations_dict = {}
        HOST = '127.0.0.1'   # Symbolic name meaning all available interfaces
        PORT = 8089 # Arbitrary non-privileged port
        self.server = TcpServer()
        if not self.server.listen(QHostAddress(HOST), PORT):
            QMessageBox.critical(self, "Threaded Fortune Server",
                    "Unable to start the server: %s." % self.server.errorString())
            self.close()
            return
        for ipAddress in QNetworkInterface.allAddresses():
            if ipAddress != QHostAddress.LocalHost and ipAddress.toIPv4Address() != 0:
                break
        else:
            ipAddress = QHostAddress(QHostAddress.LocalHost)

        ipAddress = ipAddress.toString()

        print("The server is running on\n\nIP: %s\nport: %d\n\n"
                "Run the Fortune Client example now." % (ipAddress, self.server.serverPort()))

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)

    def _onPipRootObjectEvent(self, rootObject):
        self.pipMapObject = rootObject.child('Map')
        self.pipMapWorldObject = self.pipMapObject.child('World')

        if self.pipMapWorldObject:
            self.pipWorldLocations = self.pipMapWorldObject.child('Locations')
            print("1")

            print (self.pipWorldLocations)

            if self.pipWorldLocations:
                print("2")
                self.pipWorldLocations.registerValueUpdatedListener(self._onPipWorldLocationsUpdated, 1)
                for k in self.pipWorldLocations.value():
                    for x in k.value():

                        if x == 'Name':
                            curName = k.child(x).value()
                            curKey = k.pipParentKey
                            curPoint = self.pipWorldLocations.child(curKey)
                            self._locations_dict.update({curPoint.pipId:curName})

        self._signalPipWorldLocationsUpdated.emit()

    def _onPipWorldLocationsUpdated(self, caller, value, pathObjs):
        print("Change")
        self._signalPipWorldLocationsUpdated.emit()

class Thread(QThread):

    #lock = QReadWriteLock()

    def __init__(self, socketId, parent):
        super(Thread, self).__init__(parent)
        self.socketId = socketId
        print("Thread Start")
    def run(self):
        self.socket = QTcpSocket()
        print("Thread run")
        if not self.socket.setSocketDescriptor(self.socketId):
            self.emit(SIGNAL("error(int)"),self.socket.error())
            return

        while self.socket.state() == QAbstractSocket.ConnectedState:
            self.nextBlockSize = 0
            stream = QDataStream(self.socket)
            print("after stream")
            stream.setVersion(QDataStream.Qt_4_2)
            if (self.socket.waitForReadyRead(-1) and
                self.socket.bytesAvailable() >= SIZEOF_UINT16):
                nextBlockSize = stream.readUInt16()
                print("if1")
            else:
                self.sendError("Cannot read client request")
                return
            if self.socket.bytesAvailable() < nextBlockSize:
                print("if2")

            print("Done")
            textFromClient = QS

            textToClient = "You wrote: \"{}\"".format(textFromClient)
            print(textToClient)
            #self.sendReply(textToClient)

    def sendError(self, msg):
        reply = QByteArray()
        stream = QDataStream(reply, QIODevice.WriteOnly)
        stream.setVersion(QDataStream.Qt_4_2)
        stream.writeUInt16(0)
        stream.writeQString("ERROR")
        stream.writeQString(msg)
        stream.device().seek(0)
        stream.writeUInt16(reply.size() - SIZEOF_UINT16)
        self.socket.write(reply)

    def sendReply(self, text):
        reply = QByteArray()
        stream = QDataStream(reply, QIODevice.WriteOnly)
        stream.setVersion(QDataStream.Qt_4_2)
        stream.writeUInt16(0)
        stream.writeQString(text)
        stream.device().seek(0)
        stream.writeUInt16(reply.size() - SIZEOF_UINT16)
        self.socket.write(reply)


class TcpServer(QTcpServer):

    def __init__(self, parent=None):
        super(TcpServer, self).__init__(parent)

    def incomingConnection(self, socketId):
        print("incomingConnection")
        self.thread = Thread(socketId, self)
        self.thread.start()