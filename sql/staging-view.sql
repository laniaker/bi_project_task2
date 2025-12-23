-- 1. FHV UNIFIED VIEW
CREATE OR REPLACE VIEW `taxi-bi-project.staging.fhv_staging_unified` AS
SELECT
    dispatching_base_num,
    pickup_datetime,
    dropOff_datetime,
    CAST(PUlocationID AS INT64) AS PUlocationID, 
    CAST(DOlocationID AS INT64) AS DOlocationID, 
    CAST(SR_Flag AS STRING) AS SR_Flag,          
    Affiliated_base_number,
    -- Fügen Sie die neuen Audit-Flags hinzu, falls diese in den zugrundeliegenden Tabellen existieren:
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.fhv_schema_1` 
UNION ALL
SELECT
    dispatching_base_num,
    pickup_datetime,
    dropOff_datetime,
    CAST(PUlocationID AS INT64) AS PUlocationID,
    CAST(DOlocationID AS INT64) AS DOlocationID,
    CAST(SR_Flag AS STRING) AS SR_Flag, 
    Affiliated_base_number,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.fhv_schema_2`
UNION ALL
SELECT
    dispatching_base_num,
    pickup_datetime,
    dropOff_datetime,
    CAST(PUlocationID AS INT64) AS PUlocationID,
    CAST(DOlocationID AS INT64) AS DOlocationID,
    CAST(SR_Flag AS STRING) AS SR_Flag, 
    Affiliated_base_number,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.fhv_schema_3`
UNION ALL
SELECT
    dispatching_base_num,
    pickup_datetime,
    dropOff_datetime,
    CAST(PUlocationID AS INT64) AS PUlocationID,
    CAST(DOlocationID AS INT64) AS DOlocationID,
    CAST(SR_Flag AS STRING) AS SR_Flag, 
    Affiliated_base_number,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.fhv_schema_4`
UNION ALL
SELECT
    dispatching_base_num,
    pickup_datetime,
    dropOff_datetime,
    CAST(PUlocationID AS INT64) AS PUlocationID,
    CAST(DOlocationID AS INT64) AS DOlocationID,
    CAST(SR_Flag AS STRING) AS SR_Flag, 
    Affiliated_base_number,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.fhv_schema_5`;


-- 2. GREEN UNIFIED VIEW
CREATE OR REPLACE VIEW `taxi-bi-project.staging.green_staging_unified` AS
SELECT
    VendorID,
    lpep_pickup_datetime,
    lpep_dropoff_datetime,
    store_and_fwd_flag,
    CAST(RatecodeID AS INT64) AS RatecodeID,
    PULocationID,
    DOLocationID,
    CAST(passenger_count AS INT64) AS passenger_count,
    trip_distance,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    CAST(ehail_fee AS FLOAT64) AS ehail_fee, 
    improvement_surcharge,
    total_amount,
    CAST(payment_type AS INT64) AS payment_type,
    CAST(trip_type AS INT64) AS trip_type,    
    CAST(congestion_surcharge AS FLOAT64) AS congestion_surcharge,
    -- Fügen Sie die neuen Audit-Flags hinzu, falls diese in den zugrundeliegenden Tabellen existieren:
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.green_schema_1` 
UNION ALL
SELECT
    VendorID,
    lpep_pickup_datetime,
    lpep_dropoff_datetime,
    store_and_fwd_flag,
    CAST(RatecodeID AS INT64) AS RatecodeID,
    PULocationID,
    DOLocationID,
    CAST(passenger_count AS INT64) AS passenger_count,
    trip_distance,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    CAST(ehail_fee AS FLOAT64) AS ehail_fee,
    improvement_surcharge,
    total_amount,
    CAST(payment_type AS INT64) AS payment_type,
    CAST(trip_type AS INT64) AS trip_type,
    CAST(congestion_surcharge AS FLOAT64) AS congestion_surcharge,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.green_schema_2`
UNION ALL
-- ... (Fügen Sie hier alle weiteren 7 SELECT-Statements für green_schema_3 bis green_schema_9 ein, um die Konsistenz zu gewährleisten)
-- Beispiel für green_schema_9:
SELECT
    VendorID,
    lpep_pickup_datetime,
    lpep_dropoff_datetime,
    store_and_fwd_flag,
    CAST(RatecodeID AS INT64) AS RatecodeID,
    PULocationID,
    DOLocationID,
    CAST(passenger_count AS INT64) AS passenger_count,
    trip_distance,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    CAST(ehail_fee AS FLOAT64) AS ehail_fee,
    improvement_surcharge,
    total_amount,
    CAST(payment_type AS INT64) AS payment_type,
    CAST(trip_type AS INT64) AS trip_type,
    CAST(congestion_surcharge AS FLOAT64) AS congestion_surcharge,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.green_schema_9`;


-- 3. YELLOW UNIFIED VIEW
CREATE OR REPLACE VIEW `taxi-bi-project.staging.yellow_staging_unified` AS
SELECT
    CAST(VendorID AS INT64) AS VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    CAST(passenger_count AS INT64) AS passenger_count,
    trip_distance,
    CAST(RatecodeID AS INT64) AS RatecodeID,
    store_and_fwd_flag,
    CAST(PULocationID AS INT64) AS PULocationID,
    CAST(DOLocationID AS INT64) AS DOLocationID,
    CAST(payment_type AS INT64) AS payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    CAST(congestion_surcharge AS FLOAT64) AS congestion_surcharge,
    CAST(Airport_fee AS FLOAT64) AS Airport_fee,
    -- Fügen Sie die neuen Audit-Flags hinzu, falls diese in den zugrundeliegenden Tabellen existieren:
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.yellow_schema_1`
UNION ALL
SELECT
    CAST(VendorID AS INT64) AS VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    CAST(passenger_count AS INT64) AS passenger_count,
    trip_distance,
    CAST(RatecodeID AS INT64) AS RatecodeID,
    store_and_fwd_flag,
    CAST(PULocationID AS INT64) AS PULocationID,
    CAST(DOLocationID AS INT64) AS DOLocationID,
    CAST(payment_type AS INT64) AS payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    CAST(NULL AS FLOAT64) AS congestion_surcharge, 
    CAST(NULL AS FLOAT64) AS Airport_fee,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.yellow_schema_2`
UNION ALL
SELECT
    CAST(VendorID AS INT64) AS VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    CAST(passenger_count AS INT64) AS passenger_count,
    trip_distance,
    CAST(RatecodeID AS INT64) AS RatecodeID,
    store_and_fwd_flag,
    CAST(PULocationID AS INT64) AS PULocationID,
    CAST(DOLocationID AS INT64) AS DOLocationID,
    CAST(payment_type AS INT64) AS payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    CAST(congestion_surcharge AS FLOAT64) AS congestion_surcharge,
    CAST(NULL AS FLOAT64) AS Airport_fee, 
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.yellow_schema_3`
UNION ALL
-- ... (Fügen Sie alle weiteren SELECT-Statements für yellow_schema_4 bis yellow_schema_7 ein,
-- wobei Sie die Spaltennamen und CASTs von yellow_schema_5 (Koordinaten-Daten) wie von Ihnen angegeben beibehalten)
-- Beispiel für yellow_schema_7:
SELECT
    CAST(VendorID AS INT64) AS VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    CAST(passenger_count AS INT64) AS passenger_count,
    trip_distance,
    CAST(RatecodeID AS INT64) AS RatecodeID,
    store_and_fwd_flag,
    CAST(PULocationID AS INT64) AS PULocationID,
    CAST(DOLocationID AS INT64) AS DOLocationID,
    CAST(payment_type AS INT64) AS payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    CAST(congestion_surcharge AS FLOAT64) AS congestion_surcharge,
    CAST(Airport_fee AS FLOAT64) AS Airport_fee,
    duplicate_flag,
    missing_flag
FROM `taxi-bi-project.staging.yellow_schema_7`;