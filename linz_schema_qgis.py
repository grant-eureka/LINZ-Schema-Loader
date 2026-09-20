# Created on : Dec 26, 2025, 3:07:23 PM
# linz_schema_qgis.py
# Author     : Grant
# Module for handling QGIS utility routines

import os
import configparser
from urllib.parse import urlsplit
import importlib.util

if importlib.util.find_spec("PyQt"):
    # from PyQt import uic, loadUi
    # from PyQt import QtGui, QtWidgets, QtCore
    from PyQt import (
        QSettings)
else:
    # from .PyQt import uic, loadUi
    # from .PyQt import QtGui, QtWidgets, QtCore
    from .PyQt import (
        QSettings)

if importlib.util.find_spec("qgis"):
    from qgis.core import Qgis
    from qgis.core import QgsApplication
    from qgis.core import QgsSettings
    HAS_QGIS = True
else:
    HAS_QGIS = False

if importlib.util.find_spec("linz_schema_utilities"):
    from linz_schema_database import Database, SourceConfig
else:
    from .linz_schema_database import Database, SourceConfig

DATABASES = ["mysql", "mariadb"]
FILESOURCES = ["sqlite", "gpkg",
               "csv"]


class NullClass():
    """Empty class for when qgis module not found
    """


class RelationItems():
    """Class that contains relationship definitions.
    """

    def __init__(self,
                 primaryLayer, primaryField,
                 refLayer, refField):
        self.primaryLayer = primaryLayer
        self.primaryField = primaryField
        self.refLayer = refLayer
        self.refField = refField

    def __str__(self):
        return self.text()

    def primaryLayer(self):
        return self.primaryLayer

    def primaryField(self):
        return self.primaryField

    def refLayer(self):
        return self.refLayer

    def refField(self):
        return self.refField

    def text(self):
        return f'{self.primaryLayer} ({self.primaryField})' \
               f' > {self.refLayer} ({self.refField})'
# /RelationItems


class QGISUtilities():
    """Utilities class for handling QGIS utility routines
    """
    def getRecentPath(parent):
        """Get the most recently used path from QGIS projects.
        :param parent: The calling parent object.
        :type parent: Object

        :returns: The most resent path name.
        :rtype: Str
        """
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
            # parent.appendLog(f'key {key} : {settings.value(key)}')  # debug
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
                # parent.appendLog(f'settingsFile {settingsFile}')  # debug
                config = configparser.ConfigParser()
                config.read(settingsFile)
                configSection = config['UI']
                recentPath = configSection['lastProjectDir']
            except KeyError as err:
                parent.appendLog(f'Config Error reading {settingsFile} : {err}')
        return recentPath
    # /getRecentPath

    def getProjectTitle(project, projectFile):
        """Get the title of a QGIS projects.
        :param parent: The calling parent object.
        :type parent: Object

        :param projectFile: The path to a QGIS project file.
        :type projectFile: Str

        :returns: The title of a project.
        :rtype: Str
        """
        if project and project.title() and len(project.title()) > 0:
            return project.title()
        (path, filename) = os.path.split(projectFile)
        (title, ext) = os.path.splitext(filename)
        return title.title().replace("Nz", "NZ").replace("Linz", "LINZ")
    # /getProjectTitle

    def isDatabase(storageType):
        """Test if a layer source type is a supported database
        :param storageType: Data source database type.
        :type storageType: str

        :returns: True if database source type is supported.
        :rtype: Boolean
        """
        if storageType:
            if storageType.lower() in DATABASES:
                return True
        return False
    # /isDatabase

    def isFileSource(storageType):
        """Test if a layer source type is a supported database
        :param storageType: Data source database type.
        :type storageType: str

        :returns: True if database source type is supported.
        :rtype: Boolean
        """
        if storageType:
            if storageType.lower() in FILESOURCES:
                return True
        return False
    # /isFileSource

    def extractSourceURI(storageType, uriComponents):
        """Extract source connection information from a
        vector layer source URI
        :param storageType: Data source database type.
        :type storageType: str

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        # print(f'extractSourceURI\nuriComponents:\n\t{uriComponents}')
        if uriComponents:
            # print(f'storageType={storageType} : '
            #       'isDatabase={QGISUtilities.isDatabase(storageType)}')
            s = storageType.upper()
            if QGISUtilities.isDatabase(storageType):
                if s == "ODBC":
                    return QGISUtilities.extractODBCSourceURI(
                        storageType, uriComponents)
                else:
                    return QGISUtilities.extractDatabaseSourceURI(
                        storageType, uriComponents)
            elif QGISUtilities.isFileSource(storageType):
                return QGISUtilities.extractFileSourceURI(
                    storageType, uriComponents)
            elif s == "GPX" or s == "ESRI SHAPEFILE":
                return QGISUtilities.extractShapeSourceURI(
                    storageType, uriComponents)
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        return sourceConfig
    # /extractSourceURI

    def extractODBCSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        ODBC layer source URI
        :param storageType: Data source database type.
        :type storageType: str

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        urlParts = urlsplit(uriComponents["path"])
        username = None
        password = None
        path = uriComponents['databaseName']
        if path is None:
            path = urlParts.path
        sourceConfig.setKey('path', path)
        if path:
            sep = path.find('@')
            length = len(path)
            if sep == 0:
                path = path[1:length]
            elif sep > 0:
                authentication = path[0:sep]
                path = path[sep + 1:length]
                sep = authentication.find('/')
                length = len(authentication)
                if sep == 0:
                    username = authentication[1:length]
                elif sep > 0:
                    username = authentication[0:sep]
                    password = authentication[sep + 1:length]
        sourceConfig.setKey('username', username)
        sourceConfig.setKey('password', password)
        sourceConfig.setKey('databasename', path)
        tableName = uriComponents['layerName']
        sourceConfig.setKey('tablename', tableName)
        if urlParts.hostname:
            sourceConfig.setKey('hostname', urlParts.hostname)
        if urlParts.port:
            sourceConfig.setKey('port', urlParts.port)
        return sourceConfig
    # /extractODBCSourceURI

    def extractDatabaseSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        database layer source URI
        :param storageType: Data source database type.
        :type storageType: str

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        try:
            databaseName = uriComponents['databaseName']
            sourceConfig.setKey('databasename', databaseName)
            urlParts = urlsplit(uriComponents['path'])
            path = urlParts.path
            sourceConfig.setKey('path', path)
            if urlParts.username:
                sourceConfig.setKey('username', urlParts.username)
            if urlParts.password:
                sourceConfig.setKey('password', urlParts.password)
            if urlParts.hostname:
                sourceConfig.setKey('hostname', urlParts.hostname)
            if urlParts.port:
                sourceConfig.setKey('port', urlParts.port)
            else:
                sourceConfig.setKey(
                    'port', Database.defaultPort(storageType.lower()))
            components = path.split(',')
            for component in components:
                if component.find('=') > 0:
                    c = component.split('=', 1)
                    sourceConfig.setKey(c[0], c[1])
        except KeyError:
            pass
        return sourceConfig
    # /extractDatabaseSourceURI

    def extractFileSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        file source URI
        :param storageType: Data source database type.
        :type storageType: str

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        databaseName = uriComponents['path']
        sourceConfig.setKey('databasename', databaseName)
        urlParts = urlsplit(uriComponents["path"])
        path = urlParts.path
        sourceConfig.setKey('path', path)
        return sourceConfig
    # /extractFileSourceURI

    def extractShapeSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        file source URI
        :param storageType: Data source database type.
        :type storageType: str

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """

        # print(f'\tstorageType={storageType}\t{uriComponents}')
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        try:
            path = uriComponents['vsiSuffix']
        except KeyError:
            path = uriComponents['path']
        if path:
            (root, ext) = os.path.splitext(path)
            (root, file) = os.path.split(root)
            sourceConfig.setKey('path', file)
        # print(f'path={path}\troot={root}\tfile={file}\text={ext}')
        return sourceConfig
    # /extractShapeSourceURI
# /QGISUtilities
