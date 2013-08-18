---
--- PostgreSQL stored procedures to support meteorflux.
---

---
--- Date/time helper functions.
---

CREATE OR REPLACE FUNCTION jd_decimal(timestamp without time zone) RETURNS float
LANGUAGE sql IMMUTABLE
AS $_$;
SELECT CAST(TO_CHAR(($1 - '12:00:00'::interval), 'J') AS float)
           + ( CAST(TO_CHAR(($1 - '12:00:00'::interval), 'SSSS') AS float) / 86400.0 );
$_$;


CREATE OR REPLACE FUNCTION solarlon(timestamp without time zone) RETURNS float
LANGUAGE plpgsql IMMUTABLE
AS $_$
DECLARE
    jd float;
    TWOPI float := 2.0 * PI();
    T float;
    result float;
    -- If you wonder about these numbers, see "Astronomical Algorithms" (Jean Meeus) pp 205
    a0 float[] = '{334166.0, 3489.0, 350.0, 342.0, 314.0, 268.0, 234.0, 132.0, 127.0, 120.0, 99.0, 90.0, 86.0, 78.0, 75.0, 51.0, 49.0, 36.0, 32.0, 28.0, 27.0, 24.0, 21.0, 21.0, 20.0, 16.0, 13.0, 13.0}';
    b0 float[] = '{4.669257, 4.6261, 2.744, 2.829, 3.628, 4.418, 6.135, 0.742, 2.037, 1.11, 5.233, 2.045, 3.508, 1.179, 2.533, 4.58, 4.21, 2.92, 5.85, 1.90, 0.31, 0.34, 4.81, 1.87, 2.46, 0.83, 3.41, 1.08}';
    c0 float[] = '{6283.07585, 12566.1517, 5753.385, 3.523, 77713.771, 7860.419, 3930.210, 11506.77, 529.691, 1577.344, 5884.927, 26.298, 398.149, 5223.694, 5507.553, 18849.23, 775.52, 0.07, 11790.63, 796.30, 10977.08, 5486.78, 2544.31, 5573.14, 6069.78, 213.30, 2942.46, 20.78}';
    a1 float[] = '{20606.0, 430.0, 43.0}';
    b1 float[] = '{2.67823, 2.635, 1.59}';
    s0 float := 0;
    s1 float := 0;
    s2 float := 0;
    s3 float := 0;
    angle float;
    angle1 float;

BEGIN
    jd := jd_decimal($1);  
    T := (jd - 2451545) / 365250.0;
    result := 4.8950627 + T * (6283.0758500 - T * 0.0000099);
    
    -- Calculate s0
    FOR n IN 1..28 LOOP
        angle := b0[n] + c0[n] * T;
        s0 := s0 + a0[n] * cos(angle);
    END LOOP;

    -- Calculate s1
    FOR n IN 1..3 LOOP
      angle := b1[n] + c0[n] * T;
      s1 := s1 + a1[n] * cos(angle);
    END LOOP;

    -- Calculate s2
    angle := 1.073 + c0[1] * T;
    angle1 := 0.44 + c0[2] * T;
    s2 := 872.0 * cos(angle) + 29 * cos(angle1);
    
    -- Calculate s3
    angle := 5.84 + c0[1] * T;
    s3 := 29.0 * cos(angle);
    
    -- The required longitude in radians is given by:
    result := result + ( s0 + T * ( s1 + T * ( s2 + T * s3 ) ) ) * 1e-7;
    
    -- Normalize the angle
    WHILE result > TWOPI LOOP
        result := result - TWOPI;
    END LOOP;
    WHILE result < 0 LOOP
        result := result + TWOPI;
    END LOOP;
    
    -- Return the result (DEGREES!)
    RETURN DEGREES(result);
END;
$_$;



-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

---
--- FLUX BINNING
---


DROP TYPE IF EXISTS fluxbin CASCADE;
CREATE TYPE fluxbin AS (
    "time" timestamp without time zone,
    solarlon float,
    teff float,
    eca float,
    met integer,
    flux float,
    e_flux float,
    zhr float,
    reports integer
);


CREATE OR REPLACE FUNCTION flux2zhr(float, float) RETURNS float
LANGUAGE sql
AS $_$;
-- Parameters: flux, popindex
-- Eqn 41 from (Koschak 1990b)
SELECT ($1 * 37.200) / ( (13.1*$2 - 16.45) * ($2 - 1.3)^0.748 );
$_$;


---
--- "Classical binning"
----

CREATE OR REPLACE FUNCTION bin_adaptive(text,
            timestamp without time zone, timestamp without time zone, 
            integer, float, interval, interval, 
            float, float, float, float) RETURNS SETOF fluxbin
LANGUAGE plpgsql
AS $_$DECLARE
    myshower ALIAS FOR $1;
    start ALIAS FOR $2;
    stop ALIAS FOR $3;
    min_meteors ALIAS FOR $4;
    min_eca ALIAS FOR $5;
    min_interval ALIAS FOR $6;
    max_interval ALIAS FOR $7;
    min_alt_station ALIAS FOR $8;
    min_eca_station ALIAS FOR $9;
    gamma ALIAS FOR $10;
    popindex ALIAS FOR $11;
    myperiod RECORD;
    total_teff float := 0;
    total_eca float := 0;
    total_met integer := 0;
    total_reports integer := 0;
    total_offset interval := 0;
    firstPeriod boolean := true;
    intervalstart timestamp without time zone;
    interval fluxbin;
BEGIN
    -- Query 1-minute flux bins
    FOR myperiod IN (   
        SELECT
            time,
            SUM(teff) AS teff,
            SUM(eca * (SIN(RADIANS(alt))^gamma) / SIN(RADIANS(alt)) ) AS eca,
            SUM(met) As met,
            COUNT(*) AS reports
        FROM flux
        WHERE 
            shower = myshower
            AND time BETWEEN start AND stop
            AND eca IS NOT NULL
            AND eca > min_eca_station
            AND alt > min_alt_station
        GROUP BY time
        ORDER BY time) LOOP
                
        -- Return flux if meteor/eca/timespan thresholds have been reached
        IF ( ( total_met >= min_meteors 
               OR total_eca >= min_eca 
               OR (myperiod.time - intervalstart) >= max_interval
              )
              AND (myperiod.time - intervalstart) >= min_interval) THEN

            -- Prepare values to return
            interval.time := intervalstart + (total_offset / total_eca);
            interval.solarlon := solarlon(interval.time);
            interval.teff := total_teff / 60.0; -- hours
            interval.eca := total_eca / 1000.0; -- 10^3 km^2 h
            interval.met := total_met;
            interval.flux := 1000.0 * (total_met+0.5) / total_eca; -- 10^-3 km^-2 h^-1
            interval.e_flux := 1000.0 * sqrt(total_met+0.5) / total_eca;
            interval.zhr := flux2zhr(interval.flux, popindex);
            interval.reports := total_reports;

            -- Reset vars
            total_eca := 0;
            total_teff := 0;
            total_met := 0;
            total_reports := 0;
            total_offset := 0;
            firstPeriod := true;

            -- Actual row return
            RETURN NEXT interval;
        END IF;
        
        IF firstPeriod THEN
            intervalstart := myperiod.time;
            firstPeriod := false;
        END IF;

        total_teff := total_teff + myperiod.teff;
        total_eca := total_eca + myperiod.eca;
        total_met := total_met + myperiod.met;
        total_reports := total_reports + myperiod.reports;
        -- make sum of offsets from the first myperiod.mid to average all myperiod.mid's later on   
        total_offset := total_offset + myperiod.eca * (myperiod.time - intervalstart); 

    END LOOP;

    -- Last interval
    --IF (total_met > 0.7*min_meteors) OR (total_eca > 0.7*min_eca) THEN
    --        interval.time := intervalstart + (total_offset / total_eca);
    --        interval.solarlon := solarlon(interval.time);
    --        interval.teff := total_teff / 60.0; -- hours
    --        interval.eca := total_eca / 1000.0; -- 10^3 km^2 h
    --        interval.met := total_met;
    --        interval.flux := 1000.0 * (total_met+0.5) / total_eca; -- 10^-3 km^-2 h^-1
    --        interval.e_flux := 1000.0 * sqrt(total_met+0.5) / total_eca;
    --        interval.zhr := flux2zhr(interval.flux, popindex);
    --        interval.reports := total_reports;
    --    RETURN NEXT interval;
    --END IF;

    RETURN;
END;
$_$;


-- Example:
-- SELECT * FROM bin_adaptive('PER', '2012-08-01'::timestamp, '2012-08-03'::timestamp, 100, 9000, '30 min'::interval, '3 hour'::interval, 0, 1.0)



---
--- Binning by solar longitude
----

CREATE OR REPLACE FUNCTION bin_sollon(myshower text,
                                      start float,
                                      stop float,
                                      years int[] DEFAULT '{2012}',
                                      min_meteors integer DEFAULT 25,
                                      min_eca float DEFAULT 25000.0,
                                      min_interval float DEFAULT 1.0,
                                      max_interval float DEFAULT 24.0,
                                      min_alt_station float DEFAULT 10,
                                      min_eca_station float DEFAULT 0.5,
                                      gamma float DEFAULT 1.5,
                                      popindex float DEFAULT 2.0) RETURNS SETOF fluxbin
LANGUAGE plpgsql
AS $_$DECLARE
    myperiod RECORD;
    total_teff float := 0;
    total_eca float := 0;
    total_met integer := 0;
    total_reports integer := 0;
    total_offset float := 0;
    firstPeriod boolean := true;
    intervalstart float;
    interval fluxbin;
BEGIN
    -- Query 1-minute flux bins
    FOR myperiod IN (   
        SELECT
            sollong,
            SUM(teff) AS teff,
            SUM(eca * (SIN(RADIANS(alt))^gamma) / SIN(RADIANS(alt)) ) AS eca,
            SUM(met) As met,
            COUNT(*) AS reports
        FROM flux
        WHERE 
            shower = myshower
            AND sollong BETWEEN start AND stop
            AND date_part('year', "time") = ANY(years)
            AND eca IS NOT NULL
            AND eca > min_eca_station
            AND alt > min_alt_station
        GROUP BY sollong
        ORDER BY sollong) LOOP

        -- Return flux if meteor/eca/timespan thresholds have been reached
        IF ( ( total_met >= min_meteors 
               OR total_eca >= min_eca 
               OR (myperiod.sollong - intervalstart) >= max_interval/24.0
              )
              AND (myperiod.sollong - intervalstart) >= min_interval/24.0) THEN

            -- Prepare values to return
            interval.solarlon := intervalstart + (total_offset / total_eca);
            interval.teff := total_teff / 60.0; -- hours
            interval.eca := total_eca / 1000.0; -- 10^3 km^2 h
            interval.met := total_met;
            interval.flux := 1000.0 * (total_met+0.5) / total_eca; -- 10^-3 km^-2 h^-1
            interval.e_flux := 1000.0 * sqrt(total_met+0.5) / total_eca;
            interval.zhr := flux2zhr(interval.flux, popindex);
            interval.reports := total_reports;

            -- Reset vars
            total_eca := 0;
            total_teff := 0;
            total_met := 0;
            total_reports := 0;
            total_offset := 0;
            firstPeriod := true;

            -- Actual row return
            RETURN NEXT interval;
        END IF;
        
        IF firstPeriod THEN
            intervalstart := myperiod.sollong;
            firstPeriod := false;
        END IF;

        total_teff := total_teff + myperiod.teff;
        total_eca := total_eca + myperiod.eca;
        total_met := total_met + myperiod.met;
        total_reports := total_reports + myperiod.reports;
        -- make sum of offsets from the first myperiod.mid to average all myperiod.mid's later on   
        total_offset := total_offset + myperiod.eca * (myperiod.sollong - intervalstart); 

    END LOOP;
    RETURN;
END;
$_$;


-- Example:
-- SELECT * FROM bin_sollon('PER', 120.0, 130.0)
