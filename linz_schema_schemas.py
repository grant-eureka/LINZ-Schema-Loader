# Created on : Dec 26, 2025, 3:07:23 PM
# Author     : Grant

import os
import sys
import tempfile
import zipfile
import io
import csv
import glob
from xml.etree import ElementTree
import datetime
from osgeo import osr
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
    from linz_schema_database import Database, SQLError
else:
    from .linz_schema_utilities import MessageBoxes, Utilities
    from .linz_schema_database import Database, SQLError


class Counters():
    """'Type' definition for database field.
    """
    READ = 0
    WRITE = 1
    FAIL = 2
    DUPLICATE = 4

    readCnt = 0
    writeCnt = 0
    failCnt = 0
    duplicateCnt = 0

    def __init__(self):
        self.readCnt = 0
        self.writeCnt = 0
        self.failCnt = 0
        self.duplicateCnt = 0

    def __str__(self):
        return f'Total read : {self.readCnt} ' \
               f'Total write : {self.writeCnt} ' \
               f'Total fail : {self.failCnt} ' \
               f'Total duplicate : {self.duplicateCnt}'

    def increment(self, field):
        match field:
            case self.READ:
                self.readCnt += 1
            case self.WRITE:
                self.writeCnt += 1
            case self.FAIL:
                self.failCnt += 1
            case self.DUPLICATE:
                self.duplicateCnt += 1
# /Counters


class SchemasActions():
    def __init__(self):
        super().__init__()
    # /__init__

    def init(self):
        pass
    # /init

    def requestSchemaCreate(self, parent, cnx, schemaname, description):
        if MessageBoxes.messageBox(
           parent,
           MessageBoxes.QUESTION,
           Utilities.getApptitle(parent),
           f'Create new schema "{schemaname}"?',
           MessageBoxes.YES_NO) == MessageBoxes.YES.value:
            self.createSchema(parent, cnx, schemaname, description)
        else:
            parent.appendLog('Create schema cancelled')
            return False
        return True
    # /requestSchemaCreate

    def createSchema(self, parent, cnx, schemaname, description):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'\nCreating schema {schemaname}...')
        sql = f"CREATE SCHEMA {schemaname};"
        Database.executeSQL(parent, cnx, sql)
        parent.appendLog(f'Created schema {schemaname}')
        parent.appendLog('Define GIS schema...')
        if description:
            comment = description
        else:
            comment = schemaname + " schema"
        sql = f"ALTER SCHEMA {schemaname} " \
              "DEFAULT CHARACTER SET='utf8' " \
              "DEFAULT COLLATE='utf8_general_ci'" \
              f"COMMENT='{comment}';"
        Database.executeSQL(parent, cnx, sql, True)
        sql = "GRANT select, insert, update, delete, execute " \
              f"ON {schemaname}.*" \
              "TO root@localhost WITH GRANT OPTION;"
        Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog('Create geometry tables')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.geometry_columns (" \
              "f_table_catalog    VARCHAR(256), " \
              "f_table_schema     VARCHAR(256), " \
              "f_table_name       VARCHAR(256) NOT NULL, " \
              "f_geometry_column  VARCHAR(256) NOT NULL, " \
              "coord_dimension    INTEGER(11), " \
              "srid               INTEGER(11), " \
              "type               VARCHAR(256) NOT NULL, " \
              "geometry_type      VARCHAR(256) NOT NULL, " \
              "qgis_xmin          FLOAT, " \
              "qgis_ymin          FLOAT, " \
              "qgis_xmax          FLOAT, " \
              "qgis_ymax          FLOAT, " \
              "qgis_pkey          VARCHAR(256), " \
              "INDEX (f_table_name) );"
        Database.executeSQL(parent, cnx, sql, True)
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.spatial_ref_sys (" \
              "srid       INTEGER(11) NOT NULL PRIMARY KEY, " \
              "auth_name  VARCHAR(256), " \
              "auth_srid  INTEGER(11), " \
              "srtext     VARCHAR(2048), " \
              "proj4text  VARCHAR(2048) );"
        Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog('Create dataset table')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.table_datasets (" \
              " schemaname VARCHAR(64) NOT NULL, " \
              " tablename VARCHAR(64) NOT NULL, " \
              " dataset_file VARCHAR(256), " \
              " dataset_date DATE, " \
              " dataset_cnt INTEGER, " \
              " dataset_load_seconds INTEGER, " \
              "PRIMARY KEY (schemaname, tablename));"
        Database.executeSQL(parent, cnx, sql, True)
        parent.loadDatasetTable(schemaname)
        parent.appendLog('Defined GIS schema')
        parent.appendLog(f'Created schema {schemaname}')
        parent.unsetCursor()
    # /createSchema

    def updateSchema(self, parent, cnx, schemaname, description):
        update = MessageBoxes.messageBox(
            parent,
            MessageBoxes.QUESTION,
            Utilities.getApptitle(parent),
            f'Update definitions of schema "{schemaname}"?',
            MessageBoxes.YES_NO)
        purge = MessageBoxes.messageBox(
            parent,
            MessageBoxes.QUESTION,
            Utilities.getApptitle(parent),
            f'Drop depricated tables from schema "{schemaname}"?',
            MessageBoxes.YES_NO)
        parent.appendLog(f'\nUpdating schema {schemaname}...')
        if update == MessageBoxes.YES.value:
            self.updateSchemaDefinition(parent, cnx, schemaname, description)
        if purge == MessageBoxes.YES.value:
            self.updateSchemaPurge(parent, cnx, schemaname)
        parent.appendLog(f'Updated schema {schemaname}')
    # /updateSchema

    def updateSchemaDefinition(self, parent, cnx, schemaname, description):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog('  update schema description...')
        if description:
            comment = description
        else:
            comment = schemaname + " schema"
        sql = f"ALTER SCHEMA {schemaname} " \
              "DEFAULT CHARACTER SET='utf8' " \
              "DEFAULT COLLATE='utf8_general_ci'" \
              f"COMMENT='{comment}';"
        Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog('  update schema privilges...')
        sql = "GRANT select, insert, update, delete, execute " \
              f"ON {schemaname}.*" \
              "TO root@localhost WITH GRANT OPTION;"
        Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog('  update geometry tables...')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.geometry_columns (" \
              "f_table_catalog    VARCHAR(256), " \
              "f_table_schema     VARCHAR(256), " \
              "f_table_name       VARCHAR(256) NOT NULL, " \
              "f_geometry_column  VARCHAR(256) NOT NULL, " \
              "coord_dimension    INTEGER(11), " \
              "srid               INTEGER(11), " \
              "type               VARCHAR(256) NOT NULL, " \
              "geometry_type      VARCHAR(256) NOT NULL, " \
              "qgis_xmin          FLOAT, " \
              "qgis_ymin          FLOAT, " \
              "qgis_xmax          FLOAT, " \
              "qgis_ymax          FLOAT, " \
              "qgis_pkey          VARCHAR(256), " \
              "INDEX (f_table_name) );"
        Database.executeSQL(parent, cnx, sql, True)
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.spatial_ref_sys (" \
              "srid       INTEGER(11) NOT NULL PRIMARY KEY, " \
              "auth_name  VARCHAR(256), " \
              "auth_srid  INTEGER(11), " \
              "srtext     VARCHAR(2048), " \
              "proj4text  VARCHAR(2048) );"
        Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog('  create/update dataset table...')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.table_datasets (" \
              " schemaname VARCHAR(64) NOT NULL, " \
              " tablename VARCHAR(64) NOT NULL, " \
              " dataset_file VARCHAR(256), " \
              " dataset_date DATE, " \
              " dataset_cnt INTEGER, " \
              " dataset_load_seconds INTEGER, " \
              "PRIMARY KEY (schemaname, tablename));"
        Database.executeSQL(parent, cnx, sql, True)
        sql = "ALTER TABLE " \
              f"{schemaname}.table_datasets ADD COLUMN IF NOT EXISTS (" \
              " dataset_load_seconds INTEGER );"
        Database.executeSQL(parent, cnx, sql, True)
        parent.loadDatasetTable(schemaname)
        parent.unsetCursor()
    # /updateSchemaDefinition

    def updateSchemaPurge(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog('  purge depricated tables...')
        tables = Database.getTables(parent, cnx, schemaname)
        drop = False
        if tables:
            for table in tables:
                if self.isPurgeTable(table[0]):
                    parent.appendLog(f'    drop table {table[0]}')
                    sql = f"DROP TABLE {schemaname}.{table[0]};"
                    Database.executeSQL(parent, cnx, sql)
                    drop = True
        else:
            parent.appendLog(f'    NO tables found in {schemaname}')
        parent.unsetCursor()
        if drop:
            msg = 'Database tables have been dropped from schema ' + \
                f'"{schemaname}".\n' + \
                'Database views may have been invalidated and need ' + \
                're-creating.\n' + \
                'Your QGIS projects may now have invalid data sources for ' + \
                'layers connecting to the dropped tables.\n' + \
                'Delete or update any invalid data sources from QGIS.'
            parent.appendLog(msg)
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.INFORMATION,
                Utilities.getApptitle(parent),
                msg)
    # /updateSchemaPurge

    def isPurgeTable(self, tablename):
        purgeTables = [
            'aims_address',
            'aims_address_class',
            'aims_address_component',
            'aims_address_component_type',
            'aims_address_lifecycle_stage',
            'aims_address_position',
            'aims_address_position_type',
            'aims_address_reference',
            'aims_address_reference_object_type',
            'aims_addressable_object',
            'aims_addressable_object_lifecycle_stage',
            'aims_addressable_object_type',
            'aims_addressable_object_external',
            'aims_alternative_address_type',
            'aims_organisation',
            'nz_addresses_pilot',
            'nz_addresses_roads_pilot',
            'nz_addresses_road_sections_pilot',
            'nz_roads_addressing',
            'nz_roads_addressing_road_name',
            'nz_roads_address_range_road_type',
            'nz_roads_capture_method',
            'nz_roads_geometry_class',
            'nz_roads_road',
            'nz_roads_road_section_geometry',
            'nz_roads_road_name',
            'nz_roads_road_name_association',
            'nz_roads_road_name_class',
            'nz_roads_road_name_prefix',
            'nz_roads_road_name_suffix',
            'nz_roads_road_name_type',
            'nz_roads_road_section',
            'nz_roads_road_section_lifecycle_stage',
            'nz_roads_road_section_type',
            'nz_roads_road_type',
            'nz_roads_route_name',
            'nz_roads_subsections_addressing'
        ]
        # keep as still used:    'nz_roads_organisation'
        if tablename:
            if tablename.endswith('_deprecated'):
                return True
            return tablename in purgeTables
        return False
    # /isPurgeTable

    def requestSchemaDrop(self, parent, cnx, schemaname):
        parent.appendLog(f'\nDrop GIS schema {schemaname}')
        if Database.isSchemaExist(parent, cnx, schemaname):
            option = MessageBoxes.messageBox(
                parent,
                MessageBoxes.QUESTION,
                Utilities.getApptitle(parent),
                f'Schema "{schemaname}" exists.\n\n'
                'Drop existing schema?',
                MessageBoxes.YES_NO)
            if option == MessageBoxes.YES.value:
                if MessageBoxes.messageBox(
                   parent,
                   MessageBoxes.QUESTION,
                   Utilities.getApptitle(parent),
                   f'All contents in schema "{schemaname}" '
                   'will be deleted.\n\n'
                   'Drop schema and all contents?',
                   MessageBoxes.YES_NO) == MessageBoxes.YES.value:
                    self.dropSchema(parent, cnx, schemaname)
                else:
                    parent.appendLog('Drop schema cancelled')
                    return False
            else:
                parent.appendLog('Drop schema cancelled')
                return False
        else:
            parent.appendLog(f'Schema {schemaname} does not exists.\n'
                             'Unable to drop non-existing schema.')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.INFORMATION,
                Utilities.getApptitle(parent),
                f'Schema "{schemaname}" does not exists.\n'
                'Unable to drop non-existing schema.')
        return True
    # /requestSchemaDrop

    def dropSchema(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'Droping schema {schemaname}...')
        sql = f"DROP SCHEMA {schemaname};"
        Database.executeSQL(parent, cnx, sql)
        sql = "REVOKE ALL " \
              f"ON {schemaname}.*" \
              "FROM root@localhost;"
        Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog(f'Dropped schema {schemaname}')
        parent.unsetCursor()
    # /dropSchema

    def requestSchemaLoad(self, parent, cnx, schemaname):
        parent.appendLog(f"\nImport CSV data into schema {schemaname}...")
        if Database.isSchemaExist(parent, cnx, schemaname):
            if MessageBoxes.messageBox(
               parent,
               MessageBoxes.QUESTION,
               Utilities.getApptitle(parent),
               f'Load LINZ dataset files into schema "{schemaname}"?',
               MessageBoxes.YES_NO) == MessageBoxes.YES.value:
                directoryName = self.getLoadDirectory(parent, cnx, schemaname)
                if directoryName:
                    self.processDirectory(parent, cnx,
                                          schemaname, directoryName)
                else:
                    parent.appendLog("\nNo directory selected for loading")
                self.processViews(parent, cnx, schemaname)
            else:
                parent.appendLog('Import CSV data cancelled')
    # /requestSchemaLoad

    def getLoadDirectory(self, parent, cnx, schemaname):
        directoryName = None
        sql = "SELECT dataset_file " \
              f"FROM {schemaname}.table_datasets " \
              f"WHERE schemaname='{schemaname}' "\
              "AND dataset_file IS NOT NULL " \
              "ORDER BY dataset_date DESC " \
              "LIMIT 1;"
        directoryName = Database.readDatabaseResult(parent, cnx, sql)
        directoryName = MessageBoxes.openDirectoryBox(
            parent, "Open LINZ Download ZIP Directory", directoryName)
        return directoryName
    # /getLoadDirectory

    def processDirectory(self, parent, cnx, schemaname, directoryName):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f"\nLoad zip data files from {directoryName} "
                         f"into schema {schemaname}...")
        for zipFileName in sorted(glob.glob(f"{directoryName}/*.zip")):
            if zipfile.is_zipfile(zipFileName):
                parent.appendLog(f'\nProcess {zipFileName}...')
                zip = zipfile.ZipFile(zipFileName, 'r')
                vrtfiles = Utilities.getVrtFiles(zip)
                extents = [None, None, None, None]
                for vrtfile in vrtfiles:
                    parent.appendLog(f'    Analysing\t{vrtfile}...')
                    vrtpath = Utilities.getPathDirectory(vrtfile)
                    if vrtpath:
                        vrtpath += "/"
                    vrtname = Utilities.getPathFile(vrtfile)
                    tree = ElementTree.fromstring(zip.read(vrtfile))
                    csvFileName = Utilities.getTreeText(
                        tree, None, 'SrcDataSource')
                    zipDate = self.getZipDate(zip, csvFileName)
                    parent.appendLog(f'    data file\t{vrtpath}{csvFileName}')
                    parent.appendLog(f'    data timestamp\t{zipDate}')
                    layername = Utilities.getTreeText(
                        tree, 'OGRVRTLayer', 'name')
                    tablename = None
                    if layername:
                        tablename = layername.lower().replace('-', '_')
                    if self.isPurgeTable(tablename):
                        parent.appendLog(
                            f'    \t{tablename} has been depricated '
                            'and will not be loaded')
                    else:
                        key = Utilities.getTreeText(
                            tree, None, 'FID')
                        fcnt = Utilities.getTreeInt(
                            tree, None, 'FeatureCount', 0)
                        geometry = Utilities.getTreeText(
                            tree, None, 'GeometryType')
                        if geometry:
                            geometry = geometry.upper().lstrip("WKB")
                            if geometry == "POLYGON":
                                geometry = "MULTIPOLYGON"
                            geometry = self.getTableGeometry(
                                parent, cnx, schemaname, tablename, geometry)
                            parent.appendLog(
                                f'    geometry\t{geometry}')
                            prjId = self.getPrjId(
                                parent, cnx, schemaname, zip, vrtname)
                        else:
                            parent.appendLog('    geometry\tNone')
                            prjId = None
                        extents[0] = Utilities.getTreeText(
                            tree, None, 'ExtentXMin')
                        extents[1] = Utilities.getTreeText(
                            tree, None, 'ExtentYMin')
                        extents[2] = Utilities.getTreeText(
                            tree, None, 'ExtentXMax')
                        extents[3] = Utilities.getTreeText(
                            tree, None, 'ExtentYMax')
                        geofield = Utilities.getTreeText(
                            tree, 'GeometryField', 'field')
                        fields = Utilities.getFields(
                            tree, geometry, geofield, key)
#                        for field in fields:
#                            print(f"{field.fieldName} {field.fieldType}")

                        parent.appendLog(f'    features\t{fcnt:,}')

                        dataset = self.getDataset(
                            parent, cnx, schemaname, tablename, zipFileName)
                        if Database.isTableExist(
                                parent, cnx, schemaname, tablename):
                            schemaDate = dataset[3]
                            schemaRows = dataset[4]
                            schemaElapsed = dataset[5]
                            self.logSchemaLoad(
                                parent, schemaDate, schemaRows, schemaElapsed)
                            if self.truncateTable(
                               parent, cnx,
                               schemaname, tablename, dataset, zipDate,
                               fields, zipFileName):
                                dataset = self.getDataset(
                                    parent, cnx,
                                    schemaname, tablename, zipFileName)
                                self.setTableGeometry(
                                    parent, cnx,
                                    schemaname, tablename, geometry,
                                    extents, prjId, fields)
                                append = Database.isDataExist(
                                    parent, cnx, schemaname, tablename)
                                self.loadTable(
                                    parent, cnx,
                                    schemaname, tablename, dataset,
                                    fields, geometry, key, append,
                                    directoryName, zipFileName, zip, zipDate,
                                    vrtpath + csvFileName, fcnt)
                        else:
                            ok = True
                            try:
                                self.createTable(
                                    parent, cnx,
                                    schemaname, tablename, fields, zipFileName)
                            except Exception as err:
                                parent.appendLog(
                                    '    Database error creating table '
                                    f'{schemaname}.{tablename}:\n'
                                    f'SQLError: {err}')
                                ok = False
                            if ok:
                                dataset = self.getDataset(
                                    parent, cnx,
                                    schemaname, tablename, zipFileName)
                                self.setTableGeometry(
                                    parent, cnx,
                                    schemaname, tablename, geometry,
                                    extents, prjId, fields)
                                self.loadTable(
                                    parent, cnx,
                                    schemaname, tablename, dataset,
                                    fields, geometry, key, False,
                                    directoryName, zipFileName, zip, zipDate,
                                    vrtpath + csvFileName, fcnt)
                        parent.appendLog(
                            f'    Process {vrtfile} complete')

                if vrtfiles:
                    parent.appendLog(f'Process {zipFileName} complete')
                else:
                    parent.appendLog(
                        f'Error: .vrt file not found in {zipFileName}. - '
                        'not loaded')
                zip.close()
            else:
                parent.appendLog(
                    f'Error: invalid zip file {zipFileName}. - '
                    'not loaded')
        parent.appendLog(f'Loaded data into schema {schemaname}')
        parent.unsetCursor()
    #  \processDirectory

    def logSchemaLoad(self, parent, schemaDate, schemaRows, schemaElapsed):
        if schemaDate:
            parent.appendLog(
                f'    existing date\t{schemaDate}')
        if schemaRows:
            parent.appendLog(
                f'    existing rows\t{schemaRows:,}')
        if schemaElapsed:
            t = datetime.timedelta(seconds=schemaElapsed)
            parent.appendLog(
                f'    previous time\t{t}')
    # /logSchemaLoad

    def loadTable(self, parent, cnx, schemaname, tablename, dataset,
                  fields, geometry, key, append,
                  directoryName, zipFileName, zip, zipDate, csvFileName, fcnt):
        # parent.appendLog(f'\tloadTable {schemaname}.{tablename}')
        if csvFileName:
            if geometry:
                pass
                geometry = self.loadTableFile(
                    parent, cnx,
                    schemaname, tablename, fields, geometry, key, append,
                    directoryName, zipFileName, zip, zipDate, csvFileName, fcnt)
            else:
                parent.appendLog('    load non-geometry file')
                self.loadTableFileDirect(
                    parent, cnx,
                    schemaname, tablename, fields, key, append,
                    directoryName, zipFileName, zip, zipDate, csvFileName, fcnt)
        else:
            parent.appendLog('    no data file to load')
    # /loadTable

    def loadTableFileDirect(self, parent, cnx,
                            schemaname, tablename, fields, key,
                            append, directoryName, zipFileName, zip, zipDate,
                            csvFileName, fcnt):
        # parent.appendLog(f'    loadTableFileDirect {schemaname}.{tablename}')
        startTime = Utilities.getNow()
        self.dropIndexes(parent, cnx, schemaname, tablename)
        parent.appendLog(f'    load table data into {schemaname}.{tablename}')
        parent.appendLog(f'    load data from {csvFileName}')
        csvFilePath = Utilities.getCsvFilepath(zip, csvFileName)
        csv.field_size_limit(sys.maxsize)
        try:
            tempDir = tempfile.TemporaryDirectory()
            parent.appendLog(f'    extract csv file to {tempDir.name}')
            zip.extract(csvFilePath, tempDir.name)
            uzipFileName = f"{tempDir.name}/{csvFilePath}"
            self.loadTableDirect(
                parent, cnx, schemaname, tablename, fields, key,
                zipFileName, zipDate, append, uzipFileName, fcnt)
            tempDir.cleanup()
            parent.appendLog('    count loaded rows')
            loadedCnt = self.featureCount(parent, cnx,
                                          True, schemaname, tablename, key)
            parent.appendLog(f'    {fcnt:,} records processed')
            parent.appendLog(f'    {loadedCnt:,} records loaded')
            elapsed = Utilities.getElapsedTime(startTime)
            self.setDatasetTable(
                parent, cnx,
                schemaname, tablename, zipFileName, zipDate,
                loadedCnt, elapsed)
            self.createIndexes(parent, cnx, schemaname, tablename, fields)
            parent.readStatus(None)
            parent.appendLog(f'    load completed {Utilities.getNowString()}')
            parent.appendLog(f'    elapsed time {elapsed}')
        except OSError as err:
            try:
                parent.appendLog(f'Error extracting {csvFilePath} to '
                                 f'{tempDir}:\n{err}')
                if tempDir:
                    tempDir.cleanup()
                tempDir = os.path.join(
                    os.sep, directoryName, zipFileName.rstrip(".zip"))
                parent.appendLog(f'    extract csv file to {tempDir}')
                os.makedirs(tempDir, exist_ok=True)
                zip.extract(csvFilePath, tempDir)
                uzipFileName = f"{tempDir}/{csvFilePath}"
                self.loadTableDirect(
                    parent, cnx,
                    schemaname, tablename, fields, key,
                    zipFileName, zipDate, append, uzipFileName, fcnt)
                parent.appendLog('    count loaded rows')
                loadedCnt = self.featureCount(parent, cnx,
                                              True, schemaname, tablename, key)
                parent.appendLog(f'    {fcnt:,} records processed')
                parent.appendLog(f'    {loadedCnt:,} records loaded')
                elapsed = Utilities.getElapsedTime(startTime)
                self.setDatasetTable(
                    parent, cnx,
                    schemaname, tablename, zipFileName, zipDate,
                    loadedCnt, elapsed)
                self.createIndexes(parent, cnx, schemaname, tablename, fields)
                parent.readStatus(None)
                parent.appendLog('    load completed '
                                 f'{Utilities.getNowString()}')
                parent.appendLog(f'    elapsed time {elapsed}')
            except OSError as err:
                parent.appendLog(f'Error extracting {csvFilePath} to '
                                 f'{tempDir}:\n{err}')
    # /loadTableFileDirect

    def loadTableDirect(self, parent, cnx,
                        schemaname, tablename, fields, key,
                        zipFileName, zipDate, append, uzipFileName, fcnt):
        parent.appendLog('    count existing rows')
        appendCnt = self.featureCount(parent, cnx,
                                      append, schemaname, tablename, key) + 1
        parent.appendLog(f'    load data from {uzipFileName}')
        if appendCnt > 1:
            parent.appendLog(f'    skip {appendCnt:,} lines')
        sql = "LOAD DATA "
        # local = Database.isLocalDB(parent, cnx)
        # if not local:  # force infile local for file security
        sql += "LOCAL "
        sql += f"INFILE '{uzipFileName}'\n"
        sql += f"IGNORE INTO TABLE {schemaname}.{tablename}\n" + \
            "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY 0x22 " + \
            "ESCAPED BY 0x5c\n" + \
            "LINES TERMINATED BY 0x0d0a\n" \
            f"IGNORE {appendCnt} LINES\n"
        isFirst = True
        hasTmps = False
        for field in fields:
            #  parent.appendLog(
            #     f"{field.fieldName} > {field.fieldType} "
            #     f" isNumberField={Utilities.isNumberField(field.fieldType)}"
            #     f" isKey={field.isKey}")
            isTmp = field.fieldType == 'TEXT' \
                or field.fieldType == 'VARCHAR' \
                or field.fieldType == 'STRING' \
                or field.fieldType == 'TEXT'
            isTmp = (isTmp and field.fieldWidth) \
                or Utilities.isNumberField(field.fieldType) \
                or Utilities.isDateField(field.fieldType)
            if isTmp and not field.isKey:
                fieldName = "@temp_" + field.fieldName
                hasTmps = True
            else:
                fieldName = field.fieldName
            if isFirst:
                sql += f"({fieldName}"
                isFirst = False
            else:
                sql += f", {fieldName}"
        sql += ")\n"
        if hasTmps:
            isFirst = True
            for field in fields:
                if not field.isKey:
                    isTmp = field.fieldType == 'TEXT' \
                        or field.fieldType == 'VARCHAR' \
                        or field.fieldType == 'STRING' \
                        or field.fieldType == 'TEXT'
                    if isTmp and field.fieldWidth:
                        if isFirst:
                            sql += "SET "
                            isFirst = False
                        else:
                            sql += ",\n    "
                        fieldName = "@temp_" + field.fieldName
                        sql += f"{field.fieldName} = " \
                            f"nullif(substring({fieldName}, 1," \
                            f" {field.fieldWidth}), '')"
                    isTmp = Utilities.isNumberField(field.fieldType) \
                        or Utilities.isDateField(field.fieldType)
                    if isTmp:
                        if isFirst:
                            sql += "SET "
                            isFirst = False
                        else:
                            sql += ",\n    "
                        fieldName = "@temp_" + field.fieldName
                        sql += f"{field.fieldName} = " \
                            f"IF({fieldName}='' OR {fieldName}='\n' OR " \
                            f"{fieldName}='\r', NULL, {fieldName})"
        sql += ";"
        # parent.appendLog(f"{sql}")
        parent.appendLog(f'    load started {Utilities.getNowString()}...')
        Database.executeSQLwithWarnings(parent, cnx, sql)
        Database.commit(parent, cnx)
        parent.appendLog(f'    load finished {Utilities.getNowString()}...')
    # /loadTableDirect

    def loadTableFile(self, parent, cnx,
                      schemaname, tablename, fields, geometry, key,
                      append, directoryName, zipFileName, zip, zipDate,
                      csvFileName, fcnt):
        # parent.appendLog(f'\tloadTableFile {schemaname}.{tablename}')
        startTime = Utilities.getNow()
        self.dropIndexes(parent, cnx, schemaname, tablename)
        parent.appendLog(f'    load feature data into {schemaname}.{tablename}')
        sql1 = self.loadTableFileSqlPrefix(schemaname, tablename, fields)
        parent.appendLog(f'    load data from {csvFileName}')
        counters = Counters()
        appendCnt = self.featureCount(parent, cnx,
                                      append, schemaname, tablename, key)
        startTimeLoad = Utilities.getNow()
        parent.appendLog(f'    load started {Utilities.getNowString()}...')
        parent.readStatus(f"{schemaname}.{tablename}",
                          startTimeLoad, fcnt, counters.readCnt)
        csvFilePath = Utilities.getCsvFilepath(zip, csvFileName)
        csv.field_size_limit(sys.maxsize)
        csvFile = io.TextIOWrapper(zip.open(csvFilePath), encoding="utf-8-sig")
        reader = csv.DictReader(csvFile)
        for row in reader:
            counters.increment(counters.READ)
            keyValue = self.getKeyValue(row, fields)
            if self.isFeatureExist(parent, cnx,
                                   append, appendCnt, counters.readCnt,
                                   schemaname, tablename,
                                   key, keyValue):
                counters.increment(counters.DUPLICATE)
            else:
                isFirst = True
                geoMissing = False
                for field in fields:
                    if isFirst:
                        sql = sql1
                        isFirst = False
                    else:
                        sql += ",\n "
                    if field.fieldSrc == "1":
                        value = f"{counters.readCnt}"
                    else:
                        value = row[field.fieldSrc]
                        if Utilities.isGeometryField(field.fieldType):
                            if Utilities.isNull(value):
                                geoMissing = True
                            else:
                                geotype = value[0:value.find('(') - 1] \
                                    .rstrip().upper()
                                if Utilities.isGeometryField(geotype):
                                    geometry = self.modGeometryType(
                                        parent, cnx,
                                        counters.readCnt, geometry, geotype,
                                        schemaname, tablename)
                                    value = Utilities.getGeometryValue(
                                        geometry, geotype, value)
                                else:
                                    geoMissing = True
                        elif Utilities.isNull(value):
                            value = "NULL"
                        elif Utilities.isTextField(field.fieldType):
                            value = Utilities.getTextValue(
                                value, field.fieldWidth)
                        elif Utilities.isDateField(field.fieldType):
                            value = "'" + value + "'"
                        elif isinstance(value, str):
                            value = "'" + value + "'"
                        else:  # may need more conversions for other field types
                            pass
                    sql += value
                sql += ");"
                if geoMissing:
                    counters.increment(counters.FAIL)
                    parent.appendLog(
                        f'Error inserting record {counters.readCnt} '
                        f'(id={keyValue}) into '
                        f'{schemaname}.{tablename}'
                        f' - Invalid feature geometry')
                else:
                    self.insertFeature(parent, cnx, schemaname, tablename,
                                       sql, counters)
            parent.readStatus(
                f"{schemaname}.{tablename}",
                startTimeLoad, fcnt, counters.readCnt)
        Database.commit(parent, cnx)
        csvFile.close()
        parent.appendLog(f'    load finished {Utilities.getNowString()}...')
        parent.appendLog(
            f'    {counters.readCnt:,} records processed out of {fcnt:,}')
        parent.appendLog(
            f'        {counters.writeCnt:,} loaded'
            f'        {counters.failCnt:,} failed'
            f'        {counters.duplicateCnt:,} duplicates skipped')
        elapsed = Utilities.getElapsedTime(startTime)
        self.setDatasetTable(
            parent, cnx,
            schemaname, tablename, zipFileName, zipDate,
            counters.writeCnt + counters.duplicateCnt, elapsed)
        self.createIndexes(parent, cnx, schemaname, tablename, fields)
        parent.readStatus(None)
        parent.appendLog(f'    load completed {Utilities.getNowString()}')
        parent.appendLog(f'    elapsed time {elapsed}')
        return geometry
    # /loadTableFile

    def insertFeature(self, parent, cnx, schemaname, tablename, sql, counters):
        try:
            if Database.executeSQL(parent, cnx, sql, True):
                counters.increment(counters.WRITE)
                if counters.writeCnt % 1000 == 0:
                    Database.commit(parent, cnx)
            else:
                counters.increment(counters.FAIL)
                parent.appendLog(
                    f'Error inserting record {counters.readCnt:} into '
                    f'{schemaname}.{tablename}')
        except (SQLError) as err:
            if err.errNo == Database.DUP_ENTRY:
                counters.increment(counters.DUPLICATE)
            else:
                counters.increment(counters.FAIL)
                parent.appendLog(
                    f'Error inserting record {counters.readCnt:} into '
                    f'{schemaname}.{tablename}'
                    f'\nSQLERR:{err.errNo} {err.errText}')
                # parent.appendLog(err.errSql)
    # /insertFeature

    def loadTableFileSqlPrefix(self, schemaname, tablename, fields):
        sql = f"INSERT INTO {schemaname}.{tablename}\n("
        isFirst = True
        for field in fields:
            if isFirst:
                sql = f"{sql}{field.fieldName}"
                isFirst = False
            else:
                sql = f"{sql}, {field.fieldName}"
        sql += ")\nVALUES\n("
        return sql
    # /loadTableFileSqlPrefix

    def getZipDate(self, zip, csvFileName):
        zipDate = None
        for fileName in zip.namelist():
            if fileName.endswith(csvFileName):
                t = list(zip.getinfo(fileName).date_time)
                dt = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
                zipDate = Utilities.getLatestInfoDate(
                    zipDate,
                    dt)
        return zipDate
    # /getZipDate

    def getTableGeometry(self, parent, cnx, schemaname, tablename, geometry):
        if schemaname and tablename:
            sql = "SELECT upper(c.COLUMN_TYPE) AS COLUMN_TYPE " \
                  "FROM information_schema.COLUMNS c " \
                  "INNER JOIN information_schema.TABLES t " \
                  "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
                  "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
                  "AND c.TABLE_NAME = t.TABLE_NAME " \
                  f"WHERE t.TABLE_SCHEMA='{schemaname}' " \
                  f"AND t.TABLE_NAME='{tablename}' " \
                  "AND c.COLUMN_NAME='SHAPE';"
            g = Database.readDatabaseResult(parent, cnx, sql)
            if g:
                return g
        return geometry
    # /getTableGeometry

    def getPrjId(self, parent, cnx, schemaname, zip, vrtname):
        prjfile = None
        prjText = None
        prjId = None
        projName = None
        for fileName in zip.namelist():
            if fileName.endswith(f'{vrtname}.prj'):
                prjfile = fileName
                parent.appendLog(f'    analysing\t{prjfile}...')
                for line in zip.open(prjfile):
                    prjText = line.decode('utf-8')
        if prjText:
            osr.UseExceptions()
            try:
                srs = osr.SpatialReference()
                srs.ImportFromWkt(prjText)
                srs.AutoIdentifyEPSG()
                projName = srs.GetName()
                epsg = srs.GetAuthorityCode(None)
                authority = srs.GetAuthorityName(None)
                parent.appendLog(
                    f'    projection\t{projName} '
                    f'({authority}:{epsg})')
            except RuntimeError:
                q1 = prjText.find('"')
                if q1 < 0:
                    q2 = q1
                else:
                    q2 = prjText.find('"', q1 + 1)
                if q2 < 0:
                    projName = prjText
                else:
                    projName = prjText[q1 + 1:q2]
                parent.appendLog(f'    projection\t{projName} (EPSG:unknowen)')
            sql = f"SELECT SRID FROM {schemaname}.spatial_ref_sys " \
                f"WHERE SRTEXT='{prjText}';"
            prjId = Database.readDatabaseResult(parent, cnx, sql)
            if prjId:
                parent.appendLog('    found existing projection')
            else:
                parent.appendLog('    insert new projection')
                sql = "SELECT max(SRID) " \
                    f"FROM {schemaname}.spatial_ref_sys;"
                prjId = Database.readDatabaseResult(parent, cnx, sql)
                if prjId:
                    prjId += 1
                else:
                    prjId = 1
                sql = f"INSERT INTO {schemaname}.spatial_ref_sys " \
                    "(SRID, AUTH_NAME, AUTH_SRID, SRTEXT) VALUES " \
                    f"({prjId}, NULL, NULL, '{prjText}');"
                Database.executeSQL(parent, cnx, sql, True)
                Database.commit(parent, cnx)
        else:
            parent.appendLog('    proj file not found, use default projection')
            sql = f"SELECT min(SRID) FROM {schemaname}.spatial_ref_sys;"
            prjId = Database.readDatabaseResult(parent, cnx, sql)
        return prjId
    # /getPrjId

    def truncateTable(self, parent, cnx,
                      schemaname, tablename, dataset, zipDate,
                      fields, zipFileName):
        if dataset:
            pass
        else:
            sql = f"DROP TABLE {schemaname}.{tablename};"
            if Database.executeSQL(parent, cnx, sql, True):
                sql = f"DELETE FROM {schemaname}.geometry_columns " \
                      f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
                      f"AND F_TABLE_NAME='{tablename}';"
                Database.executeSQL(parent, cnx, sql, True)
                self.createTable(
                    parent, cnx, schemaname, tablename, fields, zipFileName)
            return True
        schemaDate = dataset[3]
        datacnt = int(dataset[4])
        if datacnt > 0 and not Utilities.isNewer(zipDate, schemaDate):
            parent.appendLog('    \tlatest data already loaded into '
                             f'{schemaname}.{tablename}')
            return False
        if Utilities.isNewer(zipDate, schemaDate) and datacnt == 0:
            parent.appendLog(
                '    restart incomplete data load into '
                f'{schemaname}.{tablename}')
        elif Utilities.isNewer(zipDate, schemaDate):
            sql = f"DROP TABLE {schemaname}.{tablename};"
            parent.appendLog(
                f'    delete old data from {schemaname}.{tablename}')
            if Database.executeSQL(parent, cnx, sql, True):
                sql = f"DELETE FROM {schemaname}.geometry_columns " \
                      f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
                      f"AND F_TABLE_NAME='{tablename}';"
                Database.executeSQL(parent, cnx, sql, True)
                sql = f"DELETE FROM {schemaname}.table_datasets " \
                      f"WHERE schemaname='{schemaname}' " \
                      f"AND tablename='{tablename}';"
                Database.executeSQL(parent, cnx, sql, True)
                self.createTable(
                    parent, cnx, schemaname, tablename, fields, zipFileName)
        return True
    # /truncateTable

    def createTable(self, parent, cnx,
                    schemaname, tablename, fields, filename):
        parent.appendLog(
            f'    create table {schemaname}.{tablename}')
        sql = f"CREATE TABLE IF NOT EXISTS {schemaname}.{tablename} "
        isFirst = True
        hasPK = False
        for field in fields:
            if isFirst:
                sql += "("
                isFirst = False
            else:
                sql += ", "
            sql += f"{field.fieldName} "
            sql += f"{field.fieldType}"
            if field.fieldWidth:
                sql += f"({field.fieldWidth})"
            if field.fieldSrc == '1' or field.isKey:
                if hasPK:
                    sql += " NOT NULL UNIQUE KEY"
                else:
                    sql += " PRIMARY KEY"
                    hasPK = True
            elif Utilities.isGeometryField(field.fieldType):
                sql += " NOT NULL"
        sql += ");"
        # parent.appendLog(sql)
        Database.executeSQL(parent, cnx, sql, True)
        self.setDatasetTable(parent, cnx, schemaname, tablename, filename)
    # /createTable

    def setTableGeometry(self, parent, cnx, schemaname, tablename,
                         geometry, extents, prjId, fields):
        if geometry and prjId:
            shapeField = None
            keyField = None
            if fields:
                for field in fields:
                    if Utilities.isGeometryField(field.fieldType):
                        shapeField = field
                    if field.isKey:
                        keyField = field.fieldName
                if keyField:
                    pass
                else:
                    keyField = "OGR_FID"
            if shapeField:
                sql = f"SELECT TYPE FROM {schemaname}.geometry_columns " \
                    f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
                    f"AND F_TABLE_NAME='{tablename}';"
                geometryType = Database.readDatabaseResult(parent, cnx, sql)
                if geometryType:
                    parent.appendLog(f'    existing geometry layer {tablename}')
                    if self.isGeometryExtra(parent, cnx, schemaname, tablename):
                        parent.appendLog('    updating geometry extents')
                        sql = f"UPDATE {schemaname}.geometry_columns " \
                              f"SET GEOMETRY_TYPE='{geometryType}', " \
                              f"QGIS_XMIN={extents[0]}, " \
                              f"QGIS_YMIN={extents[1]}, " \
                              f"QGIS_XMAX={extents[2]}, " \
                              f"QGIS_YMAX={extents[3]}, " \
                              f"QGIS_PKEY='{keyField}' " \
                              f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
                              f"AND F_TABLE_NAME='{tablename}';"
                    else:
                        parent.appendLog('    updating geometry type')
                        sql = f"UPDATE {schemaname}.geometry_columns " \
                              f"SET GEOMETRY_TYPE='{geometryType}' " \
                              f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
                              f"AND F_TABLE_NAME='{tablename}';"
                    Database.executeSQL(parent, cnx, sql, True)
                    Database.commit(parent, cnx)
                else:
                    parent.appendLog(f'    create geometry layer {tablename}')
                    if self.isGeometryExtra(parent, cnx, schemaname, tablename):
                        sql = "INSERT INTO " \
                              f"{schemaname}.geometry_columns " \
                              "(F_TABLE_CATALOG, F_TABLE_SCHEMA, " \
                              "F_TABLE_NAME, F_GEOMETRY_COLUMN, " \
                              "COORD_DIMENSION, SRID, " \
                              "TYPE, GEOMETRY_TYPE, " \
                              "QGIS_XMIN, QGIS_YMIN, " \
                              "QGIS_XMAX, QGIS_YMAX, " \
                              "QGIS_PKEY) " \
                              "VALUES (" \
                              "NULL, " \
                              f"'{schemaname}', " \
                              f"'{tablename}', " \
                              f"'{shapeField .fieldName}', 2, " \
                              f"{prjId}, " \
                              f"'{shapeField .fieldType}', " \
                              f"'{shapeField .fieldType}', " \
                              f"{extents[0]}, {extents[1]}, " \
                              f"{extents[2]}, {extents[3]}, " \
                              f"'{keyField}');"
                    else:
                        sql = "INSERT INTO " \
                              f"{schemaname}.geometry_columns " \
                              "(F_TABLE_CATALOG, F_TABLE_SCHEMA, " \
                              "F_TABLE_NAME, F_GEOMETRY_COLUMN, " \
                              "COORD_DIMENSION, SRID, TYPE) " \
                              "VALUES (" \
                              f"NULL, '{schemaname}', '{tablename}', " \
                              f"'{shapeField .fieldName}', 2, " \
                              f"{prjId}, '{shapeField .fieldType}');"
                    Database.executeSQL(parent, cnx, sql, True)
                    Database.commit(parent, cnx)
            else:
                parent.appendLog('    no geometry')
    # /setTableGeometry

    def updateTableGeometry(self, parent, cnx, schemaname, tablename, geometry):
        sql = f"SELECT TYPE FROM {schemaname}.geometry_columns " \
              f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
              f"AND F_TABLE_NAME='{tablename}';"
        result = Database.readDatabaseResult(parent, cnx, sql)
        if result:
            if result != geometry:
                parent.appendLog(f'    updating geometry type to {geometry}')
                if self.isGeometryExtra(parent, cnx, schemaname, tablename):
                    sql = f"UPDATE {schemaname}.geometry_columns " \
                          f"SET TYPE='{geometry}', " \
                          f"GEOMETRY_TYPE='{geometry}' " \
                          f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
                          f"AND F_TABLE_NAME='{tablename}';"
                else:
                    sql = f"UPDATE {schemaname}.geometry_columns " \
                          f"SET TYPE='{geometry}' " \
                          f"WHERE F_TABLE_SCHEMA='{schemaname}' " \
                          f"AND F_TABLE_NAME='{tablename}';"
                Database.executeSQL(parent, cnx, sql, True)
                Database.commit(parent, cnx)
        else:
            parent.appendLog(f'    missing geometry layer {tablename}')
    # /updateTableGeometry

    def isGeometryExtra(self, parent, cnx, schemaname, tablename):
        sql = f"SELECT count(*) AS cnt " \
            "FROM information_schema.COLUMNS c " \
            f"WHERE c.TABLE_SCHEMA='{schemaname}' " \
            f"AND c.TABLE_NAME='geometry_columns' " \
            "AND upper(c.COLUMN_NAME) IN ('geometry_type', " \
            "'qgis_xmin', 'qgis_ymin', 'qgis_xmax', 'qgis_ymax', 'qgis_pkey');"
        fcnt = Database.readDatabaseResult(parent, cnx, sql)
        return (fcnt > 5)
    # /isGeometryExtra

    def modGeometryType(self, parent, cnx,
                        cnt, geometry, geotype, schemaname, tablename):
        if geometry == geotype:
            return geometry
        if geometry == 'MULTI' + geotype or geometry == geotype + 'COLLECTION':
            return geometry
        if cnt == 0:
            parent.appendLog(f'    change geometry to {geotype}')
            sql = f"ALTER TABLE {schemaname}.{tablename} " \
                  f"MODIFY SHAPE {geotype} NOT NULL;"
            Database.executeSQL(parent, cnx, sql, True)
            self.updateTableGeometry(parent, cnx,
                                     schemaname, tablename, geotype)
            return geotype
        if geotype == 'MULTI' + geometry \
           or geotype == geometry + 'COLLECTION':
            #  modify up table
            parent.appendLog(f'    change geometry to {geotype}')
            match geotype:
                case 'POINT':
                    c1 = "ST_PointFromText"
                case 'MULTIPOINT':
                    c1 = "ST_MPointFromText"
                case 'LINESTRING':
                    c1 = "ST_LineFromText"
                case 'MULTILINESTRING':
                    c1 = "ST_MLineFromText"
                case 'POLYGON':
                    c1 = "ST_PolyFromText"
                case 'MULTIPOLYGON':
                    c1 = "ST_MPolyFromText"
                case 'GEOMETRY':
                    c1 = "ST_GeomFromText"
                case 'GEOMETRYCOLLECTION':
                    c1 = "ST_GeomCollFromText('"
            sql = f"ALTER TABLE {schemaname}.{tablename} " \
                  "RENAME COLUMN SHAPE TO TEMP, " \
                  f"ADD COLUMN SHAPE {geotype};"
            Database.executeSQL(parent, cnx, sql, True)
            sql = f"UPDATE {schemaname}.{tablename} " \
                  f"SET SHAPE={c1}(concat(replace(ST_AsText(TEMP), " \
                  f"'{geometry}', '{geotype}('), ')'));"
            Database.executeSQL(parent, cnx, sql, True)
            Database.commit(parent, cnx)
            sql = f"ALTER TABLE {schemaname}.{tablename} " \
                  f"DROP COLUMN TEMP, " \
                  f"MODIFY COLUMN SHAPE {geotype} NOT NULL;"
            Database.executeSQL(parent, cnx, sql, True)
            self.updateTableGeometry(parent, cnx,
                                     schemaname, tablename, geotype)
            return geotype
            #  invalid data, can not convert
        return geometry
    # /modGeometryType

    def getKeyValue(self, row, fields):
        keyValue = None
        for field in fields:
            if field.isKey:
                value = row[field.fieldSrc]
                if Utilities.isTextField(field.fieldType):
                    keyValue = Utilities.getTextValue(value, field.fieldWidth)
                elif Utilities.isDateField(field.fieldType):
                    keyValue = "'" + value + "'"
                else:
                    keyValue = value
        return keyValue
    # /getKeyValue

    def featureCount(self, parent, cnx, append, schemaname, tablename, key):
        if append:
            if key:
                k = key
            else:
                k = "1"
            sql = f"SELECT count({k}) FROM {schemaname}.{tablename};"
            cnt = Database.readDatabaseResult(parent, cnx, sql, True)
            return int(cnt)
        return 0
    # /featureCount

    def isFeatureExist(self, parent, cnx, append, appendCnt, readCnt,
                       schemaname, tablename, key, keyValue):
        if append:
            if appendCnt > readCnt:
                return True
            if key and keyValue:
                if isinstance(keyValue, str):
                    value = f"'{keyValue}'"
                else:
                    value = keyValue
                sql = "SELECT ifnull(EXISTS(" \
                      f"SELECT 1 FROM {schemaname}.{tablename} " \
                      f"WHERE {key}={value}" \
                      "), 0);"
                exist = Database.readDatabaseResult(parent, cnx, sql, True)
                return (exist == 1)
        return False
    # /isFeatureExist

    def getDataset(self, parent, cnx, schemaname, tablename, filename=None):
        sql = "SELECT schemaname, tablename, " \
              "dataset_file, dataset_date, ifnull(dataset_cnt, 0), " \
              "dataset_load_seconds " \
              f"FROM {schemaname}.table_datasets " \
              f"WHERE schemaname='{schemaname}' " \
              f"AND tablename='{tablename}' LIMIT 1;"
        datasets = Database.readDatabase(parent, cnx, sql)
        if datasets:
            dataset = datasets[0]
        else:
            dataset = None
        if filename:
            sql = f"UPDATE {schemaname}.table_datasets " \
                  f"SET dataset_file='{filename}' " \
                  f"WHERE schemaname='{schemaname}' " \
                  f"AND tablename='{tablename}' " \
                  f"AND dataset_file IS NULL;"
            Database.executeSQL(parent, cnx, sql, True)
            Database.commit(parent, cnx)
        return dataset
    # /getDataset

    def setDatasetTable(self, parent, cnx, schemaname, tablename,
                        filename=None, filedate=None, cnt=0, elapsed=None):
        sql = f"SELECT schemaname FROM {schemaname}.table_datasets " \
            f"WHERE schemaname='{schemaname}' " \
            f"AND tablename='{tablename}';"
        result = Database.readDatabaseResult(parent, cnx, sql)
        if result:
            sql = f"UPDATE {schemaname}.table_datasets " \
                "SET dataset_file="
            if filename:
                sql += f"'{filename}'"
            else:
                sql += "NULL"
            sql += ", dataset_date="
            if filedate:
                sql += f"'{filedate}'"
            else:
                sql += "NULL"
            sql += f", dataset_cnt={cnt}"
            if elapsed is not None:
                t = int(elapsed.total_seconds())
                sql += f", dataset_load_seconds={t}"
            sql += f" WHERE schemaname='{schemaname}' " \
                f"AND tablename='{tablename}';"
        else:
            sql = f"INSERT INTO {schemaname}.table_datasets " \
                "(schemaname, tablename, " \
                "dataset_file, dataset_date, dataset_cnt, " \
                "dataset_load_seconds) " \
                f"VALUES('{schemaname}', '{tablename}', "
            if filename:
                sql += f"'{filename}', "
            else:
                sql += "NULL, "
            if filedate:
                sql += f"'{filedate}', "
            else:
                sql += "NULL, "
            sql += f"{cnt}, "
            if elapsed is not None:
                t = int(elapsed.total_seconds())
                sql += f", dataset_load_seconds={t}"
            else:
                sql += "NULL);"
        Database.executeSQL(parent, cnx, sql, True)
        Database.commit(parent, cnx)
    # /setDatasetTable

    def dropIndexes(self, parent, cnx, schemaname, tablename):
        parent.appendLog('    drop indexes...')
        sql = "SELECT INDEX_NAME " \
              "FROM information_schema.statistics " \
              f"WHERE TABLE_SCHEMA='{schemaname}' " \
              f"AND TABLE_NAME='{tablename}' " \
              f"AND INDEX_NAME!='PRIMARY' " \
              f"AND INDEX_NAME!='UNIQUE';"
        indexes = Database.readDatabase(parent, cnx, sql)
        for index in indexes:
            sql = f"ALTER TABLE {schemaname}.{tablename} " \
                  f"DROP INDEX {index[0]};"
            Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog('    dropped indexes')
    # /dropIndexes

    def createMissingIndexes(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'\nCreating indexes in {schemaname}...')
        sql = "SELECT c.TABLE_NAME, c.COLUMN_NAME, " \
              "c.ORDINAL_POSITION, c.DATA_TYPE\n" \
              "FROM information_schema.COLUMNS c " \
              "INNER JOIN information_schema.TABLES t " \
              "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
              "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
              "AND c.TABLE_NAME = t.TABLE_NAME\n" \
              f"WHERE t.TABLE_SCHEMA = '{schemaname}' " \
              "AND t.TABLE_TYPE='BASE TABLE' " \
              "AND t.TABLE_NAME not in ('geometry_columns', " \
              "'apatial_ref_sys', 'table_datasets')\n" \
              "EXCEPT\n" \
              "SELECT c.TABLE_NAME, c.COLUMN_NAME, " \
              "c.ORDINAL_POSITION, c.DATA_TYPE\n" \
              "FROM information_schema.COLUMNS c " \
              "INNER JOIN information_schema.TABLES t " \
              "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
              "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
              "AND c.TABLE_NAME = t.TABLE_NAME\n" \
              "INNER JOIN information_schema.statistics s " \
              "ON c.TABLE_CATALOG = s.TABLE_CATALOG " \
              "AND c.TABLE_SCHEMA = s.TABLE_SCHEMA " \
              "AND c.TABLE_NAME = s.TABLE_NAME " \
              "AND c.COLUMN_NAME = s.COLUMN_NAME\n" \
              f"WHERE t.TABLE_SCHEMA = '{schemaname}' " \
              "AND t.TABLE_TYPE='BASE TABLE' " \
              "AND t.TABLE_NAME not in ('geometry_columns', " \
              "'apatial_ref_sys', 'table_datasets')\n" \
              "ORDER BY TABLE_NAME ASC, ORDINAL_POSITION ASC;"
        fields = Database.readDatabase(parent, cnx, sql)
        for field in fields:
            if Utilities.isGeometryField(field[3]):
                log = '    ' \
                      f'{str("create feature shape index ").ljust(48)}' \
                      f'  on {field[0].ljust(40)}' \
                      f'  {Utilities.getNowString()}...'
                parent.appendLog(log)
                sql = f"ALTER TABLE {schemaname}.{field[0]} " \
                      f"ADD SPATIAL INDEX ({field[1]});"
                Database.executeSQL(parent, cnx, sql, True)
            elif Utilities.isCreateFieldIndex(field[1], field[3]):
                parent.appendLog(f'    create index {field[1].ljust(35)}'
                                 f'  on {field[0].ljust(40)}'
                                 f'  {Utilities.getNowString()}...')
                sql = f"ALTER TABLE {schemaname}.{field[0]} " \
                      f"ADD INDEX ({field[1]});"
                Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog(f'Created indexes in {schemaname}')
        parent.unsetCursor()
    # /createMissingIndexes

    def createIndexes(self, parent, cnx, schemaname, tablename, fields):
        parent.appendLog('    create indexes...')
        for field in fields:
            if Utilities.isGeometryField(field.fieldType):
                parent.appendLog('    create feature shape index '
                                 f'\t{Utilities.getNowString()}...')
                sql = f"ALTER TABLE {schemaname}.{tablename} " \
                      f"ADD SPATIAL INDEX ({field.fieldName});"
                Database.executeSQL(parent, cnx, sql, True)
            elif Utilities.isCreateFieldIndex(
                    field.fieldName,
                    field.fieldType,
                    field.isKey,
                    field.fieldSrc):
                parent.appendLog(f'    create {field.fieldName} index '
                                 f'\t{Utilities.getNowString()}...')
                sql = f"ALTER TABLE {schemaname}.{tablename} " \
                      f"ADD INDEX ({field.fieldName});"
                Database.executeSQL(parent, cnx, sql, True)
        parent.appendLog('    created indexes')
    # /createIndexes

    def processViews(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'\nCreating views in {schemaname}...')
        scriptName = 'linz_schema_views.sql'
        try:
            sqlFile = open(scriptName, 'rt')
            parent.appendLog(f'{scriptName} found')
            self.processViewsScript(parent, cnx, schemaname, sqlFile)
            sqlFile.close()
            parent.appendLog(f'Created views in {schemaname}')
        except IOError:
            try:
                (root, ext) = os.path.split(__file__)
                (file, ext) = os.path.splitext(root)
                if ext == '.zip' or ext == '.pyz':
                    with zipfile.ZipFile(root, 'r') as zip:
                        sqlFile = zip.open(scriptName, 'r')
                        parent.appendLog(f'{scriptName} found')
                        self.processViewsScript(parent, cnx,
                                                schemaname, sqlFile, True)
                        sqlFile.close()
                        parent.appendLog(f'Created views in {schemaname}')
                else:
                    (root, file) = os.path.split(__file__)
                    sqlFile = open(os.path.join(root, scriptName), 'rt')
                    parent.appendLog(f'{scriptName} found')
                    self.processViewsScript(parent, cnx, schemaname, sqlFile)
                    sqlFile.close()
                    parent.appendLog(f'Created views in {schemaname}')
            except IOError as err:
                parent.appendLog(f'Failed to open sql script {scriptName}'
                                 f'\n    {__file__}/{scriptName}\n{err}')
        parent.unsetCursor()
    # /processViews

    def processViewsScript(self, parent, cnx,
                           schemaname, sqlFile, zipped=False):
        parent.appendLog('Run sql script...')
        try:
            sql = None
            dependencies = None
            for zline in sqlFile:
                if zipped:
                    line = zline.decode('utf-8')
                else:
                    line = zline
                if line:
                    line = line.replace('\r\n', '\n').lstrip().rstrip()
                    if line.startswith('#') or line.startswith('--'):
                        if line.find("--DEPENDENCIES--") >= 0:
                            d1 = line.find("{") + 1
                            d2 = line.find("}")
                            dependencies = line[d1:d2]
                    else:
                        if sql:
                            sql += '\n' + line
                        else:
                            sql = line
                        if sql.endswith(';'):
                            sql = self.processViewsScriptSql(
                                parent, cnx, schemaname, sql, dependencies)
                            dependencies = None
        except IOError as err:
            parent.appendLog(f'Failed to read sql script\n{err}')
    # /processViewsScript

    def processViewsScriptSql(self, parent, cnx, schemaname, sql, dependencies):
        sqlT = sql.replace('{schema}', schemaname)
        viewname = Utilities.createViewname(sqlT)
        if Utilities.isDropSql(sqlT):
            parent.appendLog(f'    Drop view {viewname}')
            Database.executeSQL(parent, cnx, sqlT)
        else:
            isDependent = False
            parent.appendLog(f'    Create view {viewname}')
            if dependencies:
                for dependency in dependencies.split():
                    if Database.isTableExist(parent, cnx,
                                             schemaname, dependency):
                        pass
                    else:
                        isDependent = True
                        parent.appendLog(
                            "        dependency not found: "
                            f"{schemaname}.{dependency}")
            if isDependent:
                parent.appendLog('    view not created')
            else:
                Database.executeSQL(parent, cnx, sqlT)
        return None
    # /processViewsScriptSql
# /SchemasActions
