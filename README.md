
# Implementation of a GIS system in renewable energy projects with PostgreSQL + PostGIS and QGIS

[1. Introduction](#1-Introduction)

[2. Database design and development](#2-Database-design-and-development)

>[2.1. Design of the database](#2.1-Design-of-the-database)

>[2.2. Development of the database](#2.2-Development-of-the-database)

>>[2.2.1. Importing shapefiles](#2.2.1-Importing-shapefiles)

>>[2.2.2. Create roles, users and assign permissions](#2.2.2-Create-roles,-users-and-assign-permissions)

>>[2.2.3. Grant accesses to all levels in database](#2.2.3-Grant-accesses-to-all-levels-in-database)

>>[2.2.4. Automated features](#2.2.4-Automated-features)

[3. Finding the best location for the project](#3-Finding-the-best-location-for-the-project)

[4. QGIS integration](#4-QGIS-integration)

>[4.1. PostGIS connection](#4.1-PostGIS-connection)

>[4.2. Attribute Forms](#4.2-Attribute-Forms)

[5. Automated reports](#5-Automated-reports)

>[5.1. Bill of materials](#5.1-Bill-of-materials)

>[5.2. Logs table](#5.2-Logs-table)

## 1.	Introduction

This document is intended to serve as a guide for the implementation of a Geographical Information System in renewable energy projects, specifically in solar photovoltaic plants. Although it can be applied with slight modifications to any civil works project in many other sectors.

The main characteristics that define this system are:

- Database: **PostgreSQL 15.4** 64bit + **PostGIS 3.4.0**.
- Operating Sytem: **Windows 10** Home.
- Multi-user editing.
- **QGIS** integration.

The advantages of choosing a GIS with these characteristics are many, among which are the following:

- Multi-user editing: many different users can work at the same time without losing information. Database administrator can configure the permissions and access to every schema and table or view in the database, assigning roles like editor and reader.

- All QGIS users will have the same styles in the layers, as styles are saved in the database and loaded to the QGIS canvas.
- Possibility to save different project versions in the database.
- QGIS users (or CAD users) will not have to carry out measurements of areas, lengths, units, as everything will be automatized with trigger functions.
- Automatized bill of materials thanks to structured queries to database.

All data information comes from the Database of Topographical Objects (Baza danych obiektów topograficznych BDOT10k) promoted by the Department of Development, Labour and Technology of Poland (Ministerstwo Rozwoju, Pracy i Technologii).

The project will be a simulation of a photovoltaic solar plant located in the county of Łowicz (Poland).

## 2. Database design and development

As mentioned, the database used will be PostgreSQL 15.4 and its extension PostGIS 3.4. For the development it will be used the SQL Shell and sometimes the GUI of PostgreSQL called pgAdmin 4.

### 2.1. Design of the database

Although it is not necessary, I good practice is create several schemas in order to have better organized and structured the database. Besides from the public schema that comes by default with PostgreSQL, the following **schemas** will be created:

- **audit** : it will contain a table called "_ **logs** _" so that the project manager can consult everything that is done on the databases.
- **buildings** : it will have a table called "_ **budynki** __\__" and all the functions, trigger functions or views related to it.
- **forests** : it will contain a table called "_ **ot\_ptlz\_a** _" (named according to the Polish law of 27th July 2021) and all the functions, trigger functions or views related to it.
- **parcels** : it will contain a table called "_ **dzialki** __\__" and all the functions, trigger functions or views related to it.
- **power\_lines** : it will have a table called "_ **ot\_suln\_l** _" (named according to the Polish law of 27th July 2021) and all the functions, trigger functions or views related to it.
- **protected\_areas** : it will contain three tables, one for each of the protected zones present in the area: "_ **ot\_tcon\_a** _" for the Natura 2000 Areas (obszar Natura 2000 in Polish), "_ **ot\_tcpk\_a** _" for Natural Parks (park krajobrazowy) and "_ **ot\_tcrz\_a** _" for Natural Reserves (rezerwat ). All named according to the Polish law of 27th July 2021.
- **roads** : it will have a table called "_ **ot\_skjz\_l** _" (named according to the Polish law of 27th July 2021) and all the functions, trigger functions or views related to it.
- **rushes** : it will have a table called "_ **ot\_oisz\_a** _" (named according to the Polish law of 27th July 2021) and all the functions, trigger functions or views related to it.
- **utility\_poles** : it will have two tables called "_ **ot\_buit\_p** _" for all the transformators installed in the area and "_ **ot\_buwt\_p** _" for the lighting poles and Energy pillars (named according to the Polish law of 27th July 2021) and all the functions, trigger functions or views related to them.
- **wet\_areas** : it will have two tables called "_ **ot\_oimk\_a** _" for all the wetlands and "_ **ot\_oisz\_a** _" for the wet rushes (named according to the Polish law of 27th July 2021) and all the functions, trigger functions or views related to them.
- **electrical\_products** : it will contained all the tables (_ **type\_of\_device** _, _ **devices** _, _ **wires** _, _ **suppliers** _) with information about electrical products as names, descriptions, prices, suppliers, etc.
- **maps** : the schema where all versions of the QGIS project will be saved to.

| ![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/schemas.png) |
| --- |

### 2.2. Development of the database

#### 2.2.1. Creation of database, schemas and tables

In the SQL Shell:

```
--Check if database already exists

DROP DATABASE IF EXISTS oze;

--Create database

CREATE DATABASE oze;

--Create schemas

create schema audit;
create schema buildings;
create schema electrical_products;
create schema forests;
create schema maps
create schema parcels;
create schema power_lines;
create schema protected_areas;
create schema roads;
create schema rushes;
create schema utility_poles;
create schema wet_areas;
```

We will create the following tables in their corresponding schema: _ **logs** _ (in schema audit), _ **new\_ot\_suln\_l** _(in schema powe_lines) and _ **new\_ot\_buit\_p** _(in schema utility_poles).

```
-- Create a table in schema audit to register all changes in all tables in database

CREATE TABLE audit.logs VALUES (
schema_name text not null,
table_name text not null,
user_name text not null,
action char not null check (action in ('I', 'U', 'D')),
action_time timestamptz not null default now(),
old_data jsonb,
new_data jsonb,
);

CREATE INDEX ON audit.logs USING gin(old_data);
CREATE INDEX ON audit.logs USING gin(new_data);
CREATE INDEX ON audit.logs USING brin (action_time);


-- Create tables to draw all the new power lines and devices

-- For new power lines (DC and AC)

CREATE TABLE power_lines.new_ot_suln_l (
gid serial not null primary key,
description varchar(150),
quantity integer NOT NULL,
length DOUBLE PRECISION,
supplierid integer,
wirecode varchar(15)
name varchar(150)
geom geometry(LINESTRING, 2180)
);

ALTER TABLE power_lines.new_ot_suln_l
  ADD CONSTRAINT new_ot_suln_l_check
    CHECK (st_geometrytype(geom) = 'ST_Line'::text
    OR geom IS NULL)
  ADD CONSTRAINT fk_supplierid FOREIGN KEY (supplierid)
    REFERENCES electrical_products.suppliers (supplierid) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


-- For new electrical devices as transformators, junction-boxes, solar panels, etc

CREATE TABLE utility_poles.new_ot_buit_p (
gid serial not null primary key,
id_urzarzednia varchar(80) not null,
teryt varchar(5),
rodzaj varchar(80),
ilosc integer,
wysokosc double precision,
x integer,
y integer,
geom geometry(POINT, 2180)
);

ALTER TABLE utility_poles.new_ot_buit_p
  ADD CONSTRAINT new_ot_buit_p_check
  CHECK (st_geometrytype(geom) = 'ST_Point'::text
  OR geom IS NULL);
```

### 2.2.2. Importing shapefiles

The other tables will be created when importing the shapefiles into the database. We will create a Python script to import all shapefiles to their respective schemas. So, from a Python IDE or console, we run the following script:

```
import os
import fnmatch
import subprocess

root=r'the_root_where_the_shapefiles_are'
pattern = '\*.shp'

def getSchema(filename):
  if filename == "OT_BUIT_P.shp":
  return "utility\_poles"

  elif filename == "OT_BUWT_P.shp":
  return "utility_poles"

  elif filename == "OT_OIMK_A.shp":
  return "wet_areas"

  elif filename == "OT_OISZ_A.shp":
  return "rushes"

  elif filename == "OT_SKJZ_L.shp":
  return "roads"

  elif filename == "OT_SULN_L.shp":
  return "power_lines"

  elif filename == "OT_TCON_A.shp":
  return "protected_areas"

  elif filename == "OT_TCPK_A.shp":
  return "protected_areas"

  elif filename == "OT_TCRZ_A.shp":
  return "protected_areas"

  elif filename == "budynki.shp":
  return "buildings"

  elif filename == "dzialki.shp":
  return "parcels"

  else:
  return None

#walk loop to find the pattern files

for dirpath, dirnames, filenames in os.walk(root):
  for name in filenames:
    if fnmatch.fnmatch(name, pattern):

    #save the path name of the selected file to ff
    ff = os.path.join(dirpath, name)

    #create a name variable to be used for table name in DB
    tablename = name[:-4]

    #get the name of the schema according to the filename
    schema = getSchema(name)

    #Use the commandline shp2pgdql to import the shapefiles
    cmd = "shp2pgsql -I -s 2180 {0} {1}.{2} | psql -U postgres -d oze".format(ff, schema, tablename)

    # run the script from the Shell
    subprocess.run(cmd, shell=True)
```

Once all the tables are created and the shapefiles imported, we check it in the pgAdmin4. We can check the tree on the left or run the following in the Query Tool:

```
SELECT * FROM pg_catalog.pg_tables
WHERE schemaname NOT LIKE '%pg_%' AND schemaname NOT LIKE '%infor%';
```

### 2.2.3. Create roles, users and assign permissions

First, we will create two groups: editor and reader:

```
CREATE ROLE oze_editor WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION;
CREATE ROLE oze_reader WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION;
```

After we create several users and we will assign this users to one of the groups created:

```
-- Create users:

CREATE ROLE piotr WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION CONNECTION LIMIT -1 PASSWORD 'password1';
CREATE ROLE gosia WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION CONNECTION LIMIT -1 PASSWORD 'password2';

-- Assign users to groups:

GRANT oze\_editor TO piotr;
GRANT oze\_reader TO gosia;
```

### 2.2.4. Grant accesses to all levels in database

Next step will be to grant access and permissions to all objects in the database. We have to grant permissions in all levels of the database from the top to the bottom.

```
--Revoke public(all users) access to the DataBase. This is always a good idea:

REVOKE ALL PRIVILEGES ON DATABASE oze FROM public;

--Grant connection to database:

GRANT CONNECT ON DATABASE oze TO oze_editor;
GRANT CONNECT ON DATABASE oze TO oze_reader;
GRANT ALL ON DATABASE oze TO postgres;

-- Permissions on all data schemas

SELECT 'GRANT ALL ON SCHEMA ' || SPLIT_PART(tab_name, '.', 1) || ' TO oze_editor;' AS grant_schema_query
FROM (
SELECT
quote_ident(table_schema) || '.' || quote_ident(table_name) as tab_name
FROM
information_schema.tables
WHERE
table_schema NOT IN ('pg_catalog', 'information_schema', 'audit', 'public')
AND table_schema NOT LIKE 'pg_toast%'
) grantschemalist;

SELECT 'GRANT USAGE ON SCHEMA ' || SPLIT_PART(tab_name, '.', 1) || ' TO oze_reader;' AS grant_schema_query
FROM (
SELECT
quote_ident(table_schema) || '.' || quote_ident(table_name) as tab_name
FROM
information_schema.tables
WHERE
table_schema NOT IN ('pg_catalog', 'information_schema', 'audit', 'public')
AND table_schema NOT LIKE 'pg_toast%'
) grantschemalist;

GRANT USAGE ON SCHEMA audit TO oze_editor, oze_reader;
```
Once the permissions to the schemas area granted, it is time to grant permissions to all relations (tables, sequences, etc.) inside each schema:

```
SELECT 'GRANT ALL ON ALL TABLES IN SCHEMA ' || SPLIT_PART(tab_name, '.', 1) || ' TO oze_editor;' AS grant_schema_objects_query
FROM (
SELECT
quote_ident(table_schema) || '.' || quote_ident(table_name) as tab_name
FROM
information_schema.tables
WHERE
table_schema NOT IN ('pg_catalog', 'information_schema', 'audit', 'public')
AND table_schema NOT LIKE 'pg_toast%'
) grantschemaobjectslist;

SELECT 'GRANT SELECT ON ALL TABLES IN SCHEMA ' || SPLIT_PART(tab_name, '.', 1) || ' TO oze_reader;' AS grant_schema_objects_query
FROM (
SELECT
quote_ident(table_schema) || '.' || quote_ident(table_name) as tab_name
FROM
information_schema.tables
WHERE
table_schema NOT IN ('pg_catalog', 'information_schema', 'public')
AND table_schema NOT LIKE 'pg_toast%'
) grantschemaobjectslist;

SELECT 'GRANT USAGE ON ALL SEQUENCES IN SCHEMA ' || SPLIT_PART(tab_name, '.', 1) || ' TO oze_reader, oze_editor;' AS grant_schema_secuences_query
FROM (
SELECT
quote_ident(table_schema) || '.' || quote_ident(table_name) as tab_name
FROM
information_schema.tables
WHERE
table_schema NOT IN ('pg_catalog', 'information_schema', 'public')
AND table_schema NOT LIKE 'pg_toast%'
) grantschemasecuenceslist;

GRANT TRIGGER ON ALL TABLES IN SCHEMA audit TO oze\_editor, oze\_reader;
```

The permissions in the public schema are a little special. In this schema are saved the layers styles and the Spatial Reference Systems. We don't want to allow full access to this tables to readers, only to editors.

```
--Public schema permissions

GRANT USAGE ON SCHEMA public TO oze\_editor, oze\_reader;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO oze\_editor;
GRANT INSERT, SELECT, UPDATE ON ALL TABLES IN SCHEMA public TO oze\_editor;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO oze\_reader;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO oze\_editor, oze\_reader;
```

### 2.2.5. Automated features

#### 2.2.5.1. Automated features for geospatial objects: coordinates, areas, lengths

First of all, to take advantage of geospatial functions in our database, we have to install PostGIS. It is so easy as run this SQL command:

```
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/create_extension_postgis.png)

In order to avoid measurement errors and to save work for the users, we will create some functions that will automatically provide:

1. The x,y coordinates of the newly installed devices.
2. The length of the new power lines.
3. The area of the new polygon objects (parcels, buildings, etc.)

In pgAdmin4 we will open a new Query window and run following queries:

1. Point X,Y trigger function

```
CREATE OR REPLACE FUNCTION utility\_poles.x\_y\_trigger\_function() RETURNS trigger AS $$
BEGIN
NEW.x = ST_X(NEW.geom)::integer;
NEW.y = ST_Y(NEW.geom)::integer;
RETURN NEW;
END;
$$ language plpgsql;

-- X,Y Point Trigger
CREATE OR REPLACE TRIGGER x_y_trigger BEFORE INSERT OR UPDATE ON utility_poles.new_ot_buwt_p
FOR EACH ROW EXECUTE FUNCTION utility_poles.x_y_trigger_function();
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/x_y_trigger.png)

2. Length trigger function

```
CREATE OR REPLACE FUNCTION power_lines.length_trigger_function() RETURNS trigger AS $$
BEGIN
NEW.length = round(ST_Length(NEW.geom)::integer, 2);
RETURN NEW;
END;
$$ language plpgsql;

-- Length Trigger

CREATE OR REPLACE TRIGGER length_trigger BEFORE INSERT OR UPDATE ON utility_poles.power_lines.new_ot_suln_l
FOR EACH ROW EXECUTE FUNCTION power_lines.length_trigger_function();
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/length_trigger.png)

3. Area trigger function

```
--Parcel area trigger function

CREATE OR REPLACE FUNCTION parcels.parcel_area_trigger_function() RETURNS trigger AS $$
BEGIN
NEW.area = round(ST_Area(NEW.geom)::integer, 2);
RETURN NEW;
END;
$$ language plpgsql;

-- Parcel Area Trigger
CREATE OR REPLACE TRIGGER parcel_area_trigger BEFORE INSERT OR UPDATE ON parcels.dzialki
FOR EACH ROW EXECUTE FUNCTION parcels.parcel_area_trigger_function();
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/area_trigger.png)

#### 2.2.5.2. Automated features for non geospatial objects: log table

On the other hand, we will create the trigger to keep track of all the operations made on the database. We had already create the necessary audit.logs_trigger() function in item 2.2.1. of this document. Now we have to link it to the trigger:

```
CREATE OR REPLACE TRIGGER logs_trigger BEFORE INSERT OR UPDATE ON audit.logs
FOR EACH ROW EXECUTE FUNCTION audit.logs_trigger();
```

## 3. Finding the best location for the project

One of the first steps is to find a parcel on which to locate the photovoltaic plant. The requirements that these parcels must fill vary depending on the country and the project. In this guide we will assume that the plot must meet the following conditions:

1. Parcel must be larger then 50 ha.
2. Parcel cannot be located in a wet or protected area.
3. Parcel cannot have inside buildings or similar infrastructures.
4. Parcel must be situated close to an asphalted road ( < 500 m).
5. The nearest transformer must not be more than 250 metres away.
6. the nearest medium-voltage line must not be more than 500 metres away.

If we check the number of parcels in the Łowicz county, we see that there are 112526 available.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/number_of_parcels.png)

This calculation could be done from Qgis, but due to the high number of plots and constraints, we will do it from PostgreSQL and PostGIS.

In a new Query window in pgAdmin4, we will run the following script:

```
-- First we create a table with all areas where the parcel cannot be located

CREATE TABLE parcels.to_exclude AS (
SELECT(ST_Union(Array(SELECT geom FROM forests.ot_ptlz_a)))
UNION
SELECT(ST_Union(Array(SELECT geom FROM protected_areas.ot_tcon_a)))
UNION
SELECT(ST_Union(Array(SELECT geom FROM protected_areas.ot_tcpk_a)))
UNION
SELECT(ST_Union(Array(SELECT geom FROM protected_areas.ot_tcrz_a)))
UNION
SELECT(ST_Union(Array(SELECT geom FROM buildings.budynki_)))
UNION
SELECT(ST_Union(Array(SELECT geom FROM wet_areas.ot_oimk_a)))
UNION
SELECT(ST_Union(Array(SELECT geom FROM wet_areas.ot_ptwp_a)))
);

-- Then we have to find parcels that meet the requirements and are not in this new table "parcels_to_exclude".

CREATE TABLE parcels.accepted_parcels AS (

WITH sel AS (
SELECT par.gid
FROM parcels.dzialki_ AS par, parcels.to_exclude AS pte
WHERE ST_Intersects(pte.st_union,par.geom)
), to_trafo AS (

SELECT pa.gid
FROM parcels.dzialki_ AS pa, utility_poles.ot_buit_p AS tr
WHERE st_dwithin(pa.geom, tr.geom, 250::double precision)
), to_asphalt_road AS (

SELECT pa.gid
FROM parcels.dzialki_ AS pa, roads.ot_skjz_l AS ar
WHERE st_dwithin(pa.geom, ar.geom, 500::double precision)
), to_medium_voltage_line AS (

SELECT pa.gid
FROM parcels.dzialki_ AS pa, power_lines.ot_suln_l AS mvl
WHERE st_dwithin(pa.geom, mvl.geom, 500::double precision)
)

SELECT pa.gid, pa.id_dzialki, pa.area, pa.geom AS geometry
FROM parcels.dzialki_ AS pa
WHERE
pa.gid NOT IN (SELECT * FROM sel)
AND pa.gid IN (SELECT * FROM to_trafo)
AND pa.gid IN (SELECT * FROM to_asphalt_road)
AND pa.gid IN (SELECT * FROM to_medium_voltage_line)
AND pa.area > 50000
ORDER BY pa.area DESC
);
```

After running this script, we can see in Qgis the parcels accepted to develop the project:

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/parcels_accepted.png)

Let's check the number of parcels accepted:

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/query_accepted_parcels.png)


 ## 4. QGIS integration

Now that we have already decided the location of the project, it is time to start to work in the QGIS software in order to integrate with the database.

### 4.1. PostGIS connection

Each user must edit the connection to the database with the information supplied by the database administrator: host, port, databse, SSLmode, authentication (user name and password).

In the browser area, select PostgreSQL > oze > edit connection (with right button). The options "Also list tables with no geometries" and "Allow saving/loading QGIS projects in the database" must be selected.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/postgis_connection.png)

### 4.2. Attribute Forms

Attribute Forms are very useful when inserting new electrical devices in the QGIS canvas. In order to avoid errors when inserting new electrical devices, we will avoid the user having to type the name of the device, but we will facilitate the work by selecting from dropdowns.

#### 4.2.1. Electrical devices

Electrical devices are grouped by type or category, so that if a user selects the AC Circuit Breaker type, he will only be able to choose between the different models of AC Circuit Breaker in the Electrical device dropdown. And so on with the rest of type of devices.

| ![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_1.png) | ![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_2.png) |
| --- | --- |

In order to be able to carry out this conditional selection when inserting new electrical appliances, it is necessary that the tables corresponding to the electrical products ("_type\_of\_device_", "_devices_", "_wires_", etc.) are present in the QGIS canvas.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_3.png)

To achieve this we have to follow these steps:

- Layer properties \> Attributes Form \> Drag and drop designer

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_4.png)

- We can change each field of the attributes table. It is recommendable give an alias to the field. The most important is select "Value relation" in the Widget Type and choose the layer (in this example "_type\_of\_device_") where the key and value column will be taken from.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_5.png)

- Next step is set up the field in the attribute table where user will choose the electrical device. We have to get to include in the dropdown only those electrical devices belonging to the Type of device selected by the user in the previous dropdown. From the Widget Type area we will select again "Value relation", but the layer will be the table with all the electrical devices. We need to use a Filter expression to indicate QGIS that must remember the type of device selected by user.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_6.png)

- For the quantity and high fields we set an alias and as Widget Type "Range" starting from 1 for the quantity.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_7.png)

- The fields of the Coordinates X and Y, will be not editable, as they are automatically obtained thanks to the trigger function before explained.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_8.png)


#### 4.2.2. Electrical wiring

It is possible to represent the layout and the type of cable when wiring the photovoltaic solar plant, obtaining from the database all the materials and lengths needed.

As above explained, we want to make the designer's task easier and avoid errors. That's way the designer will no need to write codes or products names, just will select from a list of wires and select the number of units, and automatically the product code, description and length will be populated to the attribute table and database.

As example, in the following pictures, the user will choose only the wire and the number of units. The other fields are shown just as information to the user and will contribute to minimize errors and mistakes.

| ![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_9.png) | ![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_10.png) |
| --- | --- |

It is a little tricky to achieve this. We need to create a table with information about wires and some key columns ("_wireid_", "_nameid_", "_descriptionid_").

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/wires.png)

In the layer where we want to draw the wiring, we select Layer Properties > Attributes Form > Drag and Drop Designer.

In this window follow these steps:

1. Give an alias to the field.
2. Select "Value Relation" as the Widget Type.
3. Load the wires table in the Layer dropdown.
4. Select the "nameid" field in the Key column dropdown. This is the value saved in the database.
5. Select the "name" field in the Value column dropdown. This is the value shown to the user.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_11.png)

At his point the user will be able to select the most suitable wire. We want to show him the code and description of the wire the user chose.

We do the same with the next field "wirecode". The value column in the Value Relation Widget will be the not editable code to show the user, just to inform him what product he has chosen. The wireid must be filtered, in the Filter expression, to match the cable name the user has chosen.

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_12.png)

And we do the same for the "description" field:

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/attributes_form_13.png)

## 5.	Automated reports

Once the project is designed with the location and quantity of all electrical and non-electrical items, it is possible to obtain from the database a large amount of automated reports like BOM (Bill of materials).

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/project_layout_1.png)

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/project_layout_2.png)

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/project_layout_3.png)

 ### 5.1. Bill of materials

We create some views in the PostgreSQL database with the Bill Of Materials of the project, in order the Project Manager or any user has easy access at every stage of the project.


```
-- The full BOM of the wiring
CREATE OR REPLACE VIEW public.bom\_wiring AS

SELECT
wi.wirecode AS "Code",
wi.name AS "Wire",
pl.quantity AS "Quantity",
ROUND (pl.length::numeric, 2) AS "Length(m)",
wi.price AS "Unit price(€)",
ROUND((pl.quantity * pl.length * wi.price)::numeric, 2) AS "Total price(€)"
FROM power_lines.new_ot_suln_l pl
JOIN electrical_products.wires wi
ON pl.name::integer = wi.nameid
ORDER BY wi.wirecode;
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/bom_wiring.png)

```
-- The summarized BOM of the wiring

CREATE OR REPLACE VIEW public.summary_bom_wiring_v2 AS

SELECT wi.wirecode AS "Code",
wi.name AS "Wire",
sum(pl.quantity::numeric) AS "Quantity",
sum(ROUND (pl.length::numeric, 2)) AS "Total length(m)",
wi.price AS "Unit price(€)",
ROUND((SUM(pl.quantity::numeric) * sum(ROUND (pl.length::numeric, 2)) * wi.price::numeric)::numeric, 2) AS "Total price(€)"
FROM power_lines.new_ot_suln_l pl
JOIN electrical_products.wires wi
ON pl.name::integer = wi.nameid
GROUP BY wi.wirecode, wi.name, wi.price
ORDER BY wi.wirecode;
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/summary_bom_wiring.png)

```
-- The full BOM of the electrical and non-electrical devices

CREATE OR REPLACE VIEW public.bom_electrical_devices AS
SELECT
td.name AS "Type",
up.urzadzenie AS "Electrical device",
up.ilosc AS Quantity,
de.price AS "Unit price(€)",
up.ilosc * de.price AS "Total price(€)",
up.x AS "Coordinate X",
up.y AS "Coordinate Y"

FROM utility_poles.new_ot_buwt_p AS up

JOIN electrical_products.type_of_device AS td
ON up.rodzaj = td.typeid
JOIN electrical_products.devices AS de
ON up.urzadzenie = de.name

ORDER BY td.name;
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/bom_electrical_devices.png)

```
-- The summarized BOM of the electrical and non-electrical devices

CREATE OR REPLACE VIEW public.summary_bom_electrical_devices AS

SELECT td.name AS "Type",
up.urzadzenie AS "Electrical device",
sum(up.ilosc) AS quantity,
de.price AS "Unit price(€)",
ROUND(sum(up.ilosc::numeric * de.price)::numeric, 2) AS "Total price(€)"

FROM utility_poles.new_ot_buit_p up

JOIN electrical_products.type_of_device td ON up.rodzaj = td.typeid
JOIN electrical_products.devices de ON up.urzadzenie::text = de.name::text

GROUP BY td.name, up.urzadzenie, de.price
ORDER BY td.name;
```

![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/summary_bom_electrical_devices.png)

### 5.2. Logs table

From the logs table located in the schema audit, we can extract interesting reports for the Project Manager. Here are some basic examples:

| _All changes that Piotr has done between 6 __th_ _and 7__ th_ _September._ |
| --- |
| ![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/logs_resport_1.png) |

| _All features deleted between 6 __th_ _and 7__ th_ _September showing the Data type (point, linestring, polygon etc)_ |
| --- |
| ![](https://github.com/hroblesdiez/gis_system_in_renewable_energy_projects/blob/main/images/logs_resport_2.png) |




