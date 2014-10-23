#!/bin/bash
echo "Configuring DB settings"

cd applications/eden

if [[ $DB == mysql ]]; then
    echo "Setting up mysql"
    mysql -e "create database sahana;"
    sed -ie 's|\#settings.database.db_type = "mysql"|settings.database.db_type = "mysql"|' models/000_config.py
    sed -ie 's|\#settings.database.username = "sahana"|settings.database.username = "travis"|' models/000_config.py
    sed -ie 's|\#settings.database.database = "sahana"|settings.database.database = "sahana"|' models/000_config.py
    sed -ie 's|\#settings.database.password = "password"|settings.database.password = ""|' models/000_config.py

elif [[ `echo $DB | cut -f1 -d"-"` == postgres ]]; then


    if [[ `echo $DB | cut -f1 -d"+"` == postgres-9.1 ]]; then
        echo "Setting up postgres version 9.1"
        sudo /etc/init.d/postgresql stop
        sudo /etc/init.d/postgresql start 9.1
        psql -c "create database sahana;" -U postgres


    else
        echo "Setting up postgres version 9.3"
        sudo /etc/init.d/postgresql stop
        sudo /etc/init.d/postgresql start 9.3
        psql -c "create database sahana;" -U postgres

        if [[ $DB == postgres-9.3+postgis ]]; then

            psql -U postgres -d sahana -c "create extension postgis"
            psql -U postgres -q -d sahana -c "grant all on geometry_columns to travis;"
            psql -U postgres -q -d sahana -c "grant all on spatial_ref_sys to travis;"

            sed -ie 's|\#settings.gis.spatialdb = True|settings.gis.spatialdb = True|' models/000_config.py

        fi

        echo "pg8000 (default web2py postgres adapter) does not support some postgres 9.3 features. Using psycopg2 instead."

        sudo pip install psycopg2 -q

    fi

    sed -ie 's|\#settings.database.db_type = "postgres"|settings.database.db_type = "postgres"|' models/000_config.py
    sed -ie 's|\#settings.database.username = "sahana"|settings.database.username = "travis"|' models/000_config.py
    sed -ie 's|\#settings.database.database = "sahana"|settings.database.database = "sahana"|' models/000_config.py
    sed -ie 's|\#settings.database.password = "password"|settings.database.password = ""|' models/000_config.py
fi
