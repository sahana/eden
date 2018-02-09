
ClimateDataPortal = local_import('ClimateDataPortal')

def clear_tables():
    ClimateDataPortal.place.truncate()
    ClimateDataPortal.rainfall_mm.truncate()
    ClimateDataPortal.temperature_celsius.truncate()
    db.commit()
#clear_tables()

def frange(start, end, inc=1.0):
    value = start
    i = 0
    while True:
        value = start + (i * inc)
        if value >= end:
            raise StopIteration
        else:
            yield value
            i += 1

def populate_test_climate_data():
    assert session.s3.debug == True
    db.commit()
    
    # create a grid of places
    place_id_grid = []
    
    # BBox coords for Nepal in degrees
    for latitude in frange(26.4, 30.5, 0.3):
        row = []
        for longitude in frange(80.0, 88.3, 0.3):
            place_id = ClimateDataPortal.place.insert(
                longitude = longitude,
                latitude = latitude
            )
            row.append(place_id)
        place_id_grid.append(row)

    # create a sequence of time periods.
    def to_date(month_number):
        return datetime.date(
            month_number / 12,
            (month_number % 12) + 1,
            1
        )
    time_period_ids = list(range(
        ClimateDataPortal.date_to_month_number(datetime.date(1960, 1, 1)),
        ClimateDataPortal.date_to_month_number(datetime.date(2011, 1, 1)),
    ))

    # observed samples
    # pick 100 random points from the place_id grid
    from random import randint
    observation_place_ids = set()
    for i in range(100):
        random_row = place_id_grid[
            randint(0,len(place_id_grid)-1)
        ]
        random_place = random_row[
            randint(0,len(random_row)-1)
        ]
        observation_place_ids.add(random_place)
    
    # generate samples for observed data
    for observation_place_id in observation_place_ids:
        for time_period_id in time_period_ids:
            ClimateDataPortal.rainfall_mm.insert(
                place_id = observation_place_id,
                time_period = time_period_id,
                sample_type = ClimateDataPortal.Observed,
                value = randint(50,150)
            )
            ClimateDataPortal.temperature_celsius.insert(
                place_id = observation_place_id,
                time_period = time_period_id,
                sample_type = ClimateDataPortal.Observed,
                value = randint(-30, 30)
            )
    db.commit()

#populate_test_climate_data()

map_plugin = ClimateDataPortal.MapPlugin(
    data_type_option_names = ['Observed','Gridded','Projected', 'RC Model', 'GC Model', 'Scenario'],
    parameter_type_names = ['Rainfall', 'Temperature', ],
    year_max = datetime.date.today().year,
    year_min = 1960,
)

"""
map_plugin.get_image_overlay(
    env = Storage(globals()),
    "Observed",
    parameter = "Rainfall",
    projected_option_type = '',
    from_date = datetime.date(2005, 1, 1),
    to_date = datetime.date(2010, 1, 1),
    statistic = 'average'
)
"""
