 /* -- WARNING: Drops everything — resets schema */
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Swiss weather

CREATE TABLE swiss_weatherstation (
    station_abbr VARCHAR(8) PRIMARY KEY,

    station_name VARCHAR(64),
    station_canton VARCHAR(8),
    station_wigos_id VARCHAR(32),

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

CREATE TABLE swiss_measurement (
    station_abbr VARCHAR(8) NOT NULL REFERENCES swiss_weatherstation(station_abbr),
    station_timestamp TIMESTAMP,

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

    PRIMARY KEY (station_abbr, station_timestamp)
);

-- German weather

CREATE TABLE german_weatherstation (
    station_id INTEGER PRIMARY KEY,
	
	station_height DOUBLE PRECISION,
    station_latitude DOUBLE PRECISION,
    station_longitude DOUBLE PRECISION,

	station_from DATE,
	station_until DATE,
	station_name VARCHAR(128)
);

CREATE TABLE german_temp (
    station_id INTEGER NOT NULL REFERENCES german_weatherstation(station_id),
    station_timestamp TIMESTAMP NOT NULL,

    qn_9 INTEGER,
    temperature_c DOUBLE PRECISION,
    humidity_rel DOUBLE PRECISION,
    eor VARCHAR(4),

    PRIMARY KEY (station_id, station_timestamp)
);

CREATE TABLE german_prec (
    station_id INTEGER NOT NULL REFERENCES german_weatherstation(station_id),
    station_timestamp TIMESTAMP NOT NULL,

    qn_8 INTEGER,
    precipitation_mm DOUBLE PRECISION,
    precipitation_T_or_F BOOLEAN,
    precipitation_type INTEGER,
    eor TEXT,

    PRIMARY KEY (station_id, station_timestamp)
);

CREATE TABLE german_pres (
    station_id INTEGER NOT NULL REFERENCES german_weatherstation(station_id),
    station_timestamp TIMESTAMP NOT NULL,

    qn_8 INTEGER,
    pressure_calculated_oceanlevel  DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    eor TEXT,

    PRIMARY KEY (station_id, station_timestamp)
);

CREATE TABLE german_wind (
    station_id INTEGER NOT NULL REFERENCES german_weatherstation(station_id),
    station_timestamp TIMESTAMP NOT NULL,

    qn_3 INTEGER,
    wind_speed DOUBLE PRECISION,
    wind_direction_deg INTEGER,
    eor TEXT,

    PRIMARY KEY (station_id, station_timestamp)
);

-- Swiss Train

CREATE TABLE swiss_trainstation (
	bpuic INTEGER PRIMARY KEY,
    station_name VARCHAR(128)
);

CREATE TABLE swiss_operator (
    operator_id VARCHAR(64) PRIMARY KEY,
    operator_abbreviation VARCHAR(64),
    operator_name VARCHAR(128)
);

CREATE TABLE swiss_trainline (
    line_id INTEGER NOT NULL,
    trip_identifier VARCHAR(64) NOT NULL,
	operating_day DATE NOT NULL,

	operator_id VARCHAR(16) NOT NULL REFERENCES swiss_operator(operator_id),
	
    line_text VARCHAR(8),
	vehicle_text VARCHAR(8),
    product_id VARCHAR(8),
    circulation_id VARCHAR(8),

    PRIMARY KEY (line_id, trip_identifier, operating_day)
);

CREATE TABLE swiss_trainstop (
	stop_id INTEGER PRIMARY KEY,
	bpuic INTEGER REFERENCES swiss_trainstation(bpuic),

	line_id INTEGER NOT NULL,
	trip_identifier VARCHAR(64) NOT NULL,
	operating_day DATE NOT NULL,
	
    arrival_time TIMESTAMP,
    departure_time TIMESTAMP,
    predicted_arrival TIMESTAMP,
    predicted_departure TIMESTAMP,
    arrival_prediction_status VARCHAR(16),
    departure_prediction_status VARCHAR(16),
	
    pass_through_flag BOOLEAN,
    cancellation_flag BOOLEAN,
    extra_trip_flag BOOLEAN,
	
	FOREIGN KEY (line_id, trip_identifier, operating_day)
		REFERENCES swiss_trainline(line_id, trip_identifier, operating_day)
);

-- German Train
CREATE TABLE german_trainstation (
	eva VARCHAR(8) PRIMARY KEY, --because it starts with 0 sometimes it cant be a int
    station_name VARCHAR(64),
    xml_station_name VARCHAR(64)
);

CREATE TABLE german_trainline (
    train_line_ride_id BIGINT,
    final_destination_station VARCHAR(64),
    train_name VARCHAR(16),

	train_type VARCHAR(16),

    PRIMARY KEY (train_line_ride_id, final_destination_station, train_name)
);


CREATE TABLE german_trainstop (
    stop_id VARCHAR(64) PRIMARY KEY,

    eva VARCHAR(8) NOT NULL REFERENCES german_trainstation(eva),
	
    train_line_ride_id BIGINT NOT NULL,
	final_destination_station VARCHAR(64) NOT NULL,
	train_name VARCHAR(16) NOT NULL,

    arrival_change_time TIMESTAMP,
	departure_change_time TIMESTAMP,
	arrival_planned_time TIMESTAMP,
    departure_planned_time TIMESTAMP,

    delay_in_min INTEGER,
    train_time TIMESTAMP,

    is_canceled BOOLEAN,
    train_line_station_num INTEGER,

	FOREIGN KEY (train_line_ride_id, final_destination_station, train_name)
		REFERENCES german_trainline(train_line_ride_id, final_destination_station, train_name)
);

-- Look Up

CREATE TABLE trainstation_weatherstation(
	trainstation VARCHAR(8) PRIMARY KEY,
	trainstation_in_ch BOOLEAN,
	weatherstation VARCHAR(8),
	weatherstation_in_ch BOOLEAN
);

--- Index structures

CREATE INDEX idx_swiss_measurement ON swiss_measurement(station_abbr, station_timestamp);

CREATE INDEX idx_german_temp ON german_temp(station_id, station_timestamp);
CREATE INDEX idx_german_prec ON german_prec(station_id, station_timestamp);
CREATE INDEX idx_german_pres ON german_pres(station_id, station_timestamp);
CREATE INDEX idx_german_wind ON german_wind(station_id, station_timestamp);

CREATE INDEX idx_swiss_stop ON swiss_trainstop(bpuic);
CREATE INDEX idx_swiss_line ON swiss_trainstop(line_id, trip_identifier, operating_day);
CREATE INDEX idx_swiss_day ON swiss_trainstop(operating_day);

CREATE INDEX idx_german_stop ON german_trainstop(eva);
CREATE INDEX idx_german_line ON german_trainstop(train_line_ride_id, final_destination_station, train_name);
CREATE INDEX idx_german_day ON german_trainstop(arrival_change_time);



