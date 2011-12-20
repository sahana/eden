
ClimateDataPortal = local_import("ClimateDataPortal")

from decimal import Decimal

def import_stations(file_name):
    """
    Expects a file containing lines of the form e.g.:
226     JALESORE             1122       172     26.65     85.78
275     PHIDIM (PANCHTH      1419      1205     27.15     87.75
unused  Station name         <-id    <-elev     <-lat     <-lon
0123456789012345678901234567890123456789012345678901234567890123456789
0         1         2         3         4         5         6
    """
    for line in open(file_name, "r").readlines():
        try:
            place_id_text = line[27:33]
        except IndexError:
            continue
        else:
            try:
                station_id = int(place_id_text)
            except ValueError:
                continue
            else:
                station_name = line[8:25].strip() # don't restrict if they add more
                elevation_metres = int(line[37:43])
                
                latitude = Decimal(line[47:53])
                longitude = Decimal(line[57:623])
                place_table_name = climate_place._tablename
                existing_place = db(
                    climate_station_id.station_id == station_id
                ).select().first()
                if existing_place is None:
                    place_id = climate_place.insert(
                        longitude = longitude,
                        latitude = latitude                
                    )
                else:
                    print "Update:"
                    place_id = existing_place.id                    
                    db(climate_place.id == place_id).update(
                        longitude = longitude,
                        latitude = latitude                
                    )
                
                def insert_or_update(
                    table,
                    place_id,
                    attribute,
                    format,
                    value
                ):
                    table_name = table._tablename
                    if db(table.id == place_id).count() == 0:
                        value = repr(value)
                        formatted_value = format(value)
                        db.executesql(
                            "INSERT INTO %(table_name)s "
                            "(id, %(attribute)s) "
                            "VALUES (%(place_id)i, %(formatted_value)s);" % locals()
                        )
                    else:
                        db(table.id == place_id).update(
                            **{attribute: value}
                        )
                
                insert_or_update(
                    climate_station_name,
                    place_id,
                    "name",
                    str,
                    station_name
                )
                insert_or_update(
                    climate_elevation,
                    place_id,
                    "elevation_metres",
                    float,
                    elevation_metres
                )
                insert_or_update(
                    climate_station_id,
                    place_id,
                    "station_id",
                    int,
                    station_id
                )
                                
                print place_id, station_id, station_name, latitude, longitude, elevation_metres 
    db.commit()

import sys
import_stations(sys.argv[1])
