# -*- coding: utf-8 -*-
# Created on : Apr 14, 2025, 6:39:30 PM
# Author     : Grant
# Creates the login dialog

import socket
import importlib.util
if importlib.util.find_spec("PyQt"):
    from PyQt import Qt, QDialog, QMessageBox
    from ui_linz_schema_login_dialog import Ui_Dialog
    from linz_schema_utilities import MessageBoxes, Utilities
    from linz_schema_database import Database, SourceConfig
else:
    from .PyQt import Qt, QDialog, QMessageBox
    from .ui_linz_schema_login_dialog import Ui_Dialog
    from .linz_schema_utilities import MessageBoxes, Utilities
    from .linz_schema_database import Database, SourceConfig


class LoginDialog(QDialog):
    def __init__(self, parent):
        """
        Constructor
        """
        super(LoginDialog, self).__init__(parent)
        #   Set up the user interface that is constructed with Qt Designer.
        self.setStyleSheet(Utilities.stylesheet())
        self.parent = parent
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(
            Utilities.getApptitle(parent) + ' - Database Login')
        self.ui.hostField.setText(socket.gethostname())
        self.ui.hostField.setToolTip(MessageBoxes.translate(
            parent,
            'Enter database server ip host name/address.'))
        self.ui.portField.setText(Database.defaultPort("mariadb"))
        self.ui.portField.setToolTip(MessageBoxes.translate(
            parent,
            'Enter database server port number.'))
        self.ui.schemaField.setToolTip(MessageBoxes.translate(
            parent,
            'Enter database schema/database name (leave blank).'))
        self.ui.usernameField.setText(Database.defaultUsername("mariadb"))
        self.ui.usernameField.setToolTip(MessageBoxes.translate(
            parent,
            'Enter database root/system username.'))
        self.ui.passwordField.setText(Database.defaultPassword("mariadb"))
        self.ui.passwordField.setToolTip(MessageBoxes.translate(
            parent,
            'Enter database root/system password.'))

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.ui.okButton.clicked.connect(self.ok)
        self.ui.cancelButton.clicked.connect(self.cancel)

        # set buttons same as QMessageBox standard buttons
        self.ui.okButton.setText(
            parent.standardOkButton.text().replace("&", ""))
        self.ui.okButton.setIcon(parent.standardOkButton.icon())
        self.ui.okButton.setIconSize(parent.standardOkButton.iconSize())
        self.ui.okButton.setFont(parent.standardOkButton.font())
        self.ui.cancelButton.setText(
            parent.standardCancelButton.text().replace("&", ""))
        self.ui.cancelButton.setIcon(parent.standardCancelButton.icon())
        self.ui.cancelButton.setIconSize(parent.standardCancelButton.iconSize())
        self.ui.cancelButton.setFont(parent.standardCancelButton.font())

    def ok(self):
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', "mariadb")
        sourceConfig.setKey('databasename', self.ui.schemaField.text())
        sourceConfig.setKey('username', self.ui.usernameField.text())
        sourceConfig.setKey('password', self.ui.passwordField.text())
        sourceConfig.setKey('hostname', self.ui.hostField.text())
        sourceConfig.setKey('port', self.ui.portField.text())
        cnx = Database.connectDatabase(self, sourceConfig)
        if cnx:
            self.parent.setConnection(sourceConfig, cnx)
            self.accept()

    def cancel(self):
        self.reject()

    def closeWindow(self):
        self.close()

    # Cleanup before attribute table window closes
    def cleanupWhenWindowClosed(self):
        self.ui.okButton.clicked.disconnect(self.ok)
        self.ui.cancelButton.clicked.disconnect(self.cancel)

    # Trigger action for when close event occurs
    def closeEvent(self, event):
        self.cleanupWhenWindowClosed()

    def appendLog(self, text, replace=False):
        self.parent.appendLog(text, replace)
