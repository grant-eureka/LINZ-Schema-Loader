# -*- coding: utf-8 -*-
# Created on : 30/11/2024, 10:10:24 pm
# Author     : Grant Pearson, Eureka Technology Limited

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

if importlib.util.find_spec("qgis"):
    from qgis.core import Qgis
    from qgis.core import QgsApplication
    from qgis.core import QgsSettings
    HAS_QGIS = True
else:
    HAS_QGIS = False

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
    " border-bottom-color: black} " \
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


class NullClass():
    """ Empty class for when qgis module not found
    """


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


class RelationItems():
    """Contain relationship definitions.
    """

    def __init__(self,
                 primaryLayer, primaryTable, primaryField,
                 refLayer, refTable, refField):
        self.primaryLayer = primaryLayer
        self.primaryTable = primaryTable
        self.primaryField = primaryField
        self.refLayer = refLayer
        self.refTable = refTable
        self.refField = refField

    def __str__(self):
        return self.text()

    def primaryLayer(self):
        return self.primaryLayer

    def primaryTable(self):
        return self.primaryTable

    def primaryField(self):
        return self.primaryField

    def refLayer(self):
        return self.refLayer

    def refTable(self):
        return self.refTable

    def refField(self):
        return self.refField

    def text(self):
        return f'{self.primaryLayer}:{self.primaryTable}.{self.primaryField}' \
               f' > {self.refLayer}:{self.refTable}{self.refField}'
# /RelationItems


class MessageBoxes(Enum):
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
    def stylesheet():
        return STYLESHEET
    # /stylesheet

    def getVrtFiles(zip):
        vrtfiles = []
        for zipFile in zip.namelist():
            if zipFile.endswith('.vrt'):
                vrtfiles.append(zipFile)
        return vrtfiles
    # /getVrtFiles

    def getFields(tree, geometry, geofield, key):
        fields = []
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

    def getLatestInfoDate(d1, d2):
        if d1 and d2:
            if d1 < d2:
                return d2
        if d1:
            return d1
        return d2
    # /getLatestInfoDate

    def isNewer(zipDate, schemaDate):
        if schemaDate and zipDate:
            return (zipDate.date() > schemaDate)
        return True
    # /isNewer

    def isNull(value):
        if value:
            return (len(value) == 0)
        return True
    # /isNull

    def isTextField(type):
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
        if type:
            geotypes = [
                'POINT', 'MULTIPOINT',
                'LINESTRING', 'MULTILINESTRING',
                'POLYGON', 'MULTIPOLYGON',
                'GEOMETRY', 'GEOMETRYCOLLECTION']
            return type.upper() in geotypes
        return False
    # /isGeometryField

    def getTextValue(value, width):
        value = value.replace("'", "\\'")
        if width:
            if len(value) > int(width):
                value = value[0:int(width) - 1]
        value = "'" + value + "'"
        return value
    # /getTextValue

    def getGeometryValue(geometry, geotype, value):
        match geometry:
            case 'POINT':
                c1 = "ST_PointFromText"
            case 'LINESTRING':
                c1 = "ST_LineFromText"
            case 'POLYGON':
                c1 = "ST_PolyFromText"
            case 'MULTIPOINT':
                c1 = "ST_MPointFromText"
            case 'MULTILINESTRING':
                c1 = "ST_MLineFromText"
            case 'MULTIPOLYGON':
                c1 = "ST_MPolyFromText"
            case 'GEOMETRYCOLLECTION':
                c1 = "ST_GeomCollFromText"
            case 'GEOMETRY':
                c1 = "ST_GeomFromText"
            case _:
                c1 = "ST_GeomFromText'"
        # value = value.replace(',', ',\n')
        if geometry == 'MULTI' + geotype \
           or geometry == geotype + 'COLLECTION':
            value = value.replace(geotype, f'{geometry}(', 1) + ')'
            value = f"{c1}('{value})')"
        else:
            value = f"{c1}('{value}')"
        return value
    # /getGeometryValue

    def isFunction(sql):
        func = False
        f = sql.upper().split()
        if len(f) > 1:
            if f[0] == 'CREATE' or f[0] == 'ALTER' or f[0] == 'DROP':
                if f[1] == 'FUNCTION' or f[1] == 'PROCEDURE':
                    func = True
                else:
                    if len(f) > 3:
                        if f[1] == 'OR' \
                           and f[2] == 'REPLACE' \
                           and (f[3] == 'FUNCTION' or f[3] == 'PROCEDURE'):
                            func = True
        return func
    # /isFunction

    def isIgnore(sql):
        if sql:
            f = sql.upper().split()
            if len(f) > 8:
                if f[0] == 'ALTER' \
                   and f[1] == 'TABLE' \
                   and f[3] == 'ALTER' \
                   and f[4] == 'COLUMN' \
                   and f[6] == 'SET' \
                   and f[7] == 'STATISTICS':
                    return True
            if len(f) > 5:
                if f[0] == 'ALTER' \
                   and (f[1] == 'SCHEMA' or f[1] == 'DATABASE') \
                   and f[3] == 'OWNER' \
                   and f[4] == 'TO':
                    return True
            if len(f) > 1:
                if f[0] == 'DROP' \
                   and f[1] == 'FUNCTION':
                    return True
            if len(f) > 0:
                if f[0] == 'DO' \
                   or f[0] == 'BEGIN' \
                   or f[0] == 'END' \
                   or f[0] == 'SET' \
                   or f[0] == '$' \
                   or f[0] == ';':
                    return True
                if (f[0] == 'GRANT' or f[0] == 'REVOKE') \
                   and sql[len(sql) - 1] == ';':
                    return True
            return False
        return True
    # /isIgnore

    def isCreateSchema(sql):
        create = False
        f = sql.upper().split()
        if len(f) > 1:
            if f[0] == 'CREATE' \
               and (f[1] == 'SCHEMA' or f[1] == 'DATABASE'):
                create = True
        return create
    # /isCreateSchema

    def createTablename(sql):
        tablename = None
        f = sql.split()
        if len(f) > 5:
            if f[0].upper() == 'CREATE' \
               and f[1].upper() == 'TABLE' \
               and f[2].upper() == 'IF' \
               and f[3].upper() == 'NOT' \
               and f[4].upper() == 'EXISTS':
                tablename = f[5]
        elif len(f) > 1:
            if f[0].upper() == 'CREATE' \
               and f[1].upper() == 'TABLE':
                tablename = f[2]
        return tablename
    # /createTablename

    def createViewname(sql):
        viewname = None
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
        f = sql.split()
        if len(f) > 1:
            if f[0].upper() == 'DROP':
                return True
        return False
    # /isDropSql

    def sqlTranslate(sql):
        sqlT = sql.replace("$DESC$", "'").replace('\t', ' ') \
            .replace('\n', ' ')
        f = sql.split()
        if len(f) > 5:
            if f[0].upper() == 'COMMENT' \
               and f[1].upper() == 'ON' \
               and f[2].upper() == 'SCHEMA' \
               and f[4].upper() == 'IS':
                c1 = sql.upper().find(' IS ') + 4
                sqlT = f'ALTER SCHEMA {f[3]} comment=' \
                    '{sql[c1:len(sql)].lstrip().rstrip()}'
            if f[0].upper() == 'COMMENT' \
               and f[1].upper() == 'ON' \
               and f[2].upper() == 'TABLE' \
               and f[4].upper() == 'IS':
                c1 = sql.find("$DESC$")
                if (c1 >= 0 and c1 < len(sql) - 6):
                    c2 = sql.find("$DESC$", c1 + 6)
                    if c2 < 0:
                        c2 = len(sql)
                    comment = f"'{sql[c1 + 6:c2].lstrip().rstrip()}'"
                else:
                    c1 = sql.find("'")
                    if (c1 >= 0):
                        c2 = sql.find("'", c1 + 1)
                        comment = f"'{sql[c1 + 1:c2].lstrip().rstrip()}'"
                    else:
                        comment = f"'{sqlT[5:len(sqlT)].lstrip().rstrip()}'"
                comment = comment.replace('\n', ' ')
                sqlT = f'ALTER TABLE {f[3].lower()} comment={comment};'
        if len(f) > 1:
            if (f[0].upper() == 'CREATE' or f[0].upper() == 'ALTER') \
               and f[1].upper() == 'TABLE':
                sqlT = Utilities.varcharTranslate(sqlT)
                sqlT = sqlT \
                    .replace('character varying', 'TEXT') \
                    .replace('CHARACTER VARYING', 'TEXT') \
                    .replace('"order"', 'orderby') \
                    .replace('"name"', 'name') \
                    .replace('"current"', 'current') \
                    .replace('"default"', 'isdefault') \
                    .replace('"desc"', 'description') \
                    .replace('"type"', 'type') \
                    .replace('"constraint"', 'conditions') \
                    .replace(' condition ', ' conditions ') \
                    .replace(',condition ', ',conditions ') \
                    .replace('(condition ', '(conditions ') \
                    .replace(' without time zone', ' ')
                sqlT = Utilities.geometryTranslate(sqlT)
        # print("\n" + sql + "\n" + sqlT)
        return sqlT
    # /sqlTranslate

    def varcharTranslate(sql):
        sqlT = sql.replace('VARCHAR (', 'VARCHAR(') \
            .replace('varchar(', 'VARCHAR(') \
            .replace('varchar (', 'VARCHAR(')
        v = sqlT.upper().find('VARCHAR(', 0)
        while v > 0:
            v1 = sqlT.upper().find('(', v) + 1
            v2 = sqlT.upper().find(')', v)
            size = int(sqlT[v1:v2])
            if size > 1024:
                sqlT = sqlT[0: v] + 'TEXT' + sqlT[v1 - 1:len(sqlT)]
            v = sqlT.upper().find('VARCHAR(', v1)
        return sqlT
    # /varcharTranslate

    def geometryTranslate(sql):
        sqlT = sql.replace('geometry (', 'geometry(')
        while sqlT.upper().find('GEOMETRY(') > 0:
            g1 = sqlT.upper().find('GEOMETRY(')
            g2 = g1 + 9
            h1 = sqlT.upper().find(',', g2)
            h2 = sqlT.upper().find(')', g2) + 1
            sqlT = sqlT[0:g1] + sqlT[g2:h1].upper() + sqlT[h2:len(sqlT)]
        return sqlT
    # /geometryTranslate

    def getNow():
        return datetime.datetime.now().replace(microsecond=0)
    # /getNow

    def getNowString():
        return Utilities.getNow().strftime('%d/%m/%y %H:%M:%S')
    # /getNowString

    def getElapsedTime(startTime):
        now = Utilities.getNow()
        elapsed = now - startTime
        return elapsed
    # /getElapsedTime

    def getRemainingTime(startTime, fcnt, cnt):
        if cnt == 0:
            return "unknown"
        elapsed = Utilities.getElapsedTime(startTime)
        remainingTime = (((fcnt / cnt) * elapsed) - elapsed)
        remainingTime -= \
            datetime.timedelta(microseconds=remainingTime.microseconds)
        return f"{remainingTime}"
    # /getRemainingTime

    def getTreeText(tree, branch, index, default=None):
        text = default
        if branch:
            for source in tree.iter(branch):
                text = source.attrib.get(f'{index}')
        else:
            for source in tree.iter(f'{index}'):
                text = source.text
        return text
    # /getTreeText

    def getTreeInt(tree, branch, index, default=0):
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
        if path:
            s = path.rfind("/")
            if s < 1:
                return ""
            return path[0:s]
        return None
    # /getPathDirectory

    def getPathFile(path):
        if path:
            e = path.rfind(".")
            if e < 1:
                e = len(path)
            s = path.rfind("/")
            return path[s + 1:e]
        return None
    # /getPathFile

    def getPathExt(path):
        if path:
            e = path.rfind(".")
            if e < 1:
                return ""
            return path[e + 1:len(path)]
        return None
    # /getPathExt

    def getCsvFilepath(zip, csvFileName):
        fileName = csvFileName
        for f in zip.namelist():
            if f.endswith(csvFileName):
                fileName = f
        return fileName
    # /getCsvFilepath

    def copyFolder(parent, src, dst):
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
        if isinstance(parent, QMainWindow):
            return parent.getAppname()
        else:
            return parent.parent.getAppname()
    # /getAppname

    def getApptitle(parent):
        if isinstance(parent, QMainWindow):
            return Utilities.getMetadata(
                parent.metadata, 'general', 'name')
        else:
            return Utilities.getMetadata(
                parent.parent.metadata, 'general', 'name')
    # /getApptitle

    def readMetadata(parent):
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


class QGISUtilities():
    def getRecentPath(parent):
        if not HAS_QGIS:
            return None
        if parent.recentPath:
            return parent.recentPath
        recentPath = None
        if isinstance(parent.app, QgsApplication):
            settings = QSettings()
        else:
            settings = QgsSettings()
        keys = settings.allKeys()
        for key in keys:
            # parent.appendLog(f'key {key} : {settings.value(key)}')
            if key.startswith('UI/recentProjects/') and key.endswith('/path') \
               and recentPath is None:
                path = settings.value(key)
                if path and isinstance(path, str):
                    (recentPath, file) = os.path.split(path)
        if recentPath:
            return recentPath
        settingsFile = settings.fileName()
        s = settingsFile.find('share')
        v = Qgis.version().split('.')
        version = 'QGIS' + v[0]
        if settingsFile.find('Unknown') and s:
            s += 5
            settingsFile = settingsFile[0:s]
            settingsFile = os.path.join(settingsFile, 'QGIS', version,
                                        'profiles', 'default', 'QGIS')
            settingsFile += os.path.sep + version + '.ini'
        if os.path.isfile(settingsFile):
            try:
                # parent.appendLog(f'settingsFile {settingsFile}')
                config = configparser.ConfigParser()
                config.read(settingsFile)
                configSection = config['UI']
                recentPath = configSection['lastProjectDir']
            except KeyError as err:
                parent.appendLog(f'Config Error reading {settingsFile} : {err}')
        return recentPath
    # /getRecentPath

    def getProjectTitle(project, projectFile):
        if project and project.title() and len(project.title()) > 0:
            return project.title()
        (path, filename) = os.path.split(projectFile)
        (title, ext) = os.path.splitext(filename)
        return title.title().replace("Nz", "NZ").replace("Linz", "LINZ")
    # /getProjectTitle
# /QGISUtilities
