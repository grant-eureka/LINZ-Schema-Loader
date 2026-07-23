# Created on : Dec 26, 2025, 3:07:02 PM
# Author     : Grant

import os
import platform
import zipfile
import csv
import codecs
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
    from linz_schema_utilities import (
        MessageBoxes, Utilities, QGISUtilities, RelationItems)
    from linz_schema_database import Database
else:
    from .linz_schema_utilities import (
        MessageBoxes, Utilities, QGISUtilities, RelationItems)
    from .linz_schema_database import Database

if importlib.util.find_spec("qgis"):
    from qgis.core import (
        Qgis, QgsProject, QgsProviderRegistry,
        QgsApplication,
        QgsMapLayer, QgsVectorLayer, QgsLayerTreeLayer,
        QgsRelation,
        QgsCoordinateReferenceSystem,
        QgsStyle,
        QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer,
        QgsRuleBasedRenderer,
        QgsReadWriteContext, QgsRenderContext,
        QgsAbstractVectorLayerLabeling, QgsFeatureRenderer)
    # from qgis.core import QgsDataSourceUri
    # from qgis.gui import QgisInterface
    HAS_QGIS = True
else:
    HAS_QGIS = False


class Counters():
    """'Type' definition for database field.
    """
    EXIST_FEATURES = 0
    EXIST_TABLES = 1
    EXIST_VIEWS = 2
    EXIST_TOTAL = 4
    NEW_FEATURES = 8
    NEW_TABLES = 16
    NEW_VIEWS = 32
    NEW_TOTAL = 64

    existFeatures = 0
    existTables = 0
    existViews = 0
    existTotal = 0
    newFeatures = 0
    newTables = 0
    newViews = 0
    newTotal = 0

    def __init__(self):
        self.existFeatures = 0
        self.existTables = 0
        self.existViews = 0
        self.existTotal = 0
        self.newFeatures = 0
        self.newTables = 0
        self.newViews = 0
        self.newTotal = 0

    def __str__(self):
        return f'Total existing : {self.existTotal} ' \
               f'Total new : {self.newTotal}'

    def increment(self, field):
        match field:
            case self.EXIST_FEATURES:
                self.existFeatures += 1
                self.existTotal += 1
            case self.EXIST_TABLES:
                self.existTables += 1
                self.existTotal += 1
            case self.EXIST_VIEWS:
                self.existViews += 1
                self.existTotal += 1
            case self.EXIST_TOTAL:
                self.existTotal += 1
            case self.NEW_FEATURES:
                self.newFeatures += 1
                self.newTotal += 1
            case self.NEW_TABLES:
                self.newTables += 1
                self.newTotal += 1
            case self.NEW_VIEWS:
                self.newViews += 1
                self.newTotal += 1
            case self.NEW_TOTAL:
                self.newTotal += 1
    # /increment
# /Counters


class FeaturesActions():
    def __init__(self):
        super().__init__()
    # /__init__

    def init(self):
        pass
    # /init

    def processLayers(self, parent, sourceConfig, cnx, schemaname):
        parent.appendLog(f'\nCreating vector layers for {schemaname}...')
        (project, title) = self.openProject(parent, cnx, schemaname)
        if project is None:
            return
        parent.setCursor(Qt.CursorShape.WaitCursor)
        group = self.createGroups(QgsProject.instance(), schemaname)

        url = f'MySQL:{schemaname},' \
              f'host={sourceConfig.get("hostname")},' \
              f'port={sourceConfig.get("port")},' \
              f'user={sourceConfig.get("username")},' \
              f'password={sourceConfig.get("password")}'
        tables = self.getTables(parent, cnx, schemaname)
        counters = Counters()
        for table in tables:
            layers = self.getTableLayers(
                "mysql", schemaname, table[1])
            if len(layers) == 0:
                parent.appendLog('    create vector layer for table '
                                 f'{table[1]}...')
                layerName = table[1].replace("_", " ").title() \
                    .replace("Nz", "NZ").replace("Linz", "LINZ")
                uri = f'{url},tables={table[1]}'
                cnt = Database.getTableMetadataCount(
                    parent, cnx, schemaname, table[1])
                if cnt >= 16384:
                    uri += ',useEstimatedMetadata=True'

                # uri.setGeometryColumn(parent, geometryColumn: str | None)
                # uri.setKeyColumn(parent, column: str | None)
                # uri.setSrid(parent, srid: str | None)
                layer = QgsVectorLayer(uri, layerName, "ogr")
                crs = self.getLayerCRS(parent, cnx, schemaname, table[1])
                if crs:
                    parent.appendLog('        coordinate reference system '
                                     f'{crs.description()}'
                                     f' ({crs.authid()})')
                    layer.setCrs(crs)
                self.addLayer(parent, schemaname, table, group, layer, counters)
                parent.appendLog(f'        created layer "{layerName}"')
            else:
                if table[2] == 1:
                    counters.increment(counters.EXIST_FEATURES)
                elif table[0] == 'BASE TABLE':
                    counters.increment(counters.EXIST_TABLES)
                elif table[0] == 'VIEW':
                    counters.increment(counters.EXIST_VIEWS)
                else:
                    counters.increment(counters.EXIST_TOTAL)
                parent.appendLog(f'    vector layer "{layers[0].name()}" '
                                 f'already exists for table {table[1]}')
        parent.appendLog(f'    new feature layers:\t{counters.newFeatures}')
        parent.appendLog(f'    new table layers: \t{counters.newTables}')
        parent.appendLog(f'    new view layers:  \t{counters.newViews}')
        parent.appendLog(f'    total new layers: \t{counters.newTotal}')
        parent.appendLog('    existing feature layers:\t'
                         f'{counters.existFeatures}')
        parent.appendLog(f'    existing table layers: \t{counters.existTables}')
        parent.appendLog(f'    existing view layers:  \t{counters.existViews}')
        parent.appendLog(f'    total existing layers: \t{counters.existTotal}')
        parent.appendLog(f'Finished creating vector layers for {schemaname}')
        parent.appendLog('Wait for QGIS to process new map layers!')
        self.saveProject(parent, project, title)
        parent.unsetCursor()
    # /processLayers

    def openProject(self, parent, cnx=None, schemaname=None):
        if not HAS_QGIS:
            return (None, None)
        project = QgsProject.instance()
        if len(project.fileName()) == 0:
            recentPath = QGISUtilities.getRecentPath(parent)
            if recentPath is None:
                recentPath = Path.home()
            (projectFile, selectedFilter) = MessageBoxes.saveFileBox(
                parent,
                f'{Utilities.getApptitle(parent)} : Save Project to...',
                f'{recentPath}', "Projects (*.qgs *.qg)")
            if projectFile is None or len(projectFile) == 0:
                parent.appendLog("Project file not defined: exiting")
                return (None, None)
            (projectPath, projectFilename) = os.path.split(projectFile)
            # (title, ext) = os.path.splitext(projectFilename)
            parent.setRecentPath(projectPath)
            if os.path.isfile(projectFile):
                project.read(projectFile)
                title = QGISUtilities.getProjectTitle(project, projectFile)
                project.setTitle(title)
                parent.appendLog(f'    using existing project {title}')
            else:
                project.setFileName(projectFile)
                title = QGISUtilities.getProjectTitle(project, projectFile)
                project.setTitle(title)
                parent.appendLog(f'    creating new project {title}')
                if cnx and schemaname:
                    crs = self.getProjectCRS(parent, cnx, schemaname)
                    if crs:
                        parent.appendLog('        coordinate reference system '
                                         f'{crs.description()}'
                                         f' ({crs.authid()})')
                        QgsProject.instance().setCrs(crs)
        else:
            projectFile = project.fileName()
            (projectPath, projectFilename) = os.path.split(projectFile)
            title = QGISUtilities.getProjectTitle(project, projectFile)
            project.setTitle(title)
            parent.appendLog(f'    using existing project {title}')
        return (project, title)
    # /openProject

    def saveProject(self, parent, project, title):
        if parent.isPlugin:
            parent.appendLog("**** Save changes in project from QGIS")
        else:
            if project:
                parent.appendLog(f"Save project to {project.fileName()}...")
                if project.write():
                    parent.appendLog(f"Project '{title}' saved")
                else:
                    parent.appendLog(f"Unable to save project '{title}'")
                if not parent.isPlugin:
                    project.clear()
    # /saveProject

    def getProjectCRS(self, parent, cnx, schemaname):
        sql = "select g.srid, s.srtext, count(g.f_table_name) as cnt " \
              f"from {schemaname}.geometry_columns as g " \
              f"inner join {schemaname}.spatial_ref_sys as s" \
              " on s.srid=g.srid " \
              "group by g.srid, s.srtext " \
              "order by cnt desc " \
              "limit 1;"
        crss = Database.readDatabase(parent, cnx, sql)
        lcrs = None
        for crs in crss:
            lcrs = QgsCoordinateReferenceSystem(crs[1])
            if lcrs is None:
                lcrs = QgsCoordinateReferenceSystem.createFromWkt(crss[1])
        return lcrs

    # /getProjectCRS

    def getLayerCRS(self, parent, cnx,
                    schemaname, tablename):
        sql = "select g.srid, s.srtext " \
              f"from {schemaname}.geometry_columns as g " \
              f"inner join {schemaname}.spatial_ref_sys as s" \
              " on s.srid=g.srid " \
              f"where g.f_table_schema='{schemaname}' " \
              f"and g.f_table_name='{tablename}';"
        crss = Database.readDatabase(parent, cnx, sql)
        lcrs = None
        for crs in crss:
            lcrs = QgsCoordinateReferenceSystem(crs[1])
            if lcrs is None:
                lcrs = QgsCoordinateReferenceSystem.createFromWkt(crss[1])
        return lcrs
    # /getLayerCRS

    def addLayer(self, parent, schemaname, table, group, layer, counters):
        if parent.iface:
            parent.iface.mainWindow().blockSignals(True)
        QgsProject.instance().addMapLayer(layer, False)
        if group:
            if table[2] == 1:
                subGroup = group.findGroup('Features')
                subGroup.addChildNode(QgsLayerTreeLayer(layer))
                counters.increment(counters.NEW_FEATURES)
            elif table[0] == 'BASE TABLE':
                subGroup = group.findGroup('Tables')
                subGroup.addChildNode(QgsLayerTreeLayer(layer))
                counters.increment(counters.NEW_TABLES)
            elif table[0] == 'VIEW':
                subGroup = group.findGroup('Views')
                subGroup.addChildNode(QgsLayerTreeLayer(layer))
                counters.increment(counters.NEW_VIEWS)
            else:
                group.addChildNode(QgsLayerTreeLayer(layer))
                counters.increment(counters.NEW_TOTAL)
        else:
            QgsProject.instance().addMapLayer(layer)
            if table[2] == 1:
                counters.increment(counters.NEW_FEATURES)
            elif table[0] == 'BASE TABLE':
                counters.increment(counters.NEW_TABLES)
            elif table[0] == 'VIEW':
                counters.increment(counters.NEW_VIEWS)
            else:
                counters.increment(counters.NEW_TOTAL)
        QgsProject.instance().layerTreeRoot() \
            .findLayer(layer.id()).setItemVisibilityChecked(False)
        if parent.iface:
            parent.iface.mainWindow().blockSignals(False)
    # /addLayer

    def createGroups(self, project, schemaname):
        root = project.layerTreeRoot()
        group = root.findGroup(schemaname)
        if not group:
            group = root.addGroup(schemaname)
        if not group.findGroup('Features'):
            group.addGroup('Features')
        if not group.findGroup('Tables'):
            group.addGroup('Tables')
        if not group.findGroup('Views'):
            group.addGroup('Views')
        return group
    # /createGroups

    def getTables(self, parent, cnx, schemaname):
        sql = "select t.table_type, t.table_name, " \
              "sum(case c.column_type when 'point' then 1 " \
              "when 'linestring' then 1 when 'polygon' then 1 " \
              "when 'multipoint' then 1 when 'multilinestring' then 1 " \
              "when 'multipolygon' then 1 when 'geometrycollection' then 1 " \
              "when 'geometry' then 1 else 0 end) as geometries " \
              "from information_schema.TABLES as t " \
              "inner join information_schema.COLUMNS c " \
              "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
              "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
              "AND c.TABLE_NAME = t.TABLE_NAME " \
              f"where t.TABLE_SCHEMA='{schemaname}' " \
              "AND t.table_name !='geometry_columns' " \
              "AND t.table_name !='spatial_ref_sys' " \
              "AND t.table_name !='table_datasets' " \
              "group by t.table_type, t.table_name " \
              "order by geometries desc, t.table_type asc, t.TABLE_NAME asc;"
        tables = Database.readDatabase(parent, cnx, sql)
        return tables
    # /getTables

    def processRelations(self, parent, cnx, schemaname):
        parent.appendLog(f'\nDefine relationships for {schemaname}...')
        (project, title) = self.openProject(parent, cnx, schemaname)
        if project is None:
            return
        parent.setCursor(Qt.CursorShape.WaitCursor)

        existingRelations = self.getRelations(parent, schemaname)

        csvFileName = 'linz_schema_joins.csv'
        try:
            csvFile = open(csvFileName, 'r', newline='', encoding="utf-8-sig")
            reader = csv.reader(csvFile, delimiter=',')
            parent.appendLog(f'    {csvFileName} found')
            self.processRelationsFile(
                parent, cnx, schemaname, reader, existingRelations)
            csvFile.close()
            parent.appendLog(f'Defined relationships for {schemaname}')
        except IOError:
            try:
                (root, ext) = os.path.split(__file__)
                (file, ext) = os.path.splitext(root)
                if ext == '.zip' or ext == '.pyz':
                    with zipfile.ZipFile(root, 'r') as zip:
                        csvFile = zip.open(csvFileName, 'r')
                        parent.appendLog(f'    zipped {csvFileName} found')
                        reader = csv.reader(codecs.iterdecode(csvFile, 'utf-8'))
                        self.processRelationsFile(
                            parent, cnx, schemaname, reader, existingRelations)
                        csvFile.close()
                        parent.appendLog(
                            f'Defined relationships for {schemaname}')
                else:
                    (root, file) = os.path.split(__file__)
                    csvFile = open(os.path.join(root, csvFileName), 'rt')
                    reader = csv.reader(csvFile, delimiter=',')
                    parent.appendLog(f'    {csvFileName} found')
                    self.processRelationsFile(
                        parent, cnx, schemaname, reader, existingRelations)
                    csvFile.close()
                    parent.appendLog(f'Defined relationships for {schemaname}')
            except IOError as err:
                parent.appendLog(
                    f'Failed to read relationships file {csvFileName}'
                    f'\n{err}')
        self.saveProject(parent, project, title)
        parent.unsetCursor()
    # /processRelations

    def processRelationsFile(self, parent, cnx,
                             schemaname, reader, existingRelations):
        cnt = -1
        new = 0
        old = 0
        for row in reader:
            if row:
                if cnt > 0:
                    primaryTable = row[0]
                    primaryLayers = self.getTableLayers(
                        "mysql", schemaname, primaryTable)
                    primaryField = row[1]
                    isPrimaryTable = Database.isTableExist(
                        parent, cnx, schemaname, primaryTable)
                    refTable = row[2]
                    refLayers = self.getTableLayers(
                        "mysql", schemaname, refTable)
                    refField = row[3]
                    isRefTable = Database.isTableExist(
                        parent, cnx, schemaname, refTable)
                    if len(primaryLayers) > 0 and isPrimaryTable and \
                       len(refLayers) > 0 and isRefTable:
                        for primaryLayer in primaryLayers:
                            for refLayer in refLayers:
                                if self.isRelationExist(
                                   existingRelations,
                                   primaryLayer, primaryField,
                                   refLayer, refField):
                                    old += 1
                                else:
                                    rel = QgsRelation()
                                    rel.setReferencedLayer(primaryLayer.id())
                                    rel.setReferencingLayer(refLayer.id())
                                    rel.addFieldPair(refField, primaryField)
                                    name = f'{primaryLayer.name()}.' \
                                        f'{primaryField} : ' \
                                        f'{refLayer.name()}.' \
                                        f'{refField}'
                                    rel.setName(name)
                                    rel.setStrength(
                                        Qgis.RelationshipStrength.Association)
                                    rel.generateId()
                                    if rel.isValid():
                                        parent.appendLog('    create relation '
                                                         f'{name}')
                                        QgsProject.instance() \
                                            .relationManager().addRelation(rel)
                                        new += 1
                                    else:
                                        log = '    invalid relation:\n' \
                                              f'{primaryLayer.name()}:' \
                                              f'{primaryTable}.' \
                                              f'{primaryField} ' \
                                              f'=> {refLayer.name()}:' \
                                              f'{refTable}.{refField}'
                                        parent.appendLog(log)
                cnt += 1
        parent.appendLog(f'    {cnt} relations read.')
        parent.appendLog(f'    {old} releations already defined.')
        parent.appendLog(f'    {new} new relations defined.')
    # /processRelationsFile

    def isRelationExist(self, existingRelations,
                        primaryLayer, primaryField, refLayer, refField):
        # for existingRelation in existingRelations:
        #     print(existingRelation)
        # print(f"    {primaryLayer.name()}, {primaryField}, "
        #       f"{refLayer.name()}, {refField}")
        for relation in existingRelations:
            if relation.primaryLayer == primaryLayer.name() and \
               relation.primaryField == primaryField and \
               relation.refLayer == refLayer.name() and \
               relation.refField == refField:
                return True
            if relation.primaryLayer == refLayer.name() and \
               relation.primaryField == refField and \
               relation.refLayer == primaryLayer.name() and \
               relation.refField == primaryField:
                return True
        return False
    # /isRelationExist

    def getRelations(self, parent, schemaname):
        #   Get existing relations
        parent.appendLog('    Get existing relations...')
        relationItems = []
        relationNames = QgsProject.instance().relationManager().relations()
        for relationName in relationNames:
            relation = QgsProject.instance().relationManager().relation(
                relationName)
            kField = next(iter(relation.fieldPairs().keys()))
            vField = next(iter(relation.fieldPairs().values()))
            kStorageType = relation.referencedLayer().storageType()
            vStorageType = relation.referencingLayer().storageType()
            # parent.appendLog(f'referencedLayer type {storageType}')
            isDatabase = Database.isDatabase(kStorageType) \
                and Database.isDatabase(vStorageType) \
                and kStorageType == vStorageType
            if isDatabase:
                layers = QgsProject.instance().mapLayersByName(
                    relation.referencedLayer().name())
                if layers:
                    primaryLayer = layers[0]
                uriComponents = QgsProviderRegistry.instance().decodeUri(
                    primaryLayer.dataProvider().name(),
                    primaryLayer.source())
                sourceConfig = Database.extractDatabaseSourceURI(
                    kStorageType,
                    uriComponents)
                primaryTable = sourceConfig.get("tablename")
                primarySchema = sourceConfig.get("databasename")

                layers = QgsProject.instance().mapLayersByName(
                    relation.referencingLayer().name())
                if layers:
                    refLayer = layers[0]
                uriComponents = QgsProviderRegistry.instance().decodeUri(
                    refLayer.dataProvider().name(),
                    refLayer.source())
                sourceConfig = Database.extractDatabaseSourceURI(
                    vStorageType,
                    uriComponents)
                refTable = sourceConfig.get("tablename")
                refSchema = sourceConfig.get("databasename")

                isSchemas = primarySchema == schemaname and \
                    refSchema == schemaname
                if isSchemas:
                    relationItem = RelationItems(
                        relation.referencedLayer().name(), primaryTable,
                        vField,
                        relation.referencingLayer().name(), refTable,
                        kField)
                    relationItems.append(relationItem)

        # for relationItem in relationItems:
        #     parent.appendLog(f'{relationItem.primaryTable}.'
        #                    f'{relationItem.primaryField} > '
        #                    f'{relationItem.refTable}.'
        #                    f'{relationItem.refField}')
        parent.appendLog(f'    {len(relationItems)} existing relations.')
        return relationItems
    # /getRelations

    def getTableLayers(self, storageType, schemaname, tablename):
        layers = QgsProject.instance().mapLayers().values()
        tableLayers = list()
        for layer in layers:
            if layer.type() == QgsMapLayer.LayerType.VectorLayer:
                lStorageType = layer.storageType().lower()
                if lStorageType == storageType:
                    uriComponents = QgsProviderRegistry.instance().decodeUri(
                        layer.dataProvider().name(),
                        layer.source())
                    sourceConfig = Database.extractDatabaseSourceURI(
                        storageType,
                        uriComponents)
                    sourceTable = sourceConfig.get("tablename")
                    sourceSchema = sourceConfig.get("databasename")
                    if sourceSchema == schemaname and sourceTable == tablename:
                        tableLayers.append(layer)
        return tableLayers
    # /getTableLayers

    ########################################################

    def processLoadLayerStyles(self, parent, cnx, schemaname):
        parent.appendLog('\nDefine map styles for current project...')
        (project, title) = self.openProject(parent, cnx, schemaname)
        if project is None:
            return
        if MessageBoxes.messageBox(
           parent,
           MessageBoxes.QUESTION,
           Utilities.getApptitle(parent),
           f'Layer style in project "{project.fileName()}"\n'
           'will be over-written.\n\n'
           'Load new styles for project?',
           MessageBoxes.YES_NO) != MessageBoxes.YES.value:
            return
        parent.setCursor(Qt.CursorShape.WaitCursor)
        projectFile = project.fileName()
        (projectPath, projectFilename) = os.path.split(projectFile)
        imageFolder = os.path.join(projectPath, 'nz-topo-images')
        try:
            parent.appendLog(f"Create style images folder {imageFolder}")
            os.makedirs(imageFolder, exist_ok=True)
        except (OSError, IOError) as err:
            msg = f"Failed to create style images folder {imageFolder}\n{err}"
            parent.appendLog(f'{msg}')
            parent.unsetCursor()
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                msg)
            return
        self.extractTopoImageFiles(parent, imageFolder)
        self.updateTopoProjectStyles(parent, imageFolder, projectFile)
        self.saveProject(parent, project, title)
        parent.unsetCursor()
    # /processLoadLayerStyles

    ########################################################

    def processTopoStyles(self, parent, cnx, schemaname):
        parent.appendLog(
            '\nCreating NZ topo map style database for all projects...')
        (project, title) = self.openProject(parent, cnx, schemaname)
        if project is None:
            return
        parent.setCursor(Qt.CursorShape.WaitCursor)
        projectFile = project.fileName()
        (projectPath, projectFilename) = os.path.split(projectFile)
        imageFolder = os.path.join(projectPath, 'nz-topo-images')
        try:
            parent.appendLog(f"Create style images folder {imageFolder}")
            os.makedirs(imageFolder, exist_ok=True)
        except (OSError, IOError) as err:
            msg = f"Failed to create style images folder {imageFolder}\n{err}"
            parent.appendLog(f'{msg}')
            parent.unsetCursor()
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                msg)
            return
        self.extractTopoImageFiles(parent, imageFolder)
        self.updateTopoStylesdb(parent, imageFolder, projectFile)
        parent.unsetCursor()
    # /processTopoStyles

    def extractTopoImageFiles(self, parent, imageFolder):
        sourceFolder = 'styles'
        (root, ext) = os.path.split(__file__)
        (file, ext) = os.path.splitext(root)
        try:
            if ext == '.zip' or ext == '.pyz':
                src = os.path.join(root, sourceFolder, 'images')
                parent.appendLog(f"Copy images from {src}")
                zip = zipfile.ZipFile(root, 'r')
                iconfiles = []
                for zipFile in zip.namelist():
                    if zipFile.startswith(sourceFolder + "/") and \
                       zipFile.endswith(".png"):
                        iconfiles.append(zipFile)
                zip.extractall(imageFolder, iconfiles)
                zip.close()
                srcImages = os.path.join(imageFolder, 'styles', 'images')
                Utilities.copyFolder(parent, srcImages, imageFolder)
                srcImages = os.path.join(imageFolder, 'styles')
                Utilities.removeFolder(parent, srcImages)
                parent.appendLog(f"Images copied to {imageFolder}")
            else:
                src = os.path.join(root, sourceFolder, 'images')
                parent.appendLog(f"Copy images from {src}")
                Utilities.copyFolder(parent, src, imageFolder)
                parent.appendLog(f"Images copied to {imageFolder}")
        except IOError as err:
            parent.appendLog(f'Failed to copy images from {src}\n{err}')
    # /extractTopoImageFiles

    def updateTopoProjectStyles(self, parent, imageFolder, projectFile):
        parent.appendLog(f"Opening project '{projectFile}'...")
        project = QgsProject.instance()
        try:
            if project.read(projectFile):
                title = project.title()
                parent.appendLog(f'Opened project {title}')
                parent.appendLog('Updating map styles...')
                parent.ui.progressBar.setMinimum(0)
                parent.ui.progressBar.setMaximum(len(project.mapLayers()))
                parent.ui.progressBar.setVisible(True)
                i = 0
                for (layer_name, layer) in project.mapLayers().items():
                    if layer.type() == QgsMapLayer.LayerType.VectorLayer and \
                       layer.isSpatial():
                        if layer.wkbType() != Qgis.WkbType.Unknown and \
                           layer.wkbType() != Qgis.WkbType.NoGeometry:
                            styleFileName = FeaturesActions.getStyleFileName(
                                layer)
                            xml = None
                            if styleFileName is not None:
                                try:
                                    (root, ext) = os.path.split(__file__)
                                    (file, ext) = os.path.splitext(root)
                                    if ext == '.zip' or ext == '.pyz':
                                        zip = zipfile.ZipFile(root, 'r')
                                        zipStyleFileName = \
                                            f"styles/{styleFileName}"
                                        for item in zip.namelist():
                                            if item == zipStyleFileName:
                                                styleFile = zip.open(item, 'r')
                                                xmlText = styleFile.read()
                                                styleFile.close()
                                                xml = QDomDocument(
                                                    styleFileName)
                                                xml.setContent(xmlText)
                                                parent.appendLog(
                                                    '    style read from '
                                                    f'{root}//'
                                                    f'{zipStyleFileName}')
                                        zip.close()
                                    else:
                                        (root, file) = os.path.split(__file__)
                                        stylePath = os.path.join(
                                            root, 'styles', styleFileName)
                                        if os.path.isfile(stylePath):
                                            styleFile = open(stylePath, 'r')
                                            xmlText = styleFile.read()
                                            styleFile.close()
                                            xml = QDomDocument(styleFileName)
                                            xml.setContent(xmlText)
                                            parent.appendLog(
                                                '    style read from '
                                                f'{stylePath}')
                                except IOError as err:
                                    parent.appendLog(
                                        'Failed to read style file '
                                        f'{styleFileName}\n{err}')

                            if xml is not None:
                                docElement = xml.documentElement()
                                FeaturesActions.updateImportTagImage(
                                    imageFolder, docElement)
                                layer.importNamedStyle(xml)
                                parent.appendLog(
                                    '    updated style for '
                                    f'layer {layer.name()}')
                            else:
                                parent.appendLog(
                                    '    style not found for '
                                    f'layer {layer.name()}')
                        else:
                            parent.appendLog(
                                f"    layer {layer.name()} "
                                "has unknown geometry")
                    i += 1
                    parent.ui.progressBar.setValue(i)
                    parent.refresh(parent)
                parent.ui.progressBar.reset()
                parent.ui.progressBar.setVisible(False)
                parent.appendLog('Map layer styles updated')
            else:
                parent.appendLog(f"Failed to load project from '{projectFile}'")
                parent.appendLog(f"Loading errors: {project.error()}")
        except IOError as err:
            parent.appendLog(f'Failed to open project {projectFile}\n{err}')
    # /updateTopoProjectStyles

    ########################################################

    def updateTopoStylesdb(self, parent, imageFolder, projectFile):
        (projectPath, projectFilename) = os.path.split(projectFile)
        styledbName = projectPath + os.sep + 'NZ Topo Styles.db'
        stylesdb = FeaturesActions.getStylesdb(parent, styledbName)
        if stylesdb is None:
            return
        fail = self.addProjectTopoStylesdb(parent, stylesdb, projectFile)
        if fail:
            return

        parent.appendLog('Load map styles database...')
        try:
            (root, ext) = os.path.split(__file__)
            (file, ext) = os.path.splitext(root)
            if ext == '.zip' or ext == '.pyz':
                zip = zipfile.ZipFile(root, 'r')
                nameList = zip.namelist()
                parent.ui.progressBar.setMinimum(0)
                parent.ui.progressBar.setMaximum(len(nameList))
                parent.ui.progressBar.setVisible(True)
                i = 0
                for item in nameList:
                    if item.startswith("styles") \
                       and FeaturesActions.isBestStyleFile(item, nameList):
                        (p, ext) = os.path.splitext(item)
                        if (ext == '.qml' or ext == '.xml') and p.find('.') < 0:
                            styleFile = zip.open(item, 'r')
                            xmlText = styleFile.read()
                            styleFile.close()
                            featureType = self.getXMLStyleFeatureType(
                                parent, xmlText)
                            styleName = FeaturesActions.getStyleName(
                                featureType, nameList, item)
                            if not styleName.endswith(' <IGNORE>'):
                                parent.appendLog(
                                    f'    process style {item}')
                                self.updateXMLStyles(
                                    parent, imageFolder, stylesdb,
                                    styleName, xmlText)
                    i += 1
                    parent.ui.progressBar.setValue(i)
                    parent.refresh(parent)
                zip.close()
            else:
                (root, file) = os.path.split(__file__)
                nameList = os.listdir(os.path.join(root, 'styles'))
                if nameList:
                    parent.ui.progressBar.setMinimum(0)
                    parent.ui.progressBar.setMaximum(len(nameList))
                    parent.ui.progressBar.setVisible(True)
                    i = 0
                    for item in nameList:
                        stylePath = os.path.join(
                            root, 'styles', item)
                        if os.path.isfile(stylePath) \
                           and FeaturesActions.isBestStyleFile(item, nameList):
                            (p, ext) = os.path.splitext(item)
                            if (ext == '.qml' or ext == '.xml') and p.find('.') < 0:
                                styleFile = open(stylePath, 'r')
                                xmlText = styleFile.read()
                                styleFile.close()
                                featureType = self.getXMLStyleFeatureType(
                                    parent, xmlText)
                                styleName = FeaturesActions.getStyleName(
                                    featureType, nameList, item)
                                if not styleName.endswith(' <IGNORE>'):
                                    parent.appendLog(
                                        f'    process style {item}')
                                    self.updateXMLStyles(
                                        parent, imageFolder, stylesdb,
                                        styleName, xmlText)
                        i += 1
                        parent.ui.progressBar.setValue(i)
                        parent.refresh(parent)
            parent.ui.progressBar.reset()
            parent.ui.progressBar.setVisible(False)
            parent.appendLog('Map styles loaded')
        except IOError as err:
            parent.appendLog(f'Failed to read style file\n{err}')
        parent.appendLog('Finished loading map style database')
    # /updateTopoStylesdb

    def getStylesdb(parent, styledbName):
        parent.appendLog('Initialize map styles database...')
        stylesdb = None
        if os.path.isfile(styledbName):
            try:
                parent.appendLog(f'  Delete style database from {styledbName}')
                os.unlink(styledbName)
            except (OSError, IOError) as err:
                parent.appendLog(f'  Failed to delete {styledbName}\n{err}')
        if os.path.isfile(styledbName):
            stylesdb = QgsStyle()
            if stylesdb.load(styledbName):
                if stylesdb.name() is None or stylesdb.name().strip() == '':
                    stylesdb.setName('NZ Topo Styles')
                parent.appendLog(f'  Opened style database "{stylesdb.name()}" '
                                 f'from {stylesdb.fileName()}')
            else:
                error = stylesdb.errorString()
                parent.appendLog('  Error loading style database "'
                                 f'{stylesdb.name()}" '
                                 f'from {stylesdb.fileName()}')
                if error:
                    parent.appendLog(f'  {error}')
                return None
        else:
            parent.appendLog('  Create style database')
            stylesdb = QgsStyle()
            stylesdb.setFileName(styledbName)
            stylesdb.setName('NZ Topo Styles')
            if stylesdb.createDatabase(styledbName):
                stylesdb.createTables()
                parent.appendLog(f'  Created style database "{stylesdb.name()}"'
                                 f' at {stylesdb.fileName()}')
            else:
                error = stylesdb.errorString()
                parent.appendLog('  Error creating style database "'
                                 f'{stylesdb.name()}"'
                                 f' at {stylesdb.fileName()}')
                if error:
                    parent.appendLog(f'  {error}')
                    return None
        return stylesdb
    # /getStylesdb

    def addProjectTopoStylesdb(self, parent, stylesdb, projectFile):
        parent.appendLog(f"Opening project '{projectFile}'...")
        styledbName = stylesdb.fileName()
        project = QgsProject.instance()
        try:
            if project.read(projectFile):
                title = project.title()
                parent.appendLog(f'Opened project {title}')
                projectStyledb = project.styleSettings()
                paths = projectStyledb.styleDatabasePaths()
                exist = False
                for path in paths:
                    if path == styledbName:
                        exist = True
                if exist:
                    parent.appendLog(f'Style database "{stylesdb.name()}" '
                                     'already exists in project')
                else:
                    parent.appendLog(f'Add style database "{stylesdb.name()}" '
                                     'to project')
                    projectStyledb.addStyleDatabasePath(styledbName)
                    parent.appendLog('Project updated')
                    self.saveProject(parent, project, title)
            else:
                parent.appendLog(f"Failed to load project from '{projectFile}'")
                parent.appendLog(f"Loading errors: {project.error()}")
                return True
        except IOError as err:
            parent.appendLog(f'Failed to open project {projectFile}\n{err}')
            return True
        return False
    # /addProjectTopoStylesdb

    def updateXMLStyles(self, parent, imageFolder, stylesdb,
                        styleName, xmlText):
        xml = QDomDocument(styleName)
        xml.setContent(xmlText)
        if xml is not None:
            docElement = xml.documentElement()
            FeaturesActions.updateImportTagImage(
                imageFolder, docElement)
            tags = FeaturesActions.getStyleTags(stylesdb, styleName)
            parent.appendLog(f'        style: {styleName}')
            (labelType, labelElement) = FeaturesActions.getStyleLabel(xml)
            if labelElement:
                FeaturesActions.saveStyleLabels(
                    parent, stylesdb, styleName,
                    tags, labelType, labelElement)
            (symbolType, symbolElement) = FeaturesActions.getStyleSymbol(xml)
            if symbolElement:
                FeaturesActions.saveStyleSymbols(
                    parent, stylesdb, styleName,
                    tags, symbolType, symbolElement)
    # /updateXMLStyles

    def getXMLStyleFeatureType(self, parent, xmlText):
        xml = QDomDocument("feature")
        xml.setContent(xmlText)
        if xml is not None:
            (symbolType, symbolElement) = FeaturesActions.getStyleSymbol(xml)
            if symbolElement:
                context = QgsReadWriteContext()
                featureRenderer = QgsFeatureRenderer.load(
                    symbolElement, context)
                FeaturesActions.logStyleMessages(parent, context)
                context = QgsRenderContext()
                symbols = featureRenderer.symbols(context)
                if len(symbols) > 0:
                    return symbols[0].type()
        return None
    # /getXMLStyleFeatureType

    def getStyleLabel(xml):
        root = xml.documentElement()
        child = root.firstChildElement()
        while not child.isNull():
            if child.tagName() == "labeling":
                return (child.attribute("type"), child)
            child = child.nextSiblingElement()
        return (None, None)
    # /getStyleLabel

    def saveStyleLabels(parent, stylesdb, styleName, tags,
                        labelType, labelElement):
        parent.appendLog('        load label style')
        context = QgsReadWriteContext()
        layerSettings = QgsAbstractVectorLayerLabeling.create(
            labelElement, context)
        FeaturesActions.logStyleMessages(parent, context)
        if labelType == "simple" or labelType == "rule-based":
            subKeys = layerSettings.subProviders()
            for subKey in subKeys:
                ruleName = FeaturesActions.getStyleRuleName(
                    labelElement, subKey)
                if ruleName:
                    name = f'{styleName} ({ruleName})'
                else:
                    name = styleName
                FeaturesActions.saveStyleLabel(
                    parent, stylesdb, name, tags,
                    labelType, layerSettings.settings(subKey))
        else:
            parent.appendLog(f'        {labelType} label style not handled')
    # /saveStyleLabels

    def saveStyleLabel(parent, stylesdb, styleName, tags, labelType, label):
        if stylesdb.saveLabelSettings(styleName, label, False, tags):
            parent.appendLog(
                f'        {labelType} label style "{styleName}" saved')
        else:
            parent.appendLog(
                f'        {labelType} label style "{styleName}" NOT saved')
    # /saveStyleLabel

    def getStyleSymbol(xml):
        root = xml.documentElement()
        child = root.firstChildElement()
        while not child.isNull():
            if child.tagName() == "renderer-v2":
                return (child.attribute("type"), child)
            child = child.nextSiblingElement()
        return (None, None)
    # /getStyleSymbol

    def saveStyleSymbols(parent, stylesdb, styleName, tags,
                         symbolType, symbolElement):
        parent.appendLog('        load symbol style')
        context = QgsReadWriteContext()
        featureRenderer = QgsFeatureRenderer.load(symbolElement, context)
        FeaturesActions.logStyleMessages(parent, context)

        if symbolType == 'singleSymbol':
            renderer = QgsSingleSymbolRenderer.convertFromRenderer(
                featureRenderer)
            ruleSymbol = renderer.symbol()
            name = styleName
            FeaturesActions.saveStyleSymbol(
                parent, stylesdb, name, tags, symbolType, ruleSymbol)
        elif symbolType == 'RuleRenderer':
            renderer = QgsRuleBasedRenderer.convertFromRenderer(
                featureRenderer)

            ruleName = renderer.rootRule().label()
            ruleSymbol = renderer.rootRule().symbol()
            if ruleName:
                name = f'{styleName} ({ruleName})'
            else:
                name = styleName
            FeaturesActions.saveStyleSymbol(
                parent, stylesdb, name, tags, symbolType, ruleSymbol)

            rules = renderer.rootRule().descendants()
            for rule in rules:
                ruleName = rule.label()
                ruleSymbol = rule.symbol()
                if ruleName:
                    name = f'{styleName} ({ruleName})'
                else:
                    name = styleName
                FeaturesActions.saveStyleSymbol(
                    parent, stylesdb, name, tags, symbolType, ruleSymbol)
        elif symbolType == 'categorizedSymbol':
            renderer = QgsCategorizedSymbolRenderer.convertFromRenderer(
                featureRenderer)
            categories = renderer.categories()
            for category in categories:
                ruleName = category.label()
                ruleSymbol = category.symbol()
                if ruleName:
                    name = f'{styleName} ({ruleName})'
                else:
                    name = styleName
                FeaturesActions.saveStyleSymbol(
                    parent, stylesdb, name, tags, symbolType, ruleSymbol)
        else:
            parent.appendLog(f'        {symbolType} symbol style not handled')
    # /saveStyleSymbols

    def saveStyleSymbol(parent, stylesdb, styleName, tags,
                        symbolType, symbol):
        if symbol:
            if stylesdb.saveSymbol(styleName, symbol, True, tags):
                parent.appendLog(
                    f'        {symbolType} symbol style "{styleName}" '
                    'saved')
            else:
                parent.appendLog(
                    f'        {symbolType} symbol style "{styleName}" '
                    'NOT saved')
    # /saveStyleSymbol

    def getStyleRuleName(element, subKey):
        child = element.firstChildElement()
        rules = None
        while not child.isNull() and not rules:
            if child.tagName() == "rules":
                rules = child
            child = child.nextSiblingElement()
        if rules:
            child = rules.firstChildElement()
            while not child.isNull():
                if child.tagName() == "rule":
                    if child.attribute("key") == subKey:
                        if child.attribute("description") == '':
                            return None
                        return child.attribute("description")
                child = child.nextSiblingElement()
        return None
    # /getStyleRuleName

    def logStyleMessages(parent, context):
        if context:
            messages = context.takeMessages()
            for message in messages:
                parent.appendLog(f'\t\t{message.message()}')
    # /logStyleMessages

    def getStyleTags(stylesdb, styleName):
        tagRemoveList = [
            "All",
            "And",
            "Of",
            "Sources",
            "Source"
        ]
        tagCompressList = [
            ["North", "Island", "North Island"],
            ["South", "Island", "South Island"],
            ["New", "Zealand", "New Zealand"],
            ["Non", "Primary", "Non Primary"]
        ]
        tags = styleName.split()
        for tag in tagRemoveList:
            if tag in tags:
                tags.remove(tag)
        tags = FeaturesActions.getTagTranslate(tags)
        for compress in tagCompressList:
            if compress[0] in tags and compress[1] in tags:
                if tags.index(compress[1]) - tags.index(compress[0]) == 1:
                    tags.remove(compress[0])
                    tags.remove(compress[1])
                    tags.append(compress[2])
        if 'NZ' in tags and 'Topo' in tags:
            if tags.index('Topo') - tags.index('NZ') == 1:
                tags.remove('NZ')
                tags.remove('Topo')
        for tag in tags:
            if tag[0].isdigit():
                tags.remove(tag)
        tags = list(dict.fromkeys(tags))
        for tag in tags:
            if stylesdb.tagId(tag) < 1:
                stylesdb.addTag(tag)
        return tags
    # /getStyleTags

    def getTagTranslate(tags):
        translateList = {
            "Nz": "NZ",
            "Linz": "LINZ",
            "Nzgb": "NZGB",
            "Ni": "North Island",
            "NI": "North Island",
            "Si": "South Island",
            "SI": "South Island",
            "Addresses": "Address",
            "Addressing": "Address",
            "Areas": "Area",
            "Boundaries": "Boundary",
            "Coastlines": "Coastline",
            "Contours": "Contour",
            "Districts": "District",
            "Edges": "Edge",
            "Highways": "Highway",
            "Huts": "Hut",
            "Islands": "Island",
            "Leases": "Lease",
            "Limits": "Limit",
            "Lines": "Line",
            "Localities": "Locality",
            "Marks": "Mark",
            "Names": "Name",
            "Outlines": "Outline",
            "Parcels": "Parcel",
            "Passes": "Pass",
            "Peaks": "Peak",
            "Properties": "Property",
            "Roads": "Road",
            "Rr": "Railway",
            "Sheets": "Sheet",
            "Skifields": "Skifield",
            "Suburbs": "Suburb",
            "Texts": "Text",
            "Titles": "Title",
            "Tracks": "Track",
            "Waterways": "Waterway"
        }
        newTags = []
        for tag in tags:
            if tag in translateList:
                t = translateList.get(tag)
                newTags.append(t)
            else:
                newTags.append(tag)
        return newTags
    # /getTagTranslateList

    def updateImportTagImage(imageFolder, root):
        child = root.firstChildElement()
        while not child.isNull():
            if child.hasAttribute("name") and child.hasAttribute("value"):
                name = child.attribute("name")
                imageFile = child.attribute("value")
                if name == "imageFile":
                    (imagePath, imageFilename) = os.path.split(imageFile)
                    tagImageFile = imageFilename.replace(
                        "{STYLE_IMAGES}", imageFolder + os.sep)
                    child.setAttribute("value", tagImageFile)
            FeaturesActions.updateImportTagImage(imageFolder, child)
            child = child.nextSiblingElement()
    # /updateImportTagImage

    ########################################################

    def exportTopoStyles():
        (root, file) = os.path.split(__file__)
        if not HAS_QGIS:
            print('No QGIS module')
            return
        (f, ext) = os.path.splitext(root)
        if ext == '.zip' or ext == '.pyz':
            print('Can only be run for development')
            return
        if platform.system() != 'Linux':
            print('Can only be run for development')
            return
        app = None
        try:
            exe = shutil.which("qgis")
            (qgsRoot, ext) = os.path.split(exe)
            QgsApplication.setPrefixPath(qgsRoot, True)
            app = QgsApplication([], False)
            app.initQgis()
            print('QGIS initialized')
        except Exception as err:
            print(f"Error initializing QGIS:\n{err}")
            return
        styleFolder = os.path.join(root, 'styles')
        try:
            print(f"Create empty style folder: {styleFolder}")
            imagesFolder = os.path.join(styleFolder, 'images')
            os.makedirs(imagesFolder, exist_ok=True)
            for filename in os.listdir(styleFolder):
                file_path = os.path.join(styleFolder, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except (OSError, IOError) as err:
            print(f'Failed to create empty style folder: {styleFolder}\n{err}')
            return

        # ++++++ update project list
        projectFile = r"/gis/qgis/Grant/GIS/NZ Topo Layers.qgs"
        FeaturesActions.exportTopoProject(styleFolder, projectFile)
        projectFile = r"/gis/qgis/Grant/GIS/NZ Properties.qgs"
        FeaturesActions.exportTopoProject(styleFolder, projectFile)
        #
        print(f'Exit {file}')
        app.exitQgis()
    # /exportTopoStyles

    def exportTopoProject(styleFolder, projectFile):
        print(f"Opening '{projectFile}'...")
        project = QgsProject.instance()
        try:
            if project.read(projectFile):
                title = project.title()
                print(f'Opened project {title}')
                print('Exporting map styles...')
                cnt = 0
                for (layer_name, layer) in project.mapLayers().items():
                    if layer.type() == QgsMapLayer.LayerType.VectorLayer and \
                       layer.isSpatial():
                        if layer.wkbType() != Qgis.WkbType.Unknown and \
                           layer.wkbType() != Qgis.WkbType.NoGeometry:
                            styleFile = os.path.join(
                                styleFolder,
                                FeaturesActions.getStyleFileName(layer))
                            if os.path.isfile(styleFile):
                                print('    saved style already exists for '
                                      f'layer {layer.name()}')
                            else:
                                print('    save style for '
                                      f'layer {layer.name()}')
                                xml = QDomDocument()
                                layer.exportNamedStyle(xml)
                                root = xml.documentElement()
                                child = root.firstChildElement()
                                orphans = []
                                while not child.isNull():
                                    if FeaturesActions.isExportTagKeep(
                                       child.tagName()):
                                        # print(f'\t\tKeep {child.tagName()}')
                                        FeaturesActions.updateExportTagImage(
                                            styleFolder, child)
                                    else:
                                        # print(f'\t\tRemove {child.tagName()}')
                                        orphans.append(child)
                                    child = child.nextSiblingElement()
                                for child in orphans:
                                    root.removeChild(child)
                                with open(styleFile, "w") as file:
                                    file.write("%s" % xml.toString())
                            cnt += 1
                        else:
                            print(f"    layer {layer.name()} "
                                  "has unknown geometry")
                print(f'Exported {cnt} layer styles')
            else:
                print(f"Failed to load project from '{projectFile}'")
                print(f"Loading errors: {project.error()}")
        except IOError as err:
            print(f'Failed to open project {projectFile}\n{err}')
    # /exportTopoProject

    def isExportTagKeep(name):
        tags = ["flags", "elevation", "renderer-v2", "selection", "labeling",
                "blendMode", "featureBlendMode", "layerOpacity",
                "SingleCategoryDiagramRenderer", "DiagramLayerSettings",
                "geometryOptions", "legend", "conditionalstyles", "labelOnTop",
                "previewExpression", "mapTip"]
        return name in tags
    # /isExportTagKeep

    def updateExportTagImage(styleFolder, root):
        child = root.firstChildElement()
        while not child.isNull():
            if child.hasAttribute("name") and child.hasAttribute("value"):
                name = child.attribute("name")
                imageFile = child.attribute("value")
                if name == "imageFile":
                    (imagePath, imageFilename) = os.path.split(imageFile)
                    newImageFile = os.path.join(
                        styleFolder, 'images', imageFilename)
                    tagImageFile = "{STYLE_IMAGES}" + imageFilename
                    child.setAttribute("value", tagImageFile)
                    try:
                        if not os.path.isfile(newImageFile):
                            print(f'\tcopy image {imageFile} to '
                                  f'{newImageFile}')
                            shutil.copyfile(imageFile, newImageFile)
                    except Exception as err:
                        print(f'{err}')
            FeaturesActions.updateExportTagImage(styleFolder, child)
            child = child.nextSiblingElement()
    # /updateExportTagImage

    ########################################################

    def getStyleFileName(layer):
        styleFile = None
        if layer.dataProvider():
            dpName = layer.dataProvider().name()
        else:
            dpName = None
        uriComponents = QgsProviderRegistry.instance().decodeUri(
            dpName, layer.source())
        sourceConfig = Database.extractSourceURI(
            layer.storageType(), uriComponents)
        table = sourceConfig.get("tablename")
        path = sourceConfig.get("path")
        if table:
            styleFile = table.lower().replace('_', '-') + '.qml'
        elif path:
            styleFile = path + '.qml'
        return styleFile
    # /getStyleFileName

    def getStyleName(featureType, nameList, file):
        (root, f) = os.path.split(file)
        (filename, ext) = os.path.splitext(f)
        styleName = filename.lower()
        filenameType = ''
        if styleName.startswith('nz-'):
            styleName = styleName[3:]
        i = styleName.find('-points-')
        if i > 0:
            styleName = styleName[0:i]
            filenameType = Qgis.SymbolType.Marker
        i = styleName.find('-centrelines-')
        if i > 0:
            styleName = styleName[0:i]
            filenameType = Qgis.SymbolType.Line
        i = styleName.find('-polygons-')
        if i > 0:
            styleName = styleName[0:i]
            filenameType = Qgis.SymbolType.Fill
        i = styleName.find('-topo-')
        if i > 0:
            styleName = styleName[0:i]
        # styleCount = 0
        # for name in nameList:
        #     if name.lower().find(styleName) >= 0 \
        #        and name.lower().find(filenameType) < 0:
        #         styleCount += 1
        styleName = styleName.replace('-', ' ').replace('_', ' ').title()
        if styleName.endswith(' Ni'):
            styleName = styleName.replace(' Ni', ' NI')
        if styleName.endswith(' Si'):
            styleName = styleName.replace(' Si', ' SI')
        if styleName.endswith(' NI'):
            styleName += ' <IGNORE>'
        elif styleName.endswith(' SI'):
            names = styleName.split()
            if styleName.startswith('Highway') \
               or styleName.startswith('Road') \
               or styleName.startswith('Track') \
               or styleName.startswith('Train') \
               or styleName.startswith('Highway') \
               or styleName.startswith('Waterway') \
               or styleName.startswith('Hut') \
               or styleName.startswith('Peak') \
               or styleName.startswith('Pass'):
                styleName = 'My ' + names[0]
        elif styleName == 'Skifields':
            styleName = 'My Skifields'
        else:
            if styleName.find('Point') < 0 and \
               styleName.find('Line') < 0 and \
               styleName.find('Polygon') < 0:
                styleName += FeaturesActions.getStyleNameTypeSufix(
                    filenameType, featureType)
        tags = styleName.split()
        tags = FeaturesActions.getTagTranslate(tags)
        return ' '.join(tags)
    # /getStyleName

    def getStyleNameTypeSufix(filenameType, featureType):
        match filenameType:
            case Qgis.SymbolType.Marker:
                sufix = ' Point'
            case Qgis.SymbolType.Line:
                sufix = ' Line'
            case Qgis.SymbolType.Fill:
                sufix = ' Polygon'
            case _:
                match featureType:
                    case Qgis.SymbolType.Marker:
                        sufix = ' Point'
                    case Qgis.SymbolType.Line:
                        sufix = ' Line'
                    case Qgis.SymbolType.Fill:
                        sufix = ' Polygon'
                    case _:
                        sufix = ''
        return sufix
    # /getStyleNameTypeSufix

    def isBestStyleFile(file, fileList):
        if file is None:
            return False
        if file.find('-125k.') >= 0:
            return True
        elif file.find('-150k.') >= 0:
            name25 = file.replace('-150k.', '-125k.')
            if name25 in fileList:
                return False
            return True
        elif file.find('-1250k.') >= 0:
            name25 = file.replace('-1250k.', '-125k.')
            name50 = file.replace('-1250k.', '-150k.')
            for name in fileList:
                if name == name25 or name == name50:
                    return False
            return True
        elif file.find('-1500k.') >= 0:
            name25 = file.replace('-1500k.', '-125k.')
            name50 = file.replace('-1500k.', '-150k.')
            name250 = file.replace('-1500k.', '-1250k.')
            for name in fileList:
                if name == name25 or name == name50 or name == name250:
                    return False
            return True
        return True
    # /isBestStyleFile
# /FeaturesActions


if __name__ == '__main__':
    FeaturesActions.exportTopoStyles()
