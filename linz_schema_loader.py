# -*- coding: utf-8 -*-
# Created on : 12/11/2024, 9:19:29 pm
# Author     : Grant Pearson, Eureka Technology Limited
# Creates the main program window

import os
import sys
import platform
from pathlib import Path
import shutil
import importlib.util

if importlib.util.find_spec("PyQt"):
    # from PyQt import uic, loadUi
    # from PyQt import QtGui, QtWidgets, QtCore
    from PyQt import (
        pyqt, QObject, QCoreApplication, QSettings,
        Qt, QSize, QRect, QMetaObject,
        Signal, Slot,
        QIcon, QPixmap, QImage, QFont,
        QApplication, QMainWindow, QWidget, QFrame,
        QDialog, QMessageBox, QFileDialog,
        QLayout, QFormLayout, QGridLayout,
        QVBoxLayout, QHBoxLayout,
        QSizePolicy, QSpacerItem,
        QAbstractItemView, QAbstractScrollArea, QScrollArea,
        QLabel, QLineEdit, QPlainTextEdit,
        QPushButton, QToolButton, QListWidget, QListWidgetItem,
        QProgressBar, QMenuBar, QStatusBar,
        QMenu, QAction,
        QDomDocument, QDomElement, QTextCursor)
else:
    # from .PyQt import uic, loadUi
    # from .PyQt import QtGui, QtWidgets, QtCore
    from .PyQt import (
        pyqt, QObject, QCoreApplication, QSettings,
        Qt, QSize, QRect, QMetaObject,
        Signal, Slot,
        QIcon, QPixmap, QImage, QFont,
        QApplication, QMainWindow, QWidget, QFrame,
        QDialog, QMessageBox, QFileDialog,
        QLayout, QFormLayout, QGridLayout,
        QVBoxLayout, QHBoxLayout,
        QSizePolicy, QSpacerItem,
        QAbstractItemView, QAbstractScrollArea, QScrollArea,
        QLabel, QLineEdit, QPlainTextEdit,
        QPushButton, QToolButton, QListWidget, QListWidgetItem,
        QProgressBar, QMenuBar, QStatusBar,
        QMenu, QAction,
        QDomDocument, QDomElement, QTextCursor)

if importlib.util.find_spec("linz_schema_utilities"):
    from linz_schema_utilities import MessageBoxes, Utilities
    from linz_schema_database import Database
    from linz_schema_schemas import SchemasActions
    from linz_schema_features import FeaturesActions
    from linz_schema_login_dialog import LoginDialog
    from linz_schema_selection_dialog import SchemaSelectionDialog
    from linz_schema_create_dialog import SchemaCreateDialog
    from ui_linz_schema_loader_window import Ui_MainWindow as MainWindow
else:
    from .linz_schema_utilities import MessageBoxes, Utilities
    from .linz_schema_database import Database
    from .linz_schema_schemas import SchemasActions
    from .linz_schema_features import FeaturesActions
    from .linz_schema_login_dialog import LoginDialog
    from .linz_schema_selection_dialog import SchemaSelectionDialog
    from .linz_schema_create_dialog import SchemaCreateDialog
    from .ui_linz_schema_loader_window import Ui_MainWindow as MainWindow

if importlib.util.find_spec("qgis"):
    from qgis.core import QgsApplication
    # from qgis.core import QgsSettings
    from qgis.gui import QgsMapCanvas
    # from qgis.analysis import QgsNativeAlgorithms
    import qgis.utils
    HAS_QGIS = True
else:
    if importlib.util.find_spec("linz_schema_utilities"):
        from linz_schema_utilities import NullClass as QgsMapCanvas
    else:
        from .linz_schema_utilities import NullClass as QgsMapCanvas
    HAS_QGIS = False

SCHEMAS = [
    ['linz',
     'LINZ Landonline (LINZ)'],
    ['linztest',
     'LINZ Landonline (TEST)']
]


# class linz_schema_loader(QObject):
class linz_schema_loader(QMainWindow, MainWindow, QgsMapCanvas):
    """
    QGIS Plugin Implementation.
    """

    def __init__(self, iface=None, app=None):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # print(f'__init__ {self.__class__.__name__}')
        self.app = app
        self.metadata = Utilities.readMetadata(self)
        self.recentPath = None
        # Save reference to the QGIS interface
        if iface:
            super(linz_schema_loader, self).__init__()
            # super(linz_schema_loader, self).__init__(iface)
            self.isPlugin = True
            self.iface = iface
            self.parent = self.iface.mainWindow()
            # initialize plugin directory
            self.plugin_dir = os.path.dirname(__file__)
            # Declare instance attributes
            self.actions = []
            self.menu = "LINZ Schema Loader"
            self.toolbar = self.iface.addToolBar("LINZ Schema Loader")
            if self.toolbar:
                self.toolbar.setOrientation(Qt.Orientation.Horizontal)
                self.toolbar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
                self.toolbar.setObjectName("LINZ Schema Loader")
        else:
            super().__init__()
            self.isPlugin = False
            self.iface = None
            self.parent = None

        self.schemasActions = None
        self.featuresActions = None
        self.cnx = None
        self.schema = None
        self.schemaId = -1
        self.ui = MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(Utilities.getApptitle(self))
        icon = Utilities.getIcon(os.path.join('images', 'icon.png'))
        self.setWindowIcon(icon)
        self.connectSignalSlots()
        self.setStyleSheet(Utilities.stylesheet())
        # save QMessageBox standard buttons to use in other dialogs
        self.msgBox = QMessageBox()
        self.msgBox.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel |
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.standardOkButton = self.msgBox.button(
            QMessageBox.StandardButton.Ok)
        self.standardCancelButton = self.msgBox.button(
            QMessageBox.StandardButton.Cancel)
        self.standardYesButton = self.msgBox.button(
            QMessageBox.StandardButton.Yes)
        self.standardNoButton = self.msgBox.button(
            QMessageBox.StandardButton.No)
        self.init()
    # /__init__

    def init(self):
        # print(f'init {self.__class__.__name__}')
        self.readStatus(None)
        self.setMenuEnabled()
        if not self.isPlugin:
            self.setLog(True)
            self.show()
            self.refresh(self)
            if not Database.isDatabaseConnector():
                msg = '\nUnable to connect to database:\n' + \
                      'No MariaDB/MySQL Python Connector module found.'
                self.appendLog(msg)
                MessageBoxes.messageBox(
                    self,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(self),
                    msg)
#        quit = self.connectDB()
    # /init

    def connectSignalSlots(self):
        self.ui.actionExit.triggered.connect(
            self.doActionExit)
        self.ui.actionConnect.triggered.connect(
            self.doActionConnect)
        self.ui.actionSelectSchema.triggered.connect(
            self.doActionSelectSchema)
        self.ui.actionCreateSchema.triggered.connect(
            self.doActionCreateSchema)
        self.ui.actionUpdateSchema.triggered.connect(
            self.doActionUpdateSchema)
        self.ui.actionDropSchema.triggered.connect(
            self.doActionDropSchema)
        self.ui.actionLoadcsvData.triggered.connect(
            self.doActionLoadcsvData)
        self.ui.actionCreateIndexes.triggered.connect(
            self.doActionCreateIndexes)
        self.ui.actionCreateViews.triggered.connect(
            self.doActionCreateViews)
        self.ui.actionCreateLayers.triggered.connect(
            self.doActionCreateLayers)
        self.ui.actionCreateRelations.triggered.connect(
            self.doActionCreateRelations)
        self.ui.actionLoadLayerStyles.triggered.connect(
            self.doActionLoadLayerStyles)
        self.ui.actionCreateTopoStyles.triggered.connect(
            self.doActionCreateTopoStyles)
        self.ui.actionAbout.triggered.connect(
            self.doActionAbout)
        self.ui.actionHelp.triggered.connect(
            self.doActionHelp)
    # /connectSignalSlots

    def setMenuEnabled(self):
        self.ui.menuBar.setStyleSheet(
            "background-color: rgb(239, 240, 241); "
            "color: rgb(0, 0, 0); "
            "selection-background-color: rgb(196, 197, 198); "
            "selection-color: rgb(0, 0, 0); "
            "font: Semibold 10t \"Noto Sans\"; "
        )
        fh = QFont()
        fh.setBold(True)
        fh.setItalic(True)
        fh.setKerning(True)
        fh.setWeight(QFont.Weight.DemiBold)
        self.ui.actionSchemasSchema.setFont(fh)
        self.ui.actionLayersSchema.setFont(fh)

        s = 'background-color: rgb(239, 240, 241); ' \
            'font: 81 10pt \"Noto Sans\"; ' \
            'color: rgb(0, 0, 0); ' \
            'selection-background-color: rgb(196, 197, 198); ' \
            'selection-color: rgb(0, 0, 0); '
        fd = QFont()
        fd.setBold(False)
        fd.setKerning(True)
        fd.setWeight(QFont.Weight.Light)
        fe = QFont()
        fe.setBold(True)
        fe.setKerning(True)
        fe.setWeight(QFont.Weight.Bold)
        self.ui.menuMain.setStyleSheet(s)
        self.ui.menuMain.setFont(fe)
        self.ui.menuSchemas.setStyleSheet(s)
        self.ui.menuSchemas.setFont(fe)
        self.ui.menuLayers.setStyleSheet(s)
        self.ui.menuLayers.setFont(fe)
        self.ui.actionExit.setEnabled(True)
        self.ui.actionExit.setFont(fe)
        self.ui.actionAbout.setEnabled(True)
        self.ui.actionAbout.setFont(fe)
        self.ui.actionHelp.setEnabled(True)
        self.ui.actionHelp.setFont(fe)

        if Database.isDatabaseConnector():
            self.ui.actionConnect.setEnabled(True)
            self.ui.actionConnect.setFont(fe)
        else:
            self.ui.actionConnect.setEnabled(False)
            self.ui.actionConnect.setFont(fd)

        if Database.isConnected(self.cnx):
            self.ui.actionSelectSchema.setEnabled(True)
            self.ui.actionSelectSchema.setFont(fe)
            if self.schema:
                self.ui.actionSchemasSchema.setText(self.schema[0])
                self.ui.actionLayersSchema.setText(self.schema[0])
                if Database.isSchemaExist(self, self.cnx, self.schema[0]):
                    self.ui.actionCreateSchema.setEnabled(False)
                    self.ui.actionCreateSchema.setFont(fd)
                    self.ui.actionUpdateSchema.setEnabled(True)
                    self.ui.actionUpdateSchema.setFont(fe)
                    self.ui.actionDropSchema.setEnabled(True)
                    self.ui.actionDropSchema.setFont(fe)
                    self.ui.actionLoadcsvData.setEnabled(True)
                    self.ui.actionLoadcsvData.setFont(fe)
                    self.ui.actionCreateIndexes.setEnabled(True)
                    self.ui.actionCreateIndexes.setFont(fe)
                    self.ui.actionCreateViews.setEnabled(True)
                    self.ui.actionCreateViews.setFont(fe)
                else:
                    self.ui.actionCreateSchema.setEnabled(True)
                    self.ui.actionCreateSchema.setFont(fe)
                    self.ui.actionUpdateSchema.setEnabled(False)
                    self.ui.actionUpdateSchema.setFont(fd)
                    self.ui.actionDropSchema.setEnabled(False)
                    self.ui.actionDropSchema.setFont(fd)
                    self.ui.actionLoadcsvData.setEnabled(False)
                    self.ui.actionLoadcsvData.setFont(fd)
                    self.ui.actionCreateIndexes.setEnabled(False)
                    self.ui.actionCreateIndexes.setFont(fd)
                    self.ui.actionCreateViews.setEnabled(False)
                    self.ui.actionCreateViews.setFont(fd)
            else:
                self.ui.actionSchemasSchema.setText("....")
                self.ui.actionLayersSchema.setText("....")
                self.ui.actionCreateSchema.setEnabled(True)
                self.ui.actionCreateSchema.setFont(fe)
                self.ui.actionUpdateSchema.setEnabled(False)
                self.ui.actionUpdateSchema.setFont(fd)
                self.ui.actionDropSchema.setEnabled(False)
                self.ui.actionDropSchema.setFont(fd)
                self.ui.actionLoadcsvData.setEnabled(False)
                self.ui.actionLoadcsvData.setFont(fd)
                self.ui.actionCreateIndexes.setEnabled(False)
                self.ui.actionCreateIndexes.setFont(fd)
                self.ui.actionCreateViews.setEnabled(False)
                self.ui.actionCreateViews.setFont(fd)
        else:
            self.ui.actionSelectSchema.setEnabled(False)
            self.ui.actionSelectSchema.setFont(fd)
            self.ui.actionCreateSchema.setEnabled(False)
            self.ui.actionCreateSchema.setFont(fd)
            self.ui.actionUpdateSchema.setEnabled(False)
            self.ui.actionUpdateSchema.setFont(fd)
            self.ui.actionDropSchema.setEnabled(False)
            self.ui.actionDropSchema.setFont(fd)
            self.ui.actionLoadcsvData.setEnabled(False)
            self.ui.actionLoadcsvData.setFont(fd)
            self.ui.actionCreateIndexes.setEnabled(False)
            self.ui.actionCreateIndexes.setFont(fd)
            self.ui.actionCreateViews.setEnabled(False)
            self.ui.actionCreateViews.setFont(fd)

        if HAS_QGIS and Database.isConnected(self.cnx) and self.schema:
            self.ui.actionCreateLayers.setEnabled(True)
            self.ui.actionCreateLayers.setFont(fe)
            self.ui.actionCreateRelations.setEnabled(True)
            self.ui.actionCreateRelations.setFont(fe)
        else:
            self.ui.actionCreateLayers.setEnabled(False)
            self.ui.actionCreateLayers.setFont(fd)
            self.ui.actionCreateRelations.setEnabled(False)
            self.ui.actionCreateRelations.setFont(fd)
        if HAS_QGIS:
            self.ui.actionLoadLayerStyles.setEnabled(True)
            self.ui.actionLoadLayerStyles.setFont(fe)
            self.ui.actionCreateTopoStyles.setEnabled(True)
            self.ui.actionCreateTopoStyles.setFont(fe)
        else:
            self.ui.actionLoadLayerStyles.setEnabled(False)
            self.ui.actionLoadLayerStyles.setFont(fd)
            self.ui.actionCreateTopoStyles.setEnabled(False)
            self.ui.actionCreateTopoStyles.setFont(fd)
    # /setMenuEnabled

    def doActionExit(self):
        print(f'Closing {self.__class__.__name__}')
        self.close()
    # /doActionExit

    # Cleanup before attribute table window closes
    def cleanupWhenWindowClosed(self):
        Database.disconnectDatabase(self, self.cnx)
        self.appendLog('\nDisconnected from database')
        self.appendLog('Process LINZ Schema finished')
        if self.logFile is not None:
            if not self.logFile.closed:
                self.logFile.close()
            self.setLog(False)
        if HAS_QGIS:
            if isinstance(self.app, QgsApplication):
                self.app.exitQgis()
        else:
            if isinstance(self.app, QApplication):
                self.app.exit()
    # /cleanupWhenWindowClosed

    def closeEvent(self, event):
        self.cleanupWhenWindowClosed()
    # /closeEvent

    def doActionConnect(self):
        cont = self.connectDB()
        if cont:
            cont = self.selectSchema()
        else:
            Database.disconnectDatabase(self, self.cnx)
        self.setMenuEnabled()
    # /doActionConnect

    def doActionSelectSchema(self):
        self.selectSchema()
        self.setMenuEnabled()
    # /doActionSelectSchema

    def initSchemasActions(self):
        if not self.schemasActions:
            self.schemasActions = SchemasActions()
    # /getSchemasActions

    def initFeaturesActions(self):
        if not self.featuresActions:
            self.featuresActions = FeaturesActions()
    # /initFeaturesActions

    def doActionCreateSchema(self):
        self.initSchemasActions()
        if self.checkUsername(self.sourceConfig, True):
            if self.schema:
                pass
            else:
                self.appendLog('\nGet GIS Schema...')
                dlg = SchemaCreateDialog(self)
                if dlg.exec():
                    self.appendLog(f'Schema {self.schema[0]} selected')
                if self.schemaId < 0:
                    self.appendLog('No schema selected.')
                    return
                else:
                    self.appendLog(f'Using schema {self.schema[0]}')

            cont = self.schemasActions.requestSchemaCreate(
                self, self.cnx, self.schema[0], self.schema[1])
            if cont:
                self.schemasActions.requestSchemaLoad(
                    self, self.cnx, self.schema[0])
            self.setMenuEnabled()
    # /doActionCreateSchema

    def doActionUpdateSchema(self):
        self.initSchemasActions()
        if self.checkUsername(self.sourceConfig, True):
            self.schemasActions.updateSchema(
                self, self.cnx, self.schema[0], self.schema[1])
    # /doActionUpdateSchema

    def doActionDropSchema(self):
        self.initSchemasActions()
        if self.checkUsername(self.sourceConfig, True):
            self.schemasActions.requestSchemaDrop(
                self, self.cnx, self.schema[0])
            self.setMenuEnabled()
    # /doActionDropSchema

    def doActionLoadcsvData(self):
        self.initSchemasActions()
        if self.checkUsername(self.sourceConfig, True):
            self.schemasActions.requestSchemaLoad(
                self, self.cnx, self.schema[0])
    # /doActionLoadcsvData

    def doActionCreateIndexes(self):
        self.initSchemasActions()
        if self.checkUsername(self.sourceConfig, True):
            self.schemasActions.createMissingIndexes(
                self, self.cnx, self.schema[0])
    # /doActionCreateIndexes

    def doActionCreateViews(self):
        self.initSchemasActions()
        if self.checkUsername(self.sourceConfig, True):
            self.schemasActions.processViews(
                self, self.cnx, self.schema[0])
    # /doActionCreateViews

    def doActionCreateLayers(self):
        self.initFeaturesActions()
        if self.checkUsername(self.sourceConfig, False):
            self.featuresActions.processLayers(
                self, self.sourceConfig, self.cnx, self.schema[0])
    # /doActionCreateLayers

    def doActionCreateRelations(self):
        self.initFeaturesActions()
        if self.checkUsername(self.sourceConfig, False):
            self.featuresActions.processRelations(
                self, self.cnx, self.schema[0])
    # /doActionCreateRelations

    def doActionLoadLayerStyles(self):
        self.initFeaturesActions()
        if self.schema:
            schema = self.schema[0]
        else:
            schema = None
        self.featuresActions.processLoadLayerStyles(
            self, self.cnx, schema)
    # /doActionLoadLayerStyles

    def doActionCreateTopoStyles(self):
        self.initFeaturesActions()
        if self.schema:
            schema = self.schema[0]
        else:
            schema = None
        self.featuresActions.processTopoStyles(
            self, self.cnx, schema)
    # /doActionCreateTopoStyles

    def doActionAbout(self):
        version = Utilities.getMetadata(
            self.metadata, 'general', 'version')
        author = Utilities.getMetadata(
            self.metadata, 'general', 'author')
        about = Utilities.getMetadata(
            self.metadata, 'general', 'about')
        generalLicense = Utilities.getMetadata(
            self.metadata, 'license', 'general')
        linzLicense = Utilities.getMetadata(
            self.metadata, 'license', 'linz')
        env = f'\n<h2>{Utilities.getApptitle(self)}</h2>'
        if version:
            env += f'<b> v.{version}</b><br><br>'
        env += f'Running on host: {platform.node()}<br>'
        env += f'{platform.system()} '
        env += f'v.{platform.release()} '
        env += f'({platform.machine()})<br>'
        env += f'Python v.{sys.version}<br>'
        if pyqt.isPyQGIS():
            env += '&nbsp;&nbsp;using module QGIS.PyQt ' \
                f'v.{pyqt.pyqtVersion()}<br>'
        elif pyqt.isPyQt():
            env += '&nbsp;&nbsp;using module PyQt ' \
                f'v.{pyqt.pyqtVersion()}<br>'
        elif pyqt.isPySide():
            env += '&nbsp;&nbsp;using module PySide2 ' \
                f'v.{pyqt.pyqtVersion()}<br>'
        else:
            env += '&nbsp;&nbsp;PyQt module not found<br>'
        if Database.isMariadb():
            env += '&nbsp;&nbsp;using module mariadb ' \
                f'v.{Database.getConnectorVersion()}<br>'
        if Database.isMysql():
            env += '&nbsp;&nbsp;using module MySQLdb ' \
                f'v.{Database.getConnectorVersion()}<br>'
        if Database.isPyMysql():
            env += '&nbsp;&nbsp;using module pymysql ' \
                f'v.{Database.getConnectorVersion()}<br>'
        if HAS_QGIS:
            env += '&nbsp;&nbsp;using module qgis ' \
                f'v.{qgis.utils.Qgis.QGIS_VERSION}<br>'
        env += f'Qt v.{pyqt.qtVersion()}<br><br>'
        if Database.isConnected(self.cnx):
            host = Database.getHostDB(self, self.cnx)
            user = Database.getUsername(self, self.cnx)
            ver = Database.getDBVersion(self, self.cnx)
            env += f'Connected to database {ver}<br>'
            env += f'&nbsp;&nbsp;on server {host} as user {user}<br>'
            if self.schema:
                env += f'Schema {self.schema[0]} ({self.schema[1]}) selected' \
                       '<br><br>'
            else:
                env += 'No schema selected<br><br>'
        else:
            env += 'Not connected to database<br><br>'
        if author:
            env += f'Author: {author}<br><br>'
        if about:
            env += f'<i>{about}</i><br><br>'
        env += f'{generalLicense}<br>'
        env += f'{linzLicense}<br>'
        icon = Utilities.getPixmap(os.path.join('images', 'icon.png'))
        if icon:
            icon = icon.scaledToWidth(128)
            icon = icon.scaledToWidth(128)
        MessageBoxes.messageBox(
            self,
            MessageBoxes.INFORMATION,
            f'About: {Utilities.getApptitle(self)}',
            env, MessageBoxes.OK, icon)
    # /doActionAbout

    def doActionHelp(self):
        help = Utilities.readHelpFile(self)
        self.helpLog(help)
    # /doActionHelp

    def add_action(
            self,
            icon_path,
            text,
            callback,
            checkable=False,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = Utilities.getIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)
        return action
    # /add_action

    def initGui(self):
        # Create the menu entries and toolbar icons inside the QGIS GUI.
        # print(f'initGUI {self.__class__.__name__}')
        self.setLog(False)
        self.add_action(
            os.path.join('images', 'icon.png'),
            text="LINZ Schema Loader",
            checkable=False,
            callback=self.callGui,
            add_to_toolbar=True,
            parent=self.iface.mainWindow())
        self.mainWindow = None
    # /initGui

    def callGui(self):
        # print(f'callGUI {self.__class__.__name__}')
        if self.logFile is None:
            self.setLog(True)
        elif self.logFile.closed:
            self.setLog(True)
        icon = Utilities.getIcon(os.path.join('images', 'icon.png'))
        if self.mainWindow is None:
            self.setWindowIcon(icon)
        self.refresh(self)
        self.activateWindow()
        self.show()
    # /callGui

    def unload(self):
        # Removes the plugin menu item and icon from QGIS GUI.
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                "LINZ Schema Loader",
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    # /unload

    def connectDB(self):
        self.appendLog('\nConnect to MariaDB/MySQL database...')
        dlg = LoginDialog(self)
        if dlg.exec():
            self.appendLog('Connected to database on '
                           f'{Database.getHostDB(self, self.cnx)}')
            self.localDb = Database.isLocalDB(self, self.cnx)
            return True
        self.appendLog('Failed to connect to database')
        if self.cnx:
            Database.disconnectDatabase(self, self.cnx)
        return False
    # /connect

    def selectSchema(self):
        self.getGISschemas()
        self.appendLog('\nSelect GIS Schema...')
        dlg = SchemaSelectionDialog(self, SCHEMAS, self.schemaId)
        if dlg.exec():
            self.appendLog(f'Schema {self.schema[0]} selected')
            return True
        if self.schemaId < 0:
            self.appendLog('No schema selected.')
        else:
            self.appendLog(f'Using schema {self.schema[0]}')
        return False
    # /selectSchema

    def getGISschemas(self):
        sql = "SELECT s.SCHEMA_NAME, s.SCHEMA_COMMENT, count(t.TABLE_NAME) " \
            "FROM information_schema.TABLES t " \
            "INNER JOIN information_schema.schemata s " \
            "ON t.TABLE_SCHEMA=s.SCHEMA_NAME " \
            "WHERE (s.SCHEMA_NAME like '%gis%' " \
            " OR s.SCHEMA_NAME like '%geo%' " \
            " OR lower(t.TABLE_NAME) in " \
            "  ('geometry_columns', 'spatial_ref_sys', 'table_datasets')) " \
            "AND s.SCHEMA_NAME not in ("
        for schema in SCHEMAS:
            sql += f"'{schema[0]}', "
        sql += \
            "'information_schema', 'sys', 'performance_schema', 'mysql') " \
            "GROUP BY s.SCHEMA_NAME, s.SCHEMA_COMMENT " \
            "ORDER BY count(t.TABLE_NAME) desc, s.SCHEMA_NAME asc;"
        schemas = Database.readDatabase(self, self.cnx, sql)
        for schema in schemas:
            SCHEMAS.append([schema[0], schema[1]])
    # / getGISschemas

    """
    def getFid(self, schemaname, tablename, fields):
        fidName = None
        for field in fields:
            if field.fieldSrc == "1":
                fidName = field.fieldName
        if fidName:
            sql = f"SELECT ifnull(max({fidName}), 0) " \
                  f"FROM {schemaname}.{tablename};"
            fid = Database.readDatabaseResult(self, self.cnx, sql)
        else:
            fid = 0
        return fid
    # /getFid
    """

    def readStatus(self, layer, startTime=None, fcnt=0, readCnt=0):
        if layer:
            if (readCnt < 2000 and (readCnt % 100) == 0) \
               or (readCnt % 1000) == 0 \
               or readCnt == fcnt:
                remainingTime = Utilities.getRemainingTime(
                    startTime, fcnt, readCnt)
                self.ui.progressBar.setVisible(True)
                self.ui.progressBar.setValue(int((readCnt / fcnt) * 100))
                self.ui.layerLabel.setText(layer)
                self.ui.progressLabel.setText(
                    f'{readCnt:,}/{fcnt:,} records read')
                self.ui.RemainderLabel.setText(
                    f'Time remaining {remainingTime}')
        else:
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setVisible(False)
            self.ui.layerLabel.setText(None)
            self.ui.progressLabel.setText(None)
            self.ui.RemainderLabel.setText(None)
        self.refresh(self)
    # /readStatus

    def loadDatasetTable(self, schemaname):
        sql = f"INSERT INTO {schemaname}.table_datasets " \
            "(schemaname, tablename, dataset_cnt) " \
            "SELECT " \
            "t.TABLE_SCHEMA, t.TABLE_NAME, 0 " \
            "FROM information_schema.TABLES t " \
            "WHERE " \
            f"t.TABLE_SCHEMA = '{schemaname}' " \
            "AND t.TABLE_NAME NOT IN " \
            "('geometry_columns', 'spatial_ref_sys', 'table_datasets') " \
            "EXCEPT " \
            "SELECT d.schemaname, d.tablename, 0 " \
            f"FROM {schemaname}.table_datasets d " \
            f"WHERE d.schemaname='{schemaname}';"
        Database.executeSQL(self, self.cnx, sql, True)
        Database.commit(self, self.cnx)
    # /loadDatasetTable

    def clearDatasetTable(self, schemaname, tablename=None):
        if schemaname:
            sql = f"DELETE FROM {schemaname}.table_datasets " \
                f"WHERE schemaname='{schemaname}' "
            if tablename:
                sql += f"AND tablename='{tablename}';"
            else:
                sql += ";"
            Database.executeSQL(self, self.cnx, sql)
            sql = f"DELETE FROM {schemaname}.geometry_columns " \
                f"WHERE F_TABLE_SCHEMA='{schemaname}' "
            if tablename:
                sql += f"AND F_TABLE_NAME='{tablename}';"
            else:
                sql += ";"
            Database.executeSQL(self, self.cnx, sql)
            Database.commit(self, self.cnx)
        # /clearDatasetTable

    def tableDefinition(self, schemaname, tablename):
        sql = "SELECT " \
            "c.ORDINAL_POSITION AS ORDINAL_POSITION, " \
            "c.COLUMN_NAME AS COLUMN_NAME, " \
            "c.COLUMN_TYPE AS COLUMN_TYPE, " \
            "if(c.COLUMN_KEY='PRI','Primary Key', " \
            "if(c.COLUMN_KEY='UNI','Unique','')) AS COLUMN_KEY, " \
            "c.IS_NULLABLE AS IS_NULLABLE " \
            "FROM " \
            "information_schema.COLUMNS c " \
            "INNER JOIN information_schema.TABLES t " \
            "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
            "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
            "AND c.TABLE_NAME = t.TABLE_NAME " \
            "WHERE " \
            f"t.TABLE_SCHEMA='{schemaname}' " \
            f"AND t.TABLE_NAME='{tablename}' " \
            "ORDER BY c.ORDINAL_POSITION ASC;"
        rows = Database.readDatabase(self, self.cnx, sql)
        tableDef = None
        for columnDef in rows:
            if tableDef:
                tableDef = f'{tableDef}\n{columnDef}'
            else:
                tableDef = f'{columnDef}'
        return tableDef
    # /tableDefinition

    def setConnection(self, sourceConfig, cnx):
        self.sourceConfig = sourceConfig
        self.cnx = cnx
    # /setConnection

    def checkUsername(self, sourceConfig, rootRequired=True):
        if sourceConfig:
            username = sourceConfig.get('username')
            if username:
                if rootRequired:
                    if username.lower() == 'root':
                        return True
                    option = MessageBoxes.messageBox(
                        self,
                        MessageBoxes.QUESTION,
                        Utilities.getApptitle(self),
                        'Administrator user required but not given.\n'
                        'Usual administrator is "root".\n\n'
                        f'Continue as user "{username}"?',
                        MessageBoxes.YES_NO)
                    if option == MessageBoxes.YES.value:
                        self.appendLog('\nAdministrator user required, '
                                       f'continuing as user "{username}".')
                        return True
                else:
                    if username.lower() != 'root':
                        return True
                    option = MessageBoxes.messageBox(
                        self,
                        MessageBoxes.QUESTION,
                        Utilities.getApptitle(self),
                        f'Administrator user not required but given.\n\n'
                        f'Continue as user "{username}"?',
                        MessageBoxes.YES_NO)
                    if option == MessageBoxes.YES.value:
                        self.appendLog('\nAdministrator user not required, '
                                       'continuing as user "root".')
                        return True
        if rootRequired:
            self.appendLog('\nConnect to database as username "root".')
        else:
            self.appendLog('\nConnect to database other than username "root".')
        return False
    # /checkUsername

    def setSchemaId(self, schemaId):
        if schemaId is None:
            self.schemaId = -1
            self.schema = None
        elif schemaId < 0:
            self.schemaId = -1
            self.schema = None
        else:
            self.schemaId = schemaId
            self.schema = SCHEMAS[schemaId]
    # /setSchemaId

    def setNewSchema(self, schema):
        if schema is None:
            self.schemaId = -1
            self.schema = None
        elif schema[0] is None:
            self.schemaId = -1
            self.schema = None
        else:
            SCHEMAS.append(schema)
            self.schemaId = SCHEMAS.index(schema)
            self.schema = schema
    # /setSchemaId

    def setRecentPath(self, recentPath):
        self.recentPath = recentPath
    # /setRecentPath

    def setLog(self, init=True):
        if init:
            name = self.__class__.__name__
            self.logFilename = os.path.join(
                Path.home(),
                name + '_{:%Y%m%d_%H%M%S}.log'.format(Utilities.getNow())
            )
            self.logFile = open(self.logFilename, "w")
            text = f'{Utilities.getApptitle(self)}\n' + \
                '{:%d-%b-%Y %H:%M:%S}\n'.format(Utilities.getNow()) + \
                f'Logging to {self.logFilename}\n'
            self.log = text
            self.ui.logField.setPlainText(self.log)
            self.ui.logField.moveCursor(
                QTextCursor.MoveOperation.End,
                QTextCursor.MoveMode.MoveAnchor)
            self.lastlog = text + "\n"
            self.logFile.write(text + "\n")
            self.logFile.flush()
        else:
            self.logFilename = None
            self.logFile = None
            self.log = None
            self.lastlog = None
            self.ui.logField.setPlainText('')
            self.ui.logField.moveCursor(
                QTextCursor.MoveOperation.End,
                QTextCursor.MoveMode.MoveAnchor)
    # /setLog

    def getLog(self):
        return self.log
    # /getLog

    def appendLog(self, text, replace=False):
        if self.log:
            if self.lastlog and replace:
                self.log = self.log.removesuffix(self.lastlog) + text + "\n"
                self.ui.logField.moveCursor(
                    QTextCursor.MoveOperation.End,
                    QTextCursor.MoveMode.MoveAnchor)
                self.ui.logField.moveCursor(
                    QTextCursor.MoveOperation.Up,
                    QTextCursor.MoveMode.KeepAnchor)
                self.ui.logField.moveCursor(
                    QTextCursor.MoveOperation.StartOfLine,
                    QTextCursor.MoveMode.KeepAnchor)
                self.ui.logField.textCursor().removeSelectedText()
                self.ui.logField.insertPlainText(text + "\n")
            else:
                self.log += text + "\n"
                self.ui.logField.moveCursor(
                    QTextCursor.MoveOperation.End,
                    QTextCursor.MoveMode.MoveAnchor)
                self.ui.logField.insertPlainText(text + "\n")
                self.ui.logField.moveCursor(
                    QTextCursor.MoveOperation.End,
                    QTextCursor.MoveMode.MoveAnchor)
        else:
            self.log = text + "\n"
            self.ui.logField.setPlainText(self.log)
        self.refresh(self)
        self.lastlog = text + "\n"
        if self.logFile:
            self.logFile.write(text + "\n")
            self.logFile.flush()
    # /appendLog

    def helpLog(self, text):
        self.ui.logField.clear()
        self.ui.logField.appendHtml(text)
        self.ui.logField.moveCursor(
            QTextCursor.MoveOperation.Start,
            QTextCursor.MoveMode.MoveAnchor)
        self.refresh(self)
    # /helpLog

    def getAppname(self):
        return self.__class__.__name__
    # /getAppname

    def refresh(self, container):
        for widget in container.children():
            if isinstance(widget, QLayout) \
               or isinstance(widget, QAction):
                pass
            else:
                self.refresh(widget)
                if widget.objectName():
                    widget.repaint()
    # /refresh

    def run(self=None):
        (root, file) = os.path.split(__file__)
        if HAS_QGIS:
            try:
                exe = shutil.which("qgis")
                # print(f"qgis={exe}")
                (qgsRoot, ext) = os.path.split(exe)
                QgsApplication.setPrefixPath(qgsRoot, True)
                args = sys.argv
                argsb = []
                for arg in args:
                    argsb.append(arg.encode('utf-8-sig'))
                app = QgsApplication(argsb, False)
                app.initQgis()
            except Exception as e:
                print(f"Error initializing QGIS:\n{e}")
        else:
            app = QApplication(sys.argv)
        # print('create mainWindow')
        mainWindow = linz_schema_loader(None, app)
        icon = Utilities.getIcon(os.path.join('images', 'icon.png'))
        mainWindow.setWindowIcon(icon)
        mainWindow.show()
        sys.exit(app.exec())
    # /run
# /linz_schema_loader


if __name__ == 'linz_schema_loader' or __name__ == '__main__':
    print('Running linz_schema_loader')
    linz_schema_loader.run()
