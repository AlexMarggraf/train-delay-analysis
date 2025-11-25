/*
Use this if you want to recreate the tables, WARNING: this will delete the entire schema

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
*/

CREATE TABLE WeatherStation (
	-- this would be an artificial key
	station_id SERIAL PRIMARY KEY,

	station_latitude DOUBLE PRECISION NOT NULL CHECK (station_latitude BETWEEN -90 AND 90),
	station_longitude DOUBLE PRECISION NOT NULL CHECK (station_longitude BETWEEN -180 AND 180),

	station_name VARCHAR(64),
	station_height REAL
);

CREATE TABLE SwissWeatherStation (
	station_id INT PRIMARY KEY REFERENCES WeatherStation(station_id),

	station_lvl95_north INT,
	station_lvl95_east INT,
	station_canton VARCHAR(8),

	station_exposition_de VARCHAR(64), -- I dont know what this is, so change this approprietly
	station_url VARCHAR(128),
	station_dataowner VARCHAR(64),
	station_wigos_id VARCHAR(64), -- Also not sure about this datatype

	station_type VARCHAR(64),
	station_barometer_height DOUBLE PRECISION,

	station_from DATE -- Why is there no end time?
);

CREATE TABLE GermanWeatherStation (
	station_id INT PRIMARY KEY REFERENCES WeatherStation(station_id),

	station_from TIMESTAMP,
	station_to TIMESTAMP
);

CREATE TABLE Parameter (
	-- this would be an artificial key
	parameter_id SERIAL PRIMARY KEY,

	parameter_abbr VARCHAR(8),
	parameter_description VARCHAR(256),
	parameter_unit VARCHAR(8) NOT NULL,
	parameter_type VARCHAR(8),

	-- I split up aggregation period
	parameter_from DATE,
	parameter_to DATE
);


CREATE TABLE Measurement (
	-- this would be an artificial key
	measurement_id SERIAL PRIMARY KEY,

	measurement_time TIMESTAMP NOT NULL,
	measurement_value DOUBLE PRECISION NOT NULL,

	measurement_station_id INT NOT NULL REFERENCES WeatherStation(station_id), -- (1,1) - (0,*)
	measurement_parameter_id INT NOT NULL REFERENCES Parameter(parameter_id) -- (1,1) - (0,*) Maybe this should be 1 to 1 in which case we would need to merge measurement and parameter
);

CREATE TABLE TrainStation (
	-- this is an artificial key
	station_id SERIAL PRIMARY KEY,
	
	station_name VARCHAR(32),
	station_weatherstation_id INT NOT NULL REFERENCES WeatherStation(station_id)
);

CREATE TABLE SwissTrainStation (
	station_id INT PRIMARY KEY REFERENCES TrainStation(station_id),

	station_day DATE,
	station_bpuic INT
);

CREATE TABLE Trainride (
	-- this is artificial
	trainride_id SERIAL PRIMARY KEY,

	trainride_type VARCHAR(8)
);

CREATE TABLE Stop (
	-- this key is artificial
	stop_id SERIAL PRIMARY KEY,

	stop_arrival_time TIMESTAMP NOT NULL,
	stop_departure_time TIMESTAMP NOT NULL,
	stop_planned_arrival_time TIMESTAMP NOT NULL,
	stop_planned_departure_time TIMESTAMP NOT NULL,

	stop_station_id INT NOT NULL REFERENCES TrainStation(station_id),
	stop_trainride_id INT NOT NULL REFERENCES Trainride(trainride_id)
);

CREATE TABLE GermanStop (
	stop_id INT PRIMARY KEY REFERENCES Stop(stop_id),

	stop_time TIMESTAMP,
	stop_is_canceled BOOL,
	stop_delay_in_min INT,
	stop_station_number INT
);

CREATE TABLE SwissStop (
	stop_id INT PRIMARY KEY REFERENCES Stop(stop_id),

	stop_arrival_prognosis VARCHAR(8),
	stop_departure_prognosis VARCHAR(8),
	stop_in_transit BOOL
);

CREATE TABLE Operator (
	-- this is an artificial key
	operator_id SERIAL PRIMARY KEY,

	operator_abbr VARCHAR(3), -- should be "DB" or "SBB" but double check that
	operator_name VARCHAR(32)
);

CREATE TABLE Line (
	-- this is an artificial key
	line_id SERIAL PRIMARY KEY,

	line_name VARCHAR(8),
	line_produkt_id VARCHAR(3), -- should always be "Zug" in my eyes but double check that
	line_operator_id INT REFERENCES Operator(operator_id)
);

CREATE TABLE SwissTrainride (
	trainride_id INT PRIMARY KEY REFERENCES Trainride(trainride_id),

	trainride_umlauf_id VARCHAR(16), -- i also dont know what this is
	trainride_fahrtbezeichner VARCHAR(19),
	trainride_canceled BOOL,
	trainride_edtraride BOOL,
	trainride_line_id INT REFERENCES Line(line_id)
);

CREATE TABLE GermanTrainride (
	trainride_id INT PRIMARY KEY REFERENCES Trainride(trainride_id),

	trainride_train_name VARCHAR(32),
	trainride_final_destination INT REFERENCES Trainstation(station_id)
);

