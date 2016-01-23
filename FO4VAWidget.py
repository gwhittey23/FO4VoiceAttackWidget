import os
from PyQt5 import  QtCore, uic, QtWidgets
from widgets import widgets
from .vaServerListner import socket_serverThread
from widgets.shared import settings
import logging

class FO4VaWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()

    def __init__(self, mhandle, parent):
        super().__init__('FO4VAWidget', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'fo4va.ui'))
        self.widget.btnStart.clicked.connect(self._startserver)
        self.widget.btnStop.clicked.connect(self._stopserver)
        self.widget.chkStart.clicked.connect(self.autoConnectToggled)
        self._logger = logging.getLogger('pypipboyapp.llhookey')
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
        self._logger.debug('Server Stopped')
        self.serverThread._onShutdown()
        self.serverThread.terminate()
        self.widget.lblServerState.setText("Server is Off")
        self.serverThread = False





