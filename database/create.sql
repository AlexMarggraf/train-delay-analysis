 /* -- WARNING: Drops everything — resets schema
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
*/

-- Swiss weather

CREATE TABLE SwissWeatherStation (
    station_abbr VARCHAR(8) PRIMARY KEY,

    station_name VARCHAR(128),
    station_canton VARCHAR(8),
    station_wigos_id VARCHAR(64),

    station_type_de VARCHAR(128),
    station_type_fr VARCHAR(128),
    station_type_it VARCHAR(128),
    station_type_en VARCHAR(128),

    station_data_owner VARCHAR(128),
    station_data_since DATE,

    station_height_masl DOUBLE PRECISION,
    station_height_barometer_masl DOUBLE PRECISION,

    station_lv95_east DOUBLE PRECISION,
    station_lv95_north DOUBLE PRECISION,

    station_latitude DOUBLE PRECISION,
    station_longitude DOUBLE PRECISION,

    station_exposure_de VARCHAR(128),
    station_exposure_fr VARCHAR(128),
    station_exposure_it VARCHAR(128),
    station_exposure_en VARCHAR(128),

    station_url_de VARCHAR(512),
    station_url_fr VARCHAR(512),
    station_url_it VARCHAR(512),
    station_url_en VARCHAR(512)
);

CREATE TABLE SwissWeatherMeasurement (
    station_abbr VARCHAR(8),
    reference_timestamp TIMESTAMP,

    temp_2m_mean DOUBLE PRECISION,
    temp_2m_min DOUBLE PRECISION,
    temp_2m_max DOUBLE PRECISION,
    temp_0_5m_mean DOUBLE PRECISION,
    temp_0_5m_min DOUBLE PRECISION,

    humidity_2m DOUBLE PRECISION,
    vapor_pressure_2m DOUBLE PRECISION,
    dewpoint_2m DOUBLE PRECISION,

    pressure_station DOUBLE PRECISION,
    pressure_qff DOUBLE PRECISION,
    pressure_qnh DOUBLE PRECISION,
    geopotential_700hpa DOUBLE PRECISION,
    geopotential_850hpa DOUBLE PRECISION,

    wind_speed_10m_mean DOUBLE PRECISION,
    wind_direction_10m DOUBLE PRECISION,
    wind_speed_10m_instant DOUBLE PRECISION,
    gust_10m DOUBLE PRECISION,
    gust_10m_max DOUBLE PRECISION,
    wind_speed_10m_3min DOUBLE PRECISION,
    gust_10m_3min DOUBLE PRECISION,

    cloud_cover DOUBLE PRECISION,
    sunshine_duration DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    global_radiation DOUBLE PRECISION,
    snow_height DOUBLE PRECISION,

    soil_temp_0cm DOUBLE PRECISION,
    soil_temp_5cm DOUBLE PRECISION,
    soil_temp_10cm DOUBLE PRECISION,
    soil_temp_20cm DOUBLE PRECISION,

    snow_water_equivalent DOUBLE PRECISION,
    evapotranspiration DOUBLE PRECISION,

    soil_temp_5cm_mean DOUBLE PRECISION,
    soil_temp_10cm_mean DOUBLE PRECISION,
    soil_temp_20cm_mean DOUBLE PRECISION,

    PRIMARY KEY (station_abbr, reference_timestamp)
);

-- German weather

CREATE TABLE GermanWeatherStation (
    station_id INTEGER PRIMARY KEY,
	
	station_height DOUBLE PRECISION,
    
    station_latitude DOUBLE PRECISION CHECK (station_latitude BETWEEN -90 AND 90),
    station_longitude DOUBLE PRECISION CHECK (station_longitude BETWEEN -180 AND 180),

    station_from DATE,
    station_until DATE,
	station_name VARCHAR(128)
);


CREATE TABLE GermanAirTemperature (
    station_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    qn_9 INTEGER,
    temperature_c DOUBLE PRECISION,
    humidity_rel DOUBLE PRECISION,
    eor VARCHAR(8),

    PRIMARY KEY (station_id, timestamp),
    FOREIGN KEY (station_id) REFERENCES GermanWeatherStation(station_id)
);

CREATE TABLE GermanPrecipitation (
    station_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    qn_8 INTEGER,
    precipitation_mm DOUBLE PRECISION,
    precipitation_T_or_F BOOLEAN,
    precipitation_type INTEGER,

    eor TEXT,

    PRIMARY KEY (station_id, timestamp),
    FOREIGN KEY (station_id) REFERENCES GermanWeatherStation(station_id)
);

CREATE TABLE GermanPressure (
    station_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    qn_8 INTEGER,
    pressure_calculated_oceanlevel  DOUBLE PRECISION,
    pressure DOUBLE PRECISION,

    eor TEXT,

    PRIMARY KEY (station_id, timestamp),
    FOREIGN KEY (station_id) REFERENCES GermanWeatherStation(station_id)
);

CREATE TABLE GermanWind (
    station_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    qn_3 INTEGER,
    wind_speed DOUBLE PRECISION,
    wind_direction_deg INTEGER,

    eor TEXT,

    PRIMARY KEY (station_id, timestamp),
    FOREIGN KEY (station_id) REFERENCES GermanWeatherStation(station_id)
);

-- Swiss Train

CREATE TABLE SwissTrainStations (
    station_name VARCHAR(128) PRIMARY KEY,
    bpuic INTEGER
);

CREATE TABLE SwissStop (

    station_name VARCHAR(128),
    arrival_time TIMESTAMP,
    departure_time TIMESTAMP,
    predicted_arrival TIMESTAMP,
    predicted_departure TIMESTAMP,
    arrival_prediction_status VARCHAR(32),
    departure_prediction_status VARCHAR(32),
    pass_through_flag BOOLEAN,
    line_id INTEGER,
    cancellation_flag BOOLEAN,
    extra_trip_flag BOOLEAN,
    stop_id INTEGER PRIMARY KEY,

    FOREIGN KEY (station_name) REFERENCES SwissTrainStations(station_name)
);

CREATE TABLE SwissLine (
    line_id INTEGER NOT NULL,
   
    line_text VARCHAR(32),
    product_id VARCHAR(32),
    circulation_id VARCHAR(64),
    vehicle_text VARCHAR(64),
    trip_identifier VARCHAR(128),
    operator_id VARCHAR(64),
	operating_day DATE NOT NULL,

    PRIMARY KEY (line_id, operating_day)
);

CREATE TABLE SwissOperator (
    operator_id VARCHAR(64) PRIMARY KEY,
    operator_abbreviation VARCHAR(64),
    operator_name VARCHAR(128)
);

-- German Train
CREATE TABLE GermanTrainStation (
    station_name VARCHAR(128),
    eva_id VARCHAR(16) PRIMARY KEY, --because it starts with 0 sometimes it cant be a int
    xml_station_name VARCHAR(128)
);

CREATE TABLE GermanTrainLine (
    train_line_ride_id BIGINT,
    final_destination_station VARCHAR(128),
    train_type VARCHAR(32),
    train_name VARCHAR(64),

    PRIMARY KEY (train_line_ride_id, final_destination_station)
);


CREATE TABLE GermanTrainStop (
    stop_id VARCHAR(64) PRIMARY KEY,

    eva VARCHAR(16) NOT NULL,
    train_line_ride_id BIGINT NOT NULL,

    arrival_planned_time TIMESTAMP,
    arrival_change_time TIMESTAMP,

    departure_planned_time TIMESTAMP,
    departure_change_time TIMESTAMP,

    delay_in_min INTEGER,
    time TIMESTAMP,

    is_canceled BOOLEAN,
    train_line_station_num INTEGER
);






