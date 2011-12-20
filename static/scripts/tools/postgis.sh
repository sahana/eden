#!/bin/sh

#
# Link the gis_location table with PostGIS
# - designed to be run as postgres user
#
# sudo -H -u postgres sh postgis.sh
#
# http://eden.sahanafoundation.org/wiki/InstallationGuidelinesPostgreSQL#AddGeometrycolumntogis_location
#

# Add Geometry Column
cat << EOF > "/tmp/geometry.sql"
UPDATE public.gis_location SET wkt = 'POINT (' || lon || ' ' || lat || ')' WHERE gis_feature_type = 1;
SELECT AddGeometryColumn( 'public', 'gis_location', 'the_geom', 4326, 'GEOMETRY', 2 );
UPDATE public.gis_location SET the_geom = ST_SetSRID(ST_GeomFromText(wkt), 4326);
EOF
psql -q -d sahana -f /tmp/geometry.sql

# AutoPopulate
cat << EOF > "/tmp/autopopulate.sql"
CREATE OR REPLACE FUNCTION s3_update_geometry()
  RETURNS "trigger" AS \$$
  DECLARE
  BEGIN
    if (NEW.wkt != '') then
        NEW.the_geom = SetSRID(GeomFromText(NEW.wkt), 4326);
        end if;

    RETURN NEW;
  END;
\$$  LANGUAGE 'plpgsql' VOLATILE;
ALTER FUNCTION s3_update_geometry() OWNER TO sahana;
CREATE TRIGGER s3_locations_update
  BEFORE INSERT
  ON gis_location
  FOR EACH ROW
  EXECUTE PROCEDURE s3_update_geometry();

EOF
# Import Autopopulate
psql -q -d sahana -f /tmp/autopopulate.sql