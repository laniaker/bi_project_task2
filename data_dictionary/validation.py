from datetime import datetime
#wichtig eig zu vermerken wo der fehler auftritt welcxhe schema und zeilke 
def validate_yellow_trip(data):
    """
    Validiert Yellow Taxi Trip Records basierend auf den bereitgestellten Spaltennamen.
    """
    errors = []
    
    # VendorID: 1, 2, 6, 7 
    if data.get('VendorID') not in [1, 2, 6, 7]:
        errors.append(f"Ungültige VendorID: {data.get('VendorID')}")
    
    # Zeitstempel Logik
    pickup = data.get('tpep_pickup_datetime')
    dropoff = data.get('tpep_dropoff_datetime')
    if pickup and dropoff and pickup >= dropoff:
        errors.append("tpep_pickup_datetime muss vor tpep_dropoff_datetime liegen")
    
    # Passenger Count: 0 < count < 6 
    p_count = data.get('passenger_count', 0)
    if p_count is not None and not (0 < p_count < 6):
        errors.append(f"Ungültiger passenger_count: {p_count}")
        
    # Trip Distance: Positiv und plausibel 
    dist = data.get('trip_distance', 0)
    if dist is not None and (dist <= 0 or dist > 1000):
        errors.append(f"Trip_distance ungültig: {dist}")

    # RatecodeID: 1-6, 99 
    if data.get('RatecodeID') not in [1, 2, 3, 4, 5, 6, 99]:
        errors.append(f"Ungültige RatecodeID: {data.get('RatecodeID')}")

    # Store and Forward Flag: Y, N 
    if data.get('store_and_fwd_flag') not in ['Y', 'N']:
        errors.append("store_and_fwd_flag muss 'Y' oder 'N' sein")

    # Payment Type: 0-6 
    if data.get('payment_type') not in [0, 1, 2, 3, 4, 5, 6]:
        errors.append(f"Ungültige payment_type: {data.get('payment_type')}")

    # Finanzielle Werte: Nicht negativ 
    finance_fields = [
        'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount', 
        'improvement_surcharge', 'total_amount', 'congestion_surcharge', 'Airport_fee'
    ]
    for field in finance_fields:
        val = data.get(field)
        if val is not None and val < 0:
            errors.append(f"{field} darf nicht negativ sein")

    return len(errors) == 0, errors


def validate_green_trip(data):
    """
    Validiert Green Taxi (LPEP) Daten.
    """
    errors = []
    
    # VendorID: 1, 2, 6 
    if data.get('VendorID') not in [1, 2, 6]:
        errors.append(f"Ungültige VendorID: {data.get('VendorID')}")

    # Zeitstempel Logik
    pickup = data.get('lpep_pickup_datetime') 
    dropoff = data.get('lpep_dropoff_datetime')
    if pickup and dropoff and pickup >= dropoff:
        errors.append("lpep_pickup_datetime muss vor lpep_dropoff_datetime liegen")

    # RatecodeID & Payment Type 
    if data.get('RatecodeID') not in [1, 2, 3, 4, 5, 6, 99]:
        errors.append("Ungültige RatecodeID")
    if data.get('payment_type') not in [0, 1, 2, 3, 4, 5, 6]:
        errors.append("Ungültige payment_type")

    # Trip Type: 1=Street-hail, 2=Dispatch 
    if data.get('trip_type') not in [1, 2]:
        errors.append(f"Ungültiger trip_type: {data.get('trip_type')}")

    # Passenger & Distance
    if not (0 < data.get('passenger_count', 0) < 6):
        errors.append("Ungültiger passenger_count")
    if data.get('trip_distance', 0) <= 0 or data.get('trip_distance', 0) > 1000:
        errors.append("trip_distance ungültig")

    # Finanzielle Werte 
    finance_fields = [
        'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount', 
        'improvement_surcharge', 'total_amount', 'congestion_surcharge', 'ehail_fee'
    ]
    for field in finance_fields:
        val = data.get(field)
        if val is not None and val < 0:
            errors.append(f"{field} darf nicht negativ sein")

    return len(errors) == 0, errors


def validate_fhv_trip(data):
    """
    Validiert FHV Trip Records.
    """
    errors = []
    
    # Zeitstempel Logik 
    pickup = data.get('pickup_datetime')
    dropoff = data.get('dropOff_datetime')
    if pickup and dropoff and pickup >= dropoff:
        errors.append("pickup_datetime muss vor dropOff_datetime liegen")

    # SR_Flag: 1 (Shared) oder null 
    # Da Datentyp STRING: Prüfung auf "1" oder None
    sr_flag = data.get('SR_Flag')
    if sr_flag is not None and sr_flag != "1":
        errors.append("SR_Flag muss '1' oder null sein")

    # Pflichtfelder für IDs 
    mandatory = ['dispatching_base_num', 'PUlocationID', 'DOlocationID', 'Affiliated_base_number']
    for field in mandatory:
        if data.get(field) is None:
            errors.append(f"Pflichtfeld {field} fehlt")

    return len(errors) == 0, errors