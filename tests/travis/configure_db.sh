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

elif [[ $DB == postgres ]]; then
    echo "Setting up postgres"
    psql -c "create database sahana;" -U postgres
    sed -ie 's|\#settings.database.db_type = "postgres"|settings.database.db_type = "postgres"|' models/000_config.py
    sed -ie 's|\#settings.database.username = "sahana"|settings.database.username = "travis"|' models/000_config.py
    sed -ie 's|\#settings.database.database = "sahana"|settings.database.database = "sahana"|' models/000_config.py
    sed -ie 's|\#settings.database.password = "password"|settings.database.password = ""|' models/000_config.py
fi
