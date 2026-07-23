# -*- coding: utf-8 -*-
# Created on : Apr 14, 2025, 6:39:30 PM
# Author     : Grant
# Creates the schema selection dialog

import importlib.util
if importlib.util.find_spec("PyQt"):
    from PyQt import Qt, QDialog, QMessageBox
    from ui_linz_schema_selection_dialog import Ui_Dialog
    from linz_schema_utilities import MessageBoxes
    from linz_schema_utilities import Utilities
else:
    from .PyQt import Qt, QDialog, QMessageBox
    from .ui_linz_schema_selection_dialog import Ui_Dialog
    from .linz_schema_utilities import MessageBoxes
    from .linz_schema_utilities import Utilities


class SchemaSelectionDialog(QDialog):
    def __init__(self, parent, schemas, default=-1):
        """
        Constructor
        """
        super(SchemaSelectionDialog, self).__init__(parent)
        #   Set up the user interface that is constructed with Qt Designer.
        self.setStyleSheet(Utilities.stylesheet())
        self.parent = parent
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(
            Utilities.getApptitle(parent) + ' - Schema Selection')

        self.ui.schemaList.setToolTip(MessageBoxes.translate(
            parent, 'Select schema'))
        for schema in schemas:
            self.ui.schemaList.addItem(schema[0] + "\t" + schema[1])
        if default < 0:
            self.ui.schemaList.setCurrentRow(0)
        else:
            self.ui.schemaList.setCurrentRow(default)

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
        selection = self.ui.schemaList.currentRow()
        self.parent.setSchemaId(selection)
        self.accept()

    def cancel(self):
        self.parent.setSchemaId(None)
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
