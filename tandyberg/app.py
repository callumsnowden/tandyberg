import logging, signal, sys, json
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QLabel
from PyQt5.QtCore import Qt

from tandyberg.controller import Controller
from tandyberg.tandylayout import Ui_MainWindow

logging.basicConfig(level=logging.DEBUG)

class App(QMainWindow):
    """Main application class, is a Qt app"""
    def __init__(self):
        super().__init__()

        # Load up the main window layout, which is autogenerated from Qt Designer then pyuic5
        self.layout = Ui_MainWindow()
        self.layout.setupUi(self)

        self.statusLabel = QLabel()
        self.layout.statusbar.addWidget(self.statusLabel)

        # Initial config check - load it if it works
        try:
            self.loadConfig()
        except FileNotFoundError:
            self.config = {}
            self.config['presets'] = {}

        # Connect to camera if we can
        self.controller = Controller()
        if 'interface' in self.config:
            self.controller.connect(self.config['interface'])
        if self.controller.interface != None:
            self.statusLabel.setText(f"Connected on {self.controller.interface}")
            self.config['interface'] = self.controller.interface
            self.saveConfig()
        else:
            self.statusLabel.setText("Not connected to camera")

        # Enumerate serial devices
        self.layout.menuPort.aboutToShow.connect(self.setupConnectMenu)

        # Hook up functionality to the window. This is very verbose and a future improvement
        # might be to get Qt Designer to generate this stuff (I *think* that's possible)
        # ZOOM
        self.layout.telebutton.pressed.connect(self.controller.getZoomFunc('in'))
        self.layout.telebutton.released.connect(self.controller.stopZoom)
        self.layout.widebutton.pressed.connect(self.controller.getZoomFunc('out'))
        self.layout.widebutton.released.connect(self.controller.stopZoom)
        # SLEW
        self.layout.leftbutton.pressed.connect(self.controller.getSteerFunc('left'))
        self.layout.leftbutton.released.connect(self.controller.stopSteer)
        self.layout.rightbutton.pressed.connect(self.controller.getSteerFunc('right'))
        self.layout.rightbutton.released.connect(self.controller.stopSteer)
        self.layout.upbutton.pressed.connect(self.controller.getSteerFunc('up'))
        self.layout.upbutton.released.connect(self.controller.stopSteer)
        self.layout.downbutton.pressed.connect(self.controller.getSteerFunc('down'))
        self.layout.downbutton.released.connect(self.controller.stopSteer)
        # RECALL PRESETS
        self.layout.preset1.pressed.connect(self.recallPreset('1'))
        self.layout.preset2.pressed.connect(self.recallPreset('2'))
        self.layout.preset3.pressed.connect(self.recallPreset('3'))
        self.layout.preset4.pressed.connect(self.recallPreset('4'))
        self.layout.preset5.pressed.connect(self.recallPreset('5'))
        self.layout.preset6.pressed.connect(self.recallPreset('6'))
        self.layout.preset7.pressed.connect(self.recallPreset('7'))
        self.layout.preset8.pressed.connect(self.recallPreset('8'))
        self.layout.preset9.pressed.connect(self.recallPreset('9'))
        self.layout.preset10.pressed.connect(self.recallPreset('10'))
        # SET PRESTS
        self.layout.spreset1.triggered.connect(self.setPreset('1'))
        self.layout.spreset2.triggered.connect(self.setPreset('2'))
        self.layout.spreset3.triggered.connect(self.setPreset('3'))
        self.layout.spreset4.triggered.connect(self.setPreset('4'))
        self.layout.spreset5.triggered.connect(self.setPreset('5'))
        self.layout.spreset6.triggered.connect(self.setPreset('6'))
        self.layout.spreset7.triggered.connect(self.setPreset('7'))
        self.layout.spreset8.triggered.connect(self.setPreset('8'))
        self.layout.spreset9.triggered.connect(self.setPreset('9'))
        self.layout.spreset10.triggered.connect(self.setPreset('10'))
        # SET SPEED
        self.layout.slews1.triggered.connect(self.controller.getSetSpeed('0'))
        self.layout.slews3.triggered.connect(self.controller.getSetSpeed('2'))
        self.layout.slews5.triggered.connect(self.controller.getSetSpeed('4'))
        self.layout.slews7.triggered.connect(self.controller.getSetSpeed('6'))
        self.layout.slews9.triggered.connect(self.controller.getSetSpeed('8'))
        self.layout.slews11.triggered.connect(self.controller.getSetSpeed('a'))
        self.layout.slews13.triggered.connect(self.controller.getSetSpeed('c'))
        self.layout.slews15.triggered.connect(self.controller.getSetSpeed('e'))
        # FOCUS
        self.layout.focusauto.pressed.connect(self.autofocus)
        self.layout.focusslider.valueChanged.connect(self.focus)

        # KEYBOARD CONTROLS
        self.grabKeyboard() # Make keyboard events go to window
        self.keyMap = {
            Qt.Key_W: (self.controller.getSteerFunc('up'), self.controller.stopSteer),
            Qt.Key_A: (self.controller.getSteerFunc('left'), self.controller.stopSteer),
            Qt.Key_S: (self.controller.getSteerFunc('down'), self.controller.stopSteer),
            Qt.Key_D: (self.controller.getSteerFunc('right'), self.controller.stopSteer),
            Qt.Key_E: (self.controller.getZoomFunc('in'), self.controller.stopZoom),
            Qt.Key_Q: (self.controller.getZoomFunc('out'), self.controller.stopZoom),
        }
    
    def autofocus(self):
        self.controller.getFocus()
        if self.layout.focusauto.isChecked():
            self.controller.disableAutoFocus()
            self.layout.focusslider.setEnabled(True)
        else:
            self.controller.enableAutoFocus()
            self.layout.focusslider.setEnabled(False)
    
    def focus(self):
        self.controller.goToFocus(self.layout.focusslider.sliderPosition())
    
    def keyPressEvent(self, event):
        """Reimplement Qt keyboard event handling to do our keyboard controls"""
        key = event.key()
        if key in self.keyMap and not event.isAutoRepeat():
            self.keyMap[key][0]()
    
    def keyReleaseEvent(self, event):
        key = event.key()
        if key in self.keyMap and not event.isAutoRepeat():
            self.keyMap[key][1]()
    
    def tryConnect(self, interface):
        """Returns a function that tries to connect to a port"""
        def do():
            self.controller.connect(interface)
            if self.controller.interface != None:
                self.statusLabel.setText(f"Connected on {self.controller.interface}")
                self.config['interface'] = self.controller.interface
                self.saveConfig()
            else:
                self.statusLabel.setText("Not connected to camera")
        return do

    def setupConnectMenu(self):
        for interface in self.controller.getPorts():
            action = QAction(self)
            action.setText(interface)
            action.triggered.connect(self.tryConnect(interface))
            self.layout.menuPort.addAction(action)
    
    def saveConfig(self):
        print(self.config)
        with open('config.json', 'w') as cfile:
            cfile.write(json.dumps(self.config))
    
    def loadConfig(self):
        with open('config.json', 'r') as cfile:
            self.config = json.loads(cfile.read())
            print(self.config)
    
    def setPreset(self, preset):
        def do():
            loc = self.controller.getPos()
            if 'presets' not in self.config:
                self.config['presets'] = {}
            self.config['presets'][preset] = loc
            self.saveConfig()
        return do

    def recallPreset(self, preset):
        def do():
            if preset in self.config['presets']:
                loc = self.config['presets'][preset]
                self.controller.goToPos(*loc)
        return do
    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
