<!DOCTYPE html>
<html>
<body lang="en-NZ" dir="ltr">
<h2>LINZ Schema Loader</h2><br/>
<p>
    App and QGIS Plugin to load New Zealand LINZ Data Service files directly into a MariaDB/MySQL database and create
    QGIS feature objects and relationships.  Even though this App was
    designed for QGIS, the App can run stand-alone and the Database
    Schema Options used to load a database for other GIS software.<br/>
<br/>
Designed as a stand-alone Python App and as a plugin for QGIS version 3.40+ and is QGIS4 ready but yet to be tested.<br/>
Python 3.11+<br/>
Requires Python module for database access (eg. mariadb or MySQLdb), this may have to be installed from the console using pip:<br/>
> pip install mariadb<br/>
Requires Python modules for Qt (eg. PyQt6 or PySide6)<br/>
Supports Qt5 &amp; Qt6<br/>
<br/>
Requires a working MariaDB/MySQL database with root access.<br/>
LINZ Schema Loader, the local database and QGIS should be operated from the same workstation/server. 
The local database can be on a separate server as long as the required DBA privileges are granted.<br/>
<br/>
GIS data is acquired from the LINZ Data Service at
<a href="https://data.linz.govt.nz/data/">https://data.linz.govt.nz/data/</a><br/>
• Create your “Kordinates” account profile and API keys.<br/>
• Select the data required out of the “Data Types” (Layers, Tables,
Sets) and choose to “Export”.<br/>
• Select the export type as “CSV” and choose the required “Coordinate Reference System”
for your project (eg. “NZGD2000 (ESPG:4167)” or “NZGD2000 / New
Zealand Transverse Mercator 2000 (ESPG:2193)”)<br/>
• “Create Export” then wait for the export is complete before downloading the
created file to an accessible local directory.<br/>
<br/>
Install LINZ Schema Loader from the QGIS plugin menu or set-up as a stand-alone App.<br/>
</p>
<h3>Main Menu</h3>
<p>
    • Connect to Database - 
    Use this option to connect to your database.<br/>
    For the "Database Schemas" menu, it is advisable to connect using the database root/manager login.<br/>
    For the "Map Layers" menu, it is advisable to connect using a database user login, rather than root.<br/>
<br/>
    • Select Schema - 
    Select the database schema that the GIS data is stored in.<br/>
    A list of default schema names is provided. Any database schema that contains GIS spatial dictionary tables will be added.<br/>
    If a GIS schema doesn’t already exist, use the “Create Schema” option below.<br/>
    To clear the currently selected schema, use the "Cancel" button from "Select Schema".<br/>
</p>
<h3>Database Schemas Menu</h3>
<p>
    This menu is for GIS data administration of the local database.<br/>
    These options are only available when connected to a database, preferable as a root/administrator user.<br/>
    <b>It is strongly recommended to perform a database backup before embarking on any database schema options.</b><br/>
<br/>
    • Create Schema - 
    Creates a new database schema with GIS spatial dictionary tables.<br/>
    This option is only available if the selected schema doesn't already exist from "Select Schema" above, or no schema is selected.<br/>
    If no schema is selected, then you will be able to enter a new schema name and description. This schema can also be an existing database schema that you wish to add GIS spatial data.<br/>
    At the completion of creating the schema, data is imported and indexes and views created.<br/>
<br/>
    • Update Schema - 
    Use this option to update the GIS spatial dictionary tables with fields and rows that may be missing.<br/>
    Deprecated LINZ Data Service tables can also be dropped.<br/>
<br/>
    • Drop Schema - 
    This option drops the selected database schema with all it's containing data.<br/>
    <b>Only use this option if you are really sure you want the data removed.</b><br/>
<br/>
    • Import *.csv Data - 
    To import the *.csv files exported from LINZ Data Service, use this option to select the directory that the *.csv files have been saved to.<br/>
    All *.csv files in that directory will be imported into tables that are created and named related with the data name.<br/>
    The projection and spatial information are inserted into the GIS spatial dictionary tables for the schema.<br/>
    If a *.csv file contains a data set, then all the data in the set will be imported into the database.<br/>
    Importing of large files can take a considerable amount of time.<br/>
<br/>
    • Create Indexes - 
    After importing data, this option is used to create database indexes to enable rapid searches on the GIS tables.<br/>
    Fields identified to being automatically indexed include primary keys, shape data, fields that are named as though they are likely to be a foreign key, id or a name.<br/>
    There may be other fields that can be manually indexed if it is likely they will be searched on.<br/>
    Index creation on large tables can take a considerable amount of time.<br/>
<br/>
    • Create Views - 
    After importing data, this option is used to create database views that join GIS tables into useable groups of data simplifying data access.<br/>
    The views are predefined and use known relations.<br/>
    The view creation script "linz_schema_views.sql" will require ongoing maintenance to keep up with LINZ data format changes. 
    Note that "{schema}" automatically gets replaced by the selected schema when creating views.<br/>
</p>
<h3>Map Layers Menu</h3>
<p>
    This menu is for the creation of QGIS project objects for database information.<br/>
    QGIS is required to be installed on the workstation.<br/>
    Running this App stand-alone requires a pre-existing project file which is requested for in each option.<br/>
    Some of these options are only available when connected to a database, preferable as a GIS user.<br/>
<br/>
    • Create Map Layers -
    Use this option to create QGIS Vector Layers for all tables and views in the selected database schema.<br/>
    Layers for both feature and data tables are created.<br/>
<br/>
    • Define Relationships -
    This option creates QGIS Relations between Vector Layers in a project.<br/>
    Relationships are defined for known common primary key-foreign key LINZ data tables.<br/>
    This enables rapid linking between tables using indexed fields.<br/>
    The relationships definition script will require ongoing maintenance to keep up with LINZ data format changes.  
    This is a comma delimited text file "linz_schema_joins.csv" with four columns (tablename, primaryKey, referenceTablename, foreignKey).<br/>
<br/>
    • Define Layer Styles -
    This options loads a set of feature styles into a QGIS project.<br/>
    The styles represent NZ Topographical maps.<br/>
    <b>Warning:</b> Any pre-existing vector layer styles, within the project, may be over-written.<br/>
<br/>
    • Create Topo Style Database - 
    Use this option to create a QGIS style database for the project.<br/>
    The style database, called "NZ Topo Styles" can be used from the QGIS style manager to define the feature styles for vector layers.<br/>
    This style database can be imported into other projects.<br/>
    Existing layer styles will not be over-written.<br/>
    If no styles are shown in the style manager, close the project and reopen it to refresh.<br/>
</p>
<h3>Stand-alone App</h3>
<p>
    When installing LINZ Schema Loader from the QGIS plugin manager, the installation files are placed somewhere like:<br/>
    ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/linz_schema_loader<br/>
<br/>
    The file "linz_schema_loader.pyz" is provided in the distribution as an executable Python application.<br/>
    A Linux desktop file "linz_schema_loader.desktop" is also provided as a shortcut to the Python executable.<br/>
    The properties in the desktop file will have to be updated for the icon and environment variables to point to the right locations:<br/>
    • PYTHONPATH=/opt/qgis_3_44_11/python:$PYTHONPATH (the location of the PyQGIS modules, e.g. /usr/share/qgis/python)<br/>
    • PATH=/opt/qgis_3_44_11/bin:$PATH (the location of the installed version of qgis, e.g. /usr/bin)<br/>
    • the full path to linz_schema_loader.pyz will have to be modified for the local configuration and user.<br/>
    • the Icon full path to icon.svg will have to be modified for the local configuration and user.<br/>
<br/>
    This plugin/app has not been tested in a Windows environment, but is expected to work in theory.<br/>
    You will have to create your own shortcut to run as a stand-alone application.<br/>
</p>
<p>===========================================================================<br/>
</p>
</body>
</html>
