# Created on : Dec 26, 2025, 3:07:23 PM
# linz_schema_schemas.py
# Author     : Grant
# Module for handling miscellaneous utility routines

import os
from enum import Enum
import datetime
from pathlib import Path
import zipfile
import shutil
import configparser
from PIL import Image
from configparser import ConfigParser
import importlib.util

if importlib.util.find_spec("PyQt"):
    # from PyQt import uic, loadUi
    # from PyQt import QtGui, QtWidgets, QtCore
    from PyQt import (
        QCoreApplication,
        QIcon, QPixmap, QImage,
        QMainWindow,
        QMessageBox, QFileDialog,
        QLabel)
else:
    # from .PyQt import uic, loadUi
    # from .PyQt import QtGui, QtWidgets, QtCore
    from .PyQt import (
        QCoreApplication,
        QIcon, QPixmap, QImage,
        QMainWindow,
        QMessageBox, QFileDialog,
        QLabel)

# Standard stylesheet to use throughout application
STYLESHEET = \
    u"QToolButton {" \
    " background-color: #eff0f1; color: black; margin: 1px;" \
    " border-style: outset; border-width: 1px; border-radius: 6px; "\
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black} " \
    "QToolButton:hover {background-color: white; " \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black} " \
    "QToolButton:pressed {background-color: #c4c8cc;" \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: black;" \
    " border-top-color: black;" \
    " border-right-color: lightgray;" \
    " border-bottom-color: lightgray;} " \
    "QPushButton {" \
    " background-color: #eff0f1; color: black; margin: 5px;" \
    " border-style: outset; border-width: 2px; border-radius: 6px; "\
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black;" \
    " min-width: 90px;" \
    " font: Semibold 14px;" \
    " padding: 4px;} " \
    "QPushButton:hover {background-color: white; " \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black;} " \
    "QPushButton:pressed {background-color: #c4c8cc;" \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: black;" \
    " border-top-color: black;" \
    " border-right-color: lightgray;" \
    " border-bottom-color: lightgray;} " \
    "QProgressBar{ background-color: rgb(255, 225, 175); " \
    " color: rgb(0, 0, 0); " \
    " selection-background-color: rgb(170, 85, 0); " \
    " font: Semibold 10t \"Noto Sans\"; } " \
    "QProgressBar::chunk{ background-color: rgb(170, 85, 0); }" \
    "QLineEdit {background-color: white; color: black; } " \
    "QLabel {color: black; } " \
    "QMainWindow {color: rgb(0, 0, 0); background-color: #e0ffe1;} " \
    "QMessageBox {color: rgb(0, 0, 0); background-color: #e0ffe1;} " \
    "QDialog {color: rgb(0, 0, 0); background-color: #e0ffe1;} "


class Field():
    """'Type' definition for database field.
    """
    fieldName = None
    fieldSrc = None
    fieldType = None
    fieldWidth = None
    isKey = False

    def __init__(self, name=None, source=None, type=None, width=None,
                 isKey=False):
        self.fieldName = name
        self.fieldSrc = source
        self.fieldType = type
        self.fieldWidth = width
        self.isKey = isKey

    def __str__(self):
        return f'{self.fieldName} : {self.fieldSrc} : ' \
            '{self.fieldType} : {self.fieldWidth} : {self.isKey}'
# /Field


class MessageBoxes(Enum):
    """Class to handle creation of message boxes.
    """

    NONE = QMessageBox.Icon.NoIcon
    INFORMATION = QMessageBox.Icon.Information
    WARNING = QMessageBox.Icon.Warning
    CRITICAL = QMessageBox.Icon.Critical
    QUESTION = QMessageBox.Icon.Question
    OK = QMessageBox.StandardButton.Ok
    CANCEL = QMessageBox.StandardButton.Cancel
    OK_CANCEL = OK | CANCEL
    YES = QMessageBox.StandardButton.Yes
    NO = QMessageBox.StandardButton.No
    YES_NO = YES | NO
    YES_NO_CANCEL = YES | NO | CANCEL
    APPLY = QMessageBox.StandardButton.Apply
    RESET = QMessageBox.StandardButton.Reset
    APPLY_RESET = APPLY | RESET
    CLOSE = QMessageBox.StandardButton.Close
    HELP = QMessageBox.StandardButton.Help

    def messageBox(parent, style, title, message, buttons=OK, icon=None):
        """Display a message box.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param style: Message box type from MessageBoxes.INFORMATION,
         MessageBoxes.Icon.WARNING, MessageBoxes.Icon.CRITICAL
        :type style: int

        :param title: Message box title.
        :type title: str

        :param message: Message text.
        :type message: str

        :param buttons: Message box buttons
        :type buttons: int

        :param icon: Message icon
        :type icon: QPixmap
        """
        msgBox = QMessageBox(parent)
        lines = message.count('<br>')
        if lines > 10:
            w = msgBox.findChild(QLabel, "qt_msgbox_label").width()
            w = int(w + (w * lines / 100))
            msgBox.findChild(QLabel, "qt_msgbox_label").setFixedWidth(w)

        if icon:
            msgBox.setIconPixmap(icon)
        else:
            match style:
                case MessageBoxes.INFORMATION:
                    msgBox.setIcon(MessageBoxes.INFORMATION.value)
                case MessageBoxes.WARNING:
                    msgBox.setIcon(MessageBoxes.WARNING.value)
                case MessageBoxes.CRITICAL:
                    msgBox.setIcon(MessageBoxes.CRITICAL.value)
                case MessageBoxes.QUESTION:
                    msgBox.setIcon(MessageBoxes.QUESTION.value)
                case _:
                    msgBox.setIcon(MessageBoxes.NONE.value)
        match buttons:
            case MessageBoxes.OK:
                b = MessageBoxes.OK.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(MessageBoxes.OK.value)
                msgBox.setEscapeButton(MessageBoxes.OK.value)
            case MessageBoxes.CANCEL:
                b = MessageBoxes.CANCEL.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(MessageBoxes.CANCEL.value)
                msgBox.setEscapeButton(MessageBoxes.CANCEL.value)
            case MessageBoxes.OK_CANCEL:
                b = MessageBoxes.OK.value | MessageBoxes.CANCEL.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(MessageBoxes.OK.value)
                msgBox.setEscapeButton(MessageBoxes.CANCEL.value)
            case MessageBoxes.YES_NO:
                b = MessageBoxes.YES.value | MessageBoxes.NO.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(MessageBoxes.NO.value)
                msgBox.setEscapeButton(MessageBoxes.NO.value)
            case MessageBoxes.YES_NO_CANCEL:
                b = QMessageBox.Yes.value | MessageBoxes.NO.value | \
                    MessageBoxes.CANCEL.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(MessageBoxes.NO.value)
                msgBox.setEscapeButton(QMessageBox.No.value)
            case MessageBoxes.APPLY_RESET:
                b = MessageBoxes.APPLY.value | MessageBoxes.RESET.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(MessageBoxes.APPLY.value)
                msgBox.setEscapeButton(MessageBoxes.RESET.value)
            case MessageBoxes.CLOSE:
                b = QMessageBox.StandardButton.Close.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(QMessageBox.StandardButton.Close.value)
                msgBox.setEscapeButton(QMessageBox.StandardButton.Close.value)
            case _:
                b = MessageBoxes.OK.value
                msgBox.setStandardButtons(b)
                msgBox.setDefaultButton(MessageBoxes.OK.value)
                msgBox.setEscapeButton(MessageBoxes.OK.value)

        msgBox.setText(message)
        msgBox.setWindowTitle(title)
        returnValue = msgBox.exec()
        return returnValue
    # /messageBox

    def openDirectoryBox(parent, title, path):
        """Display a open directory dialog box.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param title: Message box title.
        :type title: str

        :param path: Directory path to open.
        :type path: str

        :returns: Selected directory.
        :rtype: str
        """
        msgBox = QFileDialog()
        msgBox.setFileMode(QFileDialog.FileMode.Directory)
        msgBox.setViewMode(QFileDialog.ViewMode.List)  # List Detail
        msgBox.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        msgBox.setOption(QFileDialog.Option.ShowDirsOnly, True)
        msgBox.setOption(QFileDialog.Option.HideNameFilterDetails, True)
        msgBox.setOption(QFileDialog.Option.ReadOnly, True)
        directoryName = msgBox.getExistingDirectory(parent, title, path)
        return directoryName
    # /openDirectoryBox

    def openFileBox(parent, title, path, filter):
        """Display a file open dialog box.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param title: Message box title.
        :type title: str

        :param path: Directory path to open.
        :type path: str

        :param filter: Name filter
        :type filter: str

        :returns: Selected (fileName, selectedFilter).
        :rtype: str
        """
        msgBox = QFileDialog()
        msgBox.setFileMode(QFileDialog.FileMode.ExistingFile)
        msgBox.setViewMode(QFileDialog.ViewMode.Detail)  # List Detail
        msgBox.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        msgBox.setOption(QFileDialog.Option.ShowDirsOnly, False)
        msgBox.setOption(QFileDialog.Option.HideNameFilterDetails, False)
        msgBox.setOption(QFileDialog.Option.ReadOnly, True)
        fileName = msgBox.getOpenFileName(parent, title, path, filter)
        return fileName
    # /openFileBox

    def saveFileBox(parent, title, path, filter):
        """Display a file open dialog box.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param title: Message box title.
        :type title: str

        :param path: Directory path to open.
        :type path: str

        :param filter: Name filter
        :type filter: str

        :returns: Selected (fileName, selectedFilter).
        :rtype: str
        """
        msgBox = QFileDialog()
        msgBox.setFileMode(QFileDialog.FileMode.AnyFile)
        msgBox.setViewMode(QFileDialog.ViewMode.Detail)  # List Detail
        msgBox.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        msgBox.setOption(QFileDialog.Option.ShowDirsOnly, False)
        msgBox.setOption(QFileDialog.Option.HideNameFilterDetails, False)
        msgBox.setOption(QFileDialog.Option.ReadOnly, False)
        fileName = msgBox.getSaveFileName(parent, title, path, filter)
        return fileName
    # /saveFileBox

    def translate(parent, message):
        """Get the translation for a string using Qt translation API.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param message: Text message for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(Utilities.getAppname(parent), message)
    # /translate
# /MessageBoxes


class Utilities():
    """Utilities class for handling miscellaneous utility routines
    """
    def stylesheet():
        """Get the application consistant stylesheet.

        :returns: The application stylesheet text.
        :rtype: str
        """
        return STYLESHEET
    # /stylesheet

    def getVrtFiles(zip):
        """Get a list of all the files of type .vrt from a zipfile.
        :param zip: Existing zipfile.
        :type zip: zipfile.ZipFile

        :returns: List of .vrt file names.
        :rtype: List
        """
        if zip is None:
            return None
        vrtfiles = []
        for zipFile in zip.namelist():
            if zipFile.endswith('.vrt'):
                vrtfiles.append(zipFile)
        return vrtfiles
    # /getVrtFiles

    def getFields(tree, geometry, geofield, key):
        """Get a list of all the field definitions from a .vrt file.
        :param tree: Element tree created from .vrt file.
        :type tree: ElementTree

        :param geometry: Geometry type name given from .vrt file.
        :type geometry: Str

        :param geofield: Geometry field name given from .vrt file.
        :type geofield: Str

        :param key: Primary key field name given from .vrt file.
        :type key: Str

        :returns: List of type Field.
        :rtype: List[]
        """
        fields = []
        if tree is None:
            return fields
        if geometry:
            hasIntKey = False
            for source in tree.iter('Field'):
                if not hasIntKey:
                    f = source.attrib.get('name')
                    t = Utilities.fieldTypeTranslate(
                        source.attrib.get('type'), source.attrib.get('width'))
                    if (f == key) and t == 'INTEGER':
                        hasIntKey = True
            if hasIntKey:
                pass
            else:
                field = Field('OGR_FID', '1', 'INTEGER', 10)
                fields.append(field)
            field = Field('SHAPE', geofield, geometry)
            fields.append(field)
        for source in tree.iter('Field'):
            f = source.attrib.get('name')
            s = source.attrib.get('src')
            t = Utilities.fieldTypeTranslate(
                source.attrib.get('type'), source.attrib.get('width'))
            w = Utilities.fieldSizeTranslate(f, t, source.attrib.get('width'))
            k = (f == key)
            f = Utilities.fieldNameTranslate(f)
            fields.append(Field(f, s, t, w, k))
        return fields
    # /getFields

    def fieldTypeTranslate(fieldType, width):
        """Convert LINZ field type to database specific types.
        :param fieldType: LINZ GIS field type.
        :type fieldType: Str

        :param width: Size of field.
        :type width: Int

        :returns: Database specific type.
        :rtype: Str
        """
        if fieldType:
            fieldType = fieldType.upper().replace('CHARACTER VARYING', 'TEXT') \
                .replace('STRING', 'VARCHAR') \
                .replace('INTEGER64', 'BIGINT') \
                .replace('REAL', 'FLOAT')
            if width:
                if int(width) > 1024:
                    fieldType = 'TEXT'
        else:
            return None
        return fieldType
    # /fieldTypeTranslate

    def fieldSizeTranslate(fieldName, fieldType, width):
        """Convert LINZ field size to database limited sizes.
        :param fieldName: LINZ GIS field name.
        :type fieldName: Str

        :param fieldType: Database field type.
        :type fieldType: Str

        :param width: Size of field.
        :type width: Int

        :returns: Database specific field size.
        :rtype: Int
        """
        if fieldType == 'VARCHAR' and not width:
            if fieldName.upper().endswith('CODE'):
                width = 32
            else:
                width = 512
        elif fieldType == 'STRING' and not width:
            width = 1024
        elif fieldType == 'UUID':
            width = None
        return width
    # /fieldSizeTranslate

    def fieldNameTranslate(fieldName):
        """Convert LINZ field name to valid database identifier name.
        :param fieldName: LINZ GIS field name.
        :type fieldName: Str

        :returns: Valid database identifier name.
        :rtype: Str
        """
        if fieldName:
            match fieldName:
                case 'order':
                    fieldName = "orderby"
                case 'default':
                    fieldName = "isdefault"
                case 'desc':
                    fieldName = "description"
                case 'constraint':
                    fieldName = "conditions"
                case 'condition':
                    fieldName = "conditions"
                case 'use':
                    fieldName = "uses"
        else:
            return None
        return fieldName
    # /fieldNameTranslate

    def isCreateFieldIndex(fieldName, fieldType, isKey=False, fieldSrc=None):
        """Test if a field should be indexed.
        :param fieldName: Database field name.
        :type fieldName: Str

        :param fieldType: Database field type.
        :type fieldType: Str

        :param isKey: True if field is the LINZ GIS key field.
        :type isKey: Boolean

        :param fieldSrc: Field source definition.
                         (column name in .csv file
                          or "1" to auto increment)
        :type fieldSrc: Str

        :returns: True if conditions met to index field.
        :rtype: Boolean
        """
        if fieldName is None or fieldType is None:
            return False
        if isKey or \
           fieldSrc == '1' or \
           Utilities.isGeometryField(fieldType):
            return False
        if fieldType.upper().endswith('TEXT') or \
           fieldType.upper().endswith('LOB'):
            return False
        name = fieldName.upper()
        if name.endswith('_ID') or \
           name.endswith('_ID_PARENT') or \
           name.endswith('TITLE_NO') or \
           name.endswith('_CODE'):
            return True
        if name == 'ID' or \
           name == 'SURNAME' or \
           name == 'PRIME_SURNAME' or \
           name == 'CORPORATE_NAME' or \
           name == 'LEASE_NAME' or \
           name == 'NAME' or \
           name == 'REFERENCE_NO' or \
           name == 'ACT_TIN_ID' or \
           name == 'ATT_TYPE' or \
           name == 'ADDRESS_REFERENCE_OBJECT_VALUE' or \
           name == 'ADDREESS_COMPONENT_VALUE' or \
           name == 'VALUATION_REFERENCE' or \
           name == 'LEGAL_DESCRIPTION' or \
           name == 'FULL_ROAD_NAME' or \
           name == 'ROAD_NAME' or \
           name == 'MAJOR_NAME' or \
           name == 'ADDITIONAL_NAME' or \
           name == 'TERRITORIAL_AUTHORITY':
            return True
        return False
    # /isCreateFieldIndex

    def getLatestDate(d1, d2):
        """Get the later of two dates of the same type.
        :param d1: First date given.
        :type d1: Object

        :param d2: Second date given.
        :type d2: Object

        :returns: The later of the given dates as the type given.
        :rtype: Object
        """
        if d1 and d2:
            if d1 < d2:
                return d2
        if d1:
            return d1
        return d2
    # /getLatestDate

    def isNewer(d1, d2):
        """Test if truncated first datetime is after second date.
        :param d1: First datetime given.
        :type d1: datetime

        :param d2: Second date given.
        :type d2: Date

        :returns: True if first date is after second date.
        :rtype: Boolean
        """
        if d2 and d1:
            return (d1.date() > d2)
        return True
    # /isNewer

    def isNull(value):
        """Test if value is empty.
        :param value: Value given.
        :type value: Str

        :returns: True if value is None or length of zero.
        :rtype: Boolean
        """
        if value:
            return (len(value) == 0)
        return True
    # /isNull

    def isTextField(type):
        """Test if a field type is text.
        :param type: Field type given.
        :type type: Str

        :returns: True if field type is text.
        :rtype: Boolean
        """
        if type:
            t = type.upper()
            if t.find('TEXT') >= 0 \
               or t.find('CHAR') >= 0 \
               or t.find('BLOB') >= 0 \
               or t.find('CLOB') >= 0 \
               or t.find('BINARY') >= 0 \
               or t.find('BYTE') >= 0 \
               or t.find('UUID') >= 0:
                return True
        return False
    # /isTextField

    def isDateField(type):
        """Test if a field type is date.
        :param type: Field type given.
        :type type: Str

        :returns: True if field type is date or time.
        :rtype: Boolean
        """
        if type:
            t = type.upper()
            if t.find('DATE') >= 0 \
               or t.find('TIME') >= 0 \
               or t.find('DATETIME') >= 0 \
               or t.find('TIMESTAMP') >= 0:
                return True
        return False
    # /isDateField

    def isNumberField(type):
        """Test if a field type is numeric.
        :param type: Field type given.
        :type type: Str

        :returns: True if field type is numeric.
        :rtype: Boolean
        """
        if type:
            t = type.upper()
            if t.find('REAL') >= 0 \
               or t.find('FLOAT') >= 0 \
               or t.find('DECIMAL') >= 0 \
               or t.find('DOUBLE') >= 0 \
               or t.find('BIGINT') >= 0 \
               or t.find('INTEGER') >= 0:
                return True
        return False
    # /isNumberField

    def isGeometryField(type):
        """Test if a field type is geometric.
        :param type: Field type given.
        :type type: Str

        :returns: True if field type is geometric.
        :rtype: Boolean
        """
        if type:
            geotypes = [
                'POINT', 'MULTIPOINT',
                'LINESTRING', 'MULTILINESTRING',
                'POLYGON', 'MULTIPOLYGON',
                'GEOMETRY', 'GEOMETRYCOLLECTION']
            return type.upper() in geotypes
        return False
    # /isGeometryField

    def truncateValue(value, width):
        """Truncate a value to given maximum width.
        :param value: Value given.
        :type value: Str

        :param width: Maximum width of value.
        :type width: Int

        :returns: Value truncated to width.
        :rtype: Str
        """
        if value and width:
            if len(value) > int(width):
                value = value[0:int(width) - 1]
        return value
    # /truncateValue

    def getGeometryValue(geometry, geotype, value):
        """Build geometry string from components.
        :param geometry: Expected geometry type.
        :type geometry: Str

        :param geotype: Actual geometry type.
        :type geotype: Str

        :param value: Geometry string value given.
        :type value: Str

        :returns: String to geometry database function name;
                  Corrected geometry string.
        :rtype: Str, Str
        """
        match geometry:
            case 'POINT':
                geoFromText = "ST_PointFromText"
            case 'LINESTRING':
                geoFromText = "ST_LineFromText"
            case 'POLYGON':
                geoFromText = "ST_PolyFromText"
            case 'MULTIPOINT':
                geoFromText = "ST_MPointFromText"
            case 'MULTILINESTRING':
                geoFromText = "ST_MLineFromText"
            case 'MULTIPOLYGON':
                geoFromText = "ST_MPolyFromText"
            case 'GEOMETRYCOLLECTION':
                geoFromText = "ST_GeomCollFromText"
            case 'GEOMETRY':
                geoFromText = "ST_GeomFromText"
            case _:
                geoFromText = "ST_GeomFromText"
        # value = value.replace(',', ',\n')
        if geometry == 'MULTI' + geotype \
           or geometry == geotype + 'COLLECTION':
            value = value.replace(geotype, f'{geometry}(', 1) + ')'
        return (geoFromText, value)
    # /getGeometryValue

    def createViewname(sql):
        """Get database view name out of sql command text.
        :param sql: Sql command string.
        :type sql: Str

        :returns: Name of view extracted from sql text.
        :rtype: Str
        """
        viewname = None
        if sql:
            f = sql.split()
            if len(f) > 4:
                logic1 = f[0].upper() == 'CREATE' \
                    and f[1].upper() == 'OR' \
                    and f[2].upper() == 'REPLACE' \
                    and f[3].upper() == 'VIEW'
                logic2 = f[0].upper() == 'DROP' \
                    and f[1].upper() == 'VIEW' \
                    and f[2].upper() == 'IF' \
                    and f[3].upper() == 'EXISTS'
                if logic1 or logic2:
                    viewname = f[4]
            elif len(f) > 2:
                logic1 = f[0].upper() == 'CREATE' \
                    and f[1].upper() == 'VIEW'
                logic2 = f[0].upper() == 'DROP' \
                    and f[1].upper() == 'VIEW'
                if logic1 or logic2:
                    viewname = f[2]
        return viewname
    # /createViewname

    def isDropSql(sql):
        """Test if sql command text is a "DROP" statement.
        :param sql: Sql command string.
        :type sql: Str

        :returns: True if Sql text is a drop command.
        :rtype: Boolean
        """
        if sql:
            f = sql.split()
            if len(f) > 1:
                if f[0].upper() == 'DROP':
                    return True
        return False
    # /isDropSql

    def getNow():
        """Gets the current datetime.

        :returns: The current datetime truncated to seconds.
        :rtype: datetime
        """
        return datetime.datetime.now().replace(microsecond=0)
    # /getNow

    def getNowString():
        """Gets the string formatted current datetime.

        :returns: The current datetime truncated to seconds.
        :rtype: Str
        """
        return Utilities.getNow().strftime('%d/%m/%y %H:%M:%S')
    # /getNowString

    def getElapsedTime(startTime):
        """Gets the current time elapsed since a given time.
        :param startTime: The start datetime.
        :type startTime: datetime

        :returns: The elapsed datetime truncated to seconds.
        :rtype: datetime
        """
        now = Utilities.getNow()
        elapsed = now - startTime
        return elapsed
    # /getElapsedTime

    def getRemainingTime(startTime, totalItems, cnt):
        """Calculate the remaining time given the number of items processed.
        :param startTime: The start datetime.
        :type startTime: datetime

        :param totalItems: The total number of items to process.
        :type totalItems: Int

        :param cnt: The number of items processed.
        :type cnt: Int

        :returns: The remaining time calculated.
        :rtype: datetime
        """
        if cnt == 0:
            return "unknown"
        elapsed = Utilities.getElapsedTime(startTime)
        remainingTime = (((totalItems / cnt) * elapsed) - elapsed)
        remainingTime -= \
            datetime.timedelta(microseconds=remainingTime.microseconds)
        return f"{remainingTime}"
    # /getRemainingTime

    def getTreeText(tree, branch, index, default=None):
        """Get the value of an item in an element tree created from XML text.
        :param tree: The element tree from XML text.
        :type tree: ElementTree

        :param branch: The branch name within the tree.
        :type branch: Int

        :param index: The field name within the tree.
        :type index: Str

        :param default: Default value if index not found.
        :type default: Str

        :returns: String value of tree item for branch.field.
        :rtype: Str
        """
        text = default
        if tree is not None:
            if branch:
                for source in tree.iter(branch):
                    text = source.attrib.get(f'{index}')
            else:
                for source in tree.iter(f'{index}'):
                    text = source.text
        return text
    # /getTreeText

    def getTreeInt(tree, branch, index, default=0):
        """Get the value of an item in an element tree created from XML text.
        :param tree: The element tree from XML text.
        :type tree: ElementTree

        :param branch: The branch name within the tree.
        :type branch: Int

        :param index: The field name within the tree.
        :type index: Str

        :param default: Default value if index not found.
        :type default: Str

        :returns: Integer value of tree item for branch.field.
        :rtype: Int
        """
        text = None
        if branch:
            for source in tree.iter(branch):
                text = source.attrib.get(f'{index}')
        else:
            for source in tree.iter(f'{index}'):
                text = source.text
        if text:
            return int(text)
        return default
    # /getTreeInt

    def getPathDirectory(path):
        """Extract the directory name from a full path name.
        :param path: The "/" delimited path name.
        :type path: Str

        :returns: The directory name part of a path.
        :rtype: Str
        """
        if path:
            s = path.rfind("/")
            if s < 1:
                return ""
            return path[0:s]
        return None
    # /getPathDirectory

    def getPathFile(path):
        """Extract the file name from a full path name, excluding any extension.
        :param path: The "/" delimited path name.
        :type path: Str

        :returns: The file name part of a path.
        :rtype: Str
        """
        if path:
            e = path.rfind(".")
            if e < 1:
                e = len(path)
            s = path.rfind("/")
            return path[s + 1:e]
        return None
    # /getPathFile

    def getPathExt(path):
        """Extract the file extension name from a full path name.
        :param path: The "/" delimited path name.
        :type path: Str

        :returns: The extension name part of a path.
        :rtype: Str
        """
        if path:
            e = path.rfind(".")
            if e < 1:
                return ""
            return path[e + 1:len(path)]
        return None
    # /getPathExt

    def getZippedFile(zip, fileName):
        """Get the path a file from a zipfile.
        :param zip: Existing zipfile.
        :type zip: zipfile.ZipFile

        :returns: Path of file within zip.
        :rtype: Str
        """
        if zip is None or fileName is None:
            return None
        file = fileName
        for f in zip.namelist():
            if f.endswith(fileName):
                file = f
        return file
    # /getZippedFile

    def copyFolder(parent, src, dst):
        """Copy contents of a directory recursively to another directory.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param src: The source directory path name.
        :type src: Str

        :param dst: The destination directory path name.
        :type dst: Str
        """
        if src is None or dst is None:
            return
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            try:
                if os.path.isdir(s):
                    os.makedirs(d, exist_ok=True)
                    Utilities.copyFolder(parent, s, d)
                elif os.path.isfile(s):
                    if not os.path.exists(d) or \
                       os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                        shutil.copy2(s, d)
            except (OSError, IOError, EnvironmentError) as err:
                parent.appendLog(f'  Failed to copy {s} to {d}\n{err}')
    # /copyFolder

    def removeFolder(parent, folder):
        """Deletes a directory and its contents. Use with caution!
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param folder: The directory path name.
        :type folder: Str
        """
        if folder is None:
            return
        if isinstance(folder, str):
            name = folder
        else:
            name = f'{folder}'
        if len(name) < 5:
            parent.appendLog(
                f'  Failed to delete {name}: possible system folder.')
            return
        directory = Path(folder)
        for item in directory.iterdir():
            if item.is_dir():
                Utilities.removeFolder(parent, item)
            else:
                try:
                    item.unlink()
                except (OSError, IOError) as err:
                    parent.appendLog(f'  Failed to delete {item}\n{err}')
        directory.rmdir()
    # /removeFolder

    def getAppname(parent):
        """Get the application name.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :returns: Name of application.
        :rtype: Str
        """
        if isinstance(parent, QMainWindow):
            return parent.getAppname()
        else:
            if parent.parent:
                return Utilities.getAppname(parent.parent)
        return ""
    # /getAppname

    def getApptitle(parent):
        """Get the application title.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :returns: Title of application.
        :rtype: Str
        """
        if isinstance(parent, QMainWindow):
            return Utilities.getMetadata(
                parent.metadata, 'general', 'name')
        else:
            if parent.parent:
                return Utilities.getApptitle(parent.parent)
        return ""
    # /getApptitle

    def readMetadata(parent):
        """Read metadata.txt for application.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :returns: metadata.
        :rtype: ConfigParser
        """
        metaName = 'metadata.txt'
        infoName = 'metainfo.txt'
        metadata = ConfigParser()
        if os.path.isfile(metaName):
            file = open(metaName, 'r', newline='', encoding="utf-8-sig")
            Utilities.readMetadataFile(metadata, file)
            file.close()
            file = open(infoName, 'r', newline='', encoding="utf-8-sig")
            Utilities.readMetadataFile(metadata, file)
            file.close()
        else:
            try:
                (root, ext) = os.path.split(__file__)
                (file, ext) = os.path.splitext(root)
                if ext == '.zip' or ext == '.pyz':
                    with zipfile.ZipFile(root, 'r') as zip:
                        file = zip.open(metaName, 'r')
                        Utilities.readMetadataFile(metadata, file)
                        file.close()
                        file = zip.open(infoName, 'r')
                        Utilities.readMetadataFile(metadata, file)
                        file.close()
                else:
                    (root, f) = os.path.split(__file__)
                    file = open(os.path.join(root, metaName), 'rt')
                    Utilities.readMetadataFile(metadata, file)
                    file.close()
                    file = open(os.path.join(root, infoName), 'rt')
                    Utilities.readMetadataFile(metadata, file)
                    file.close()
            except IOError as err:
                print(f'Failed to open file: {metaName} and {infoName}'
                      f'\n{err}')
        return metadata
    # /readMetadata

    def readMetadataFile(metadata, metaFile):
        """Read line from metadata.txt for application.
        :param metadata: metadata that is appended to with newly read data.
        :type metadata: ConfigParser

        :param metaFile: open metadata file to read from.
        :type metaFile: File
        """
        try:
            text = metaFile.read()
            if isinstance(text, bytes):
                metadata.read_string(
                    text.decode('utf-8-sig').replace('\n ', '<br> '))
            else:
                metadata.read_string(
                    text.replace('\n ', '<br> '))
        except IOError as err:
            print('Failed to read metadata file:'
                  f'\n{err}')
    # /readMetadataFile

    def getMetadata(metadata, section='DEFAULT', key=None):
        """Get value from metadata.
        :param metadata: metadata.
        :type metadata: ConfigParser

        :param section: Section name of metadata to lookup.
        :type section: Str

        :param key: Key name within section of metadata to lookup.
        :type key: Str
        """
        if metadata and key:
            try:
                value = metadata.get(section, key)
            except (configparser.NoSectionError, configparser.NoOptionError):
                return ''
            if value:
                return value
            else:
                return ''
        return ''
    # /getMetadata

    def readHelpFile(parent):
        """Read help from README.md for application.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :returns: Contents text of file.
        :rtype: Str
        """
        helpName = 'README.md'
        if os.path.isfile(helpName):
            file = open(helpName, 'r', newline='', encoding="utf-8-sig")
            help = Utilities.readHelpdataFile(file)
            file.close()
        else:
            try:
                (root, ext) = os.path.split(__file__)
                (file, ext) = os.path.splitext(root)
                if ext == '.zip' or ext == '.pyz':
                    with zipfile.ZipFile(root, 'r') as zip:
                        file = zip.open(helpName, 'r')
                        help = Utilities.readHelpdataFile(file)
                        file.close()
                else:
                    (root, f) = os.path.split(__file__)
                    file = open(os.path.join(root, helpName), 'rt')
                    help = Utilities.readHelpdataFile(file)
                    file.close()
            except IOError as err:
                print(f'Failed to open file: {helpName}'
                      f'\n{err}')
        return help
    # /readHelpFile

    def readHelpdataFile(file):
        """Read help from README.md for application.
        :param file: Open fil to read contents from.
        :type file: File

        :returns: Contents text of file.
        :rtype: Str
        """
        try:
            data = file.read()
            if isinstance(data, bytes):
                text = data.decode('utf-8-sig')
            else:
                text = data
        except IOError as err:
            print('Failed to read help file:'
                  f'\n{err}')
        return text
    # /readHelpdataFile

    def getPixmap(filename):
        """Read Pixmap from file.
        :param filename: File name to read Pixmap from.
        :type filename: Str

        :returns: Pixmap from file.
        :rtype: QPixmap
        """
        if filename:
            (root, file) = os.path.split(__file__)
            path = os.path.join(root, filename)
            if os.path.isfile(path):
                pixmap = QPixmap(path)
                return pixmap
            else:
                try:
                    (root, ext) = os.path.split(__file__)
                    (file, ext) = os.path.splitext(root)
                    if ext == '.zip' or ext == '.pyz':
                        with zipfile.ZipFile(root, 'r') as zip:
                            iconFile = zip.open(filename)
                            image = Image.open(iconFile)
                            image = image.convert("RGBA")
                            data = image.tobytes("raw", "BGRA")
                            qim = QImage(data, image.width, image.height,
                                         QImage.Format.Format_ARGB32)
                            image.close()
                            iconFile.close()
                            pixmap = QPixmap.fromImage(qim)
                            return pixmap
                except (IOError, AttributeError, TypeError) as err:
                    print(f'Failed to open file: {filename}'
                          f'\n{err}')
        return None
    # /getPixmap

    def getIcon(filename):
        """Read Icon from file.
        :param filename: File name to read Icon from.
        :type filename: Str

        :returns: Icon from file.
        :rtype: QIcon
        """
        if filename:
            (root, file) = os.path.split(__file__)
            path = os.path.join(root, filename)
            if os.path.isfile(path):
                icon = QIcon(path)
                return icon
            else:
                try:
                    (root, ext) = os.path.split(__file__)
                    (file, ext) = os.path.splitext(root)
                    if ext == '.zip' or ext == '.pyz':
                        with zipfile.ZipFile(root, 'r') as zip:
                            iconFile = zip.open(filename)
                            image = Image.open(iconFile)
                            image = image.convert("RGBA")
                            data = image.tobytes("raw", "BGRA")
                            qim = QImage(data, image.width, image.height,
                                         QImage.Format.Format_ARGB32)
                            image.close()
                            iconFile.close()
                            pixmap = QPixmap.fromImage(qim)
                            icon = QIcon(pixmap)
                            return icon
                except (IOError, AttributeError, TypeError) as err:
                    print(f'Failed to open file: {filename}'
                          f'\n{err}')
        return None
    # /getIcon
# /Utilities
