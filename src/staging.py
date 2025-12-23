import json
import pandas as pd
from google.cloud import bigquery
from google.cloud import storage
from datetime import datetime, timezone
import time
import os

# --- KONSTANTEN ---
PROJECTID = "taxi-bi-project" 
DATASET = "staging"
BUCKET_NAME = "taxi-raw-bucket"
RAW_PREFIX = "raw/"
SCHEMAJSONFILES = [
    "schemes/schemas_with_filenames_fhv.json",
    "schemes/schemas_with_filenames_greentaxi.json",
    "schemes/schemas_with_filenames_yellowtaxi.json"
]
LOGTABLE = "log_table_audit"

PROCESSOR_NAME = "ed033" 

# Die spezifischen GCS-Ordner, die verarbeitet werden sollen
TARGET_GCS_PREFIXES = [
    "raw/FHV_Data_2015-2025_all/",
    "raw/Green_Taxi_Trip_Data_2015-2025_all/",
    "raw/Yellow_Taxi_Trip_Data_2023/",
    "raw/Yellow_Taxi_Trip_Data_June_2010-2025/"
]

print("START ETL - Lokale Ausführung (DUAL FLAGS IMPLEMENTIERT)")
print(f"Schema-Dateien: {SCHEMAJSONFILES}")

# Initialisierung der Clients
try:
    storage_client = storage.Client(project=PROJECTID)
    bqclient = bigquery.Client(project=PROJECTID)
    print("Google Cloud Clients erfolgreich initialisiert.")
except Exception as e:
    print(f"FEHLER bei der Initialisierung der Google Cloud Clients: {e}")
    print("Stellen Sie sicher, dass die Google Cloud CLI installiert und 'gcloud auth application-default login' ausgeführt wurde.")
    exit(1)


# --- AUDIT-TABELLEN-GARANTIE ---

def ensure_audit_tables_exist(client):
    """Stellt sicher, dass die log_table_audit Tabelle existiert."""
    print("\nINFO: Überprüfe/Erstelle kritische Audit-Tabelle log_table_audit...")

    log_schema = [
        bigquery.SchemaField("table_name", "STRING"), bigquery.SchemaField("file_name", "STRING"),
        bigquery.SchemaField("row_count", "INT64"), bigquery.SchemaField("column_count", "INT64"),
        bigquery.SchemaField("duplicate_count", "INT64"), bigquery.SchemaField("processed_at", "TIMESTAMP"),
        bigquery.SchemaField("opened_at", "TIMESTAMP"), bigquery.SchemaField("processed_by", "STRING"),
        bigquery.SchemaField("status", "STRING"), bigquery.SchemaField("additional_info", "STRING")
    ]
    
    full_log_table = f"{PROJECTID}.{DATASET}.{LOGTABLE}"
    try:
        client.get_table(full_log_table)
    except:
        table = bigquery.Table(full_log_table, schema=log_schema)
        client.create_table(table)
        print(f"INFO: Tabelle {LOGTABLE} wurde neu erstellt.")
        time.sleep(5) 
        print("INFO: 5 Sekunden gewartet, um BigQuery-Status-Update zu ermöglichen.")

    print("INFO: Audit-Tabelle ist vorhanden.")

# --- AUDIT-STATUS ABFRAGEN ---

def get_processed_files(client):
    """Fragt die log_table_audit ab, um alle erfolgreich verarbeiteten Dateinamen zu erhalten."""
    query = f"""
    SELECT DISTINCT file_name
    FROM `{PROJECTID}.{DATASET}.{LOGTABLE}`
    WHERE status = 'success'
    """
    
    try:
        query_job = client.query(query)
        processed_files = {row.file_name for row in query_job}
        print(f"INFO: {len(processed_files)} Dateien wurden laut Audit-Log als erfolgreich verarbeitet erkannt.")
        return processed_files
    except Exception as e:
        print(f"WARNUNG: Konnte Audit-Log nicht abfragen (Tabellenstatus oder Fehler). Starte mit leerer Liste: {e}")
        return set()


# --- HILFSFUNKTIONEN  ---

def loadschemamappingjsonfile(jsonfile):
    """Lädt das Schema-Mapping aus einer JSON-Datei im GCS-Bucket und erstellt ein Dateiname->Schema-Mapping."""
    print(f"INFO: Lade Mapping aus gs://{BUCKET_NAME}/{jsonfile}")
    
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(jsonfile)
    
    try:
        json_bytes = blob.download_as_bytes()
        schemas = json.loads(json_bytes.decode('utf-8'))
    except Exception as e:
        print(f"FEHLER: Konnte JSON-Schema-Datei {jsonfile} nicht laden. {e}")
        return {}

    mapping = {}
    for schemaentry in schemas:
        for key in schemaentry:
            if key.lower().startswith("schema"): 
                files = schemaentry["files"]
                mapping.update({file.split("/")[-1]: key for file in files})

    print(f"DEBUG: Geladenes Mapping aus {jsonfile} hat {len(mapping)} Einträge.")
    return mapping

def list_gcs_parquet_files(bucket_name, prefix):
    """Listet alle Parquet-Dateien in einem GCS-Bucket-Ordnerbaum rekursiv auf."""
    print(f"INFO: Suche Parquet-Dateien in gs://{bucket_name}/{prefix}...")
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    return [blob.name for blob in blobs if blob.name.endswith('.parquet')]


def insert_log_job(client, row):
    """Fügt eine Log-Zeile als Load Job (Batch-Insert) ein."""
    df_log = pd.DataFrame([row])
    
    df_log["processed_at"] = pd.to_datetime(df_log["processed_at"]).dt.tz_localize(None) 
    df_log["opened_at"] = pd.to_datetime(df_log["opened_at"]).dt.tz_localize(None)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    
    full_log_table = f"{PROJECTID}.{DATASET}.{LOGTABLE}"
    
    job = client.load_table_from_dataframe(
        df_log,
        full_log_table,
        job_config=job_config
    )
    job.result()


def processfile(bqclient, mapping, filename, gcs_path):
    """Verarbeitet eine einzelne Parquet-Datei: Lädt, prüft Duplikate, setzt DUPLICATE_FLAG und MISSING_FLAG, lädt in BigQuery, loggt."""
    print(f"\n--- Starte Verarbeitung der Datei: {gcs_path} ---")
    
    current_time_utc = datetime.now(timezone.utc)
    start_time = time.time()

    log_row = {
        "table_name": None,
        "file_name": filename,
        "row_count": None,
        "column_count": None,
        "duplicate_count": None,
        "processed_at": current_time_utc.isoformat(),
        "opened_at": current_time_utc.isoformat(),
        "processed_by": PROCESSOR_NAME, 
        "status": "running",
        "additional_info": "" # Initialisierung für Warnungen/Fehler
    }
    
    tablename = None
    schemacategory = mapping.get(filename) 
    
    # 1. PRÜFUNG: Schema-Mapping
    if not schemacategory:
        log_row["status"] = "quarantine"
        log_row["additional_info"] = "CRITICAL: No schema mapping found for file. File completely quarantined."
        
        try:
            insert_log_job(bqclient, log_row) 
        except Exception as log_e:
            print(f"KRITISCHER FEHLER beim Logging des Quarantäne-Status: {str(log_e)}")
            raise
            
        print(f"KEIN SCHEMA: Keine Schemazuordnung für Datei {filename}. Log in Quarantäne-Status.")
        return tablename

    try:
        # 2. PARQUET LADEN
        start_load = time.time()
        gcs_uri = f"gs://{BUCKET_NAME}/{gcs_path}"
        
        df = pd.read_parquet(gcs_uri)
        load_duration = time.time() - start_load 
        
        initial_row_count = len(df)
        log_row["row_count"] = initial_row_count
        log_row["column_count"] = len(df.columns)
        
        print(f"INFO: Parquet-Laden abgeschlossen. Dauer: {load_duration:.2f}s. Rows: {initial_row_count}.")
        
        # 2b. BESTIMME KRITISCHE SPALTEN FÜR NULL CHECK
        if filename.startswith('fhv_'):
            source_prefix = 'fhv'
            CRITICAL_NULL_COLS = ['PULocationID', 'DOLocationID', 'Affiliated_base_number', 'SR_Flag', 'dispatching_base_num', 'pickup_datetime', 'dropOff_datetime'] 
        elif filename.startswith('green_'):
            source_prefix = 'green'
            CRITICAL_NULL_COLS = ['lpep_pickup_datetime', 'lpep_dropoff_datetime', 'VendorID']
        elif filename.startswith('yellow_'):
            source_prefix = 'yellow'
            CRITICAL_NULL_COLS = ['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'VendorID']
        else:
            CRITICAL_NULL_COLS = [] 
            raise ValueError(f"Unbekanntes Quelldateiformat für {filename}") 

        tablename = f"{source_prefix}_{schemacategory.replace('-', '_').lower()}" 
        log_row["table_name"] = tablename
        
        # Finde kritische Spalten, die tatsächlich im DataFrame existieren
        existing_critical_cols = [col for col in CRITICAL_NULL_COLS if col in df.columns]

        # 3. DUAL FLAG LOGIK
        
        start_check = time.time()
        
        # 3a. Duplikat-Erkennung (Exakte Zeilenduplikate)
        is_duplicated = df.duplicated()
        dupcount = is_duplicated.sum()
        log_row["duplicate_count"] = int(dupcount)
        
        # Setze duplicate_flag
        df['duplicate_flag'] = is_duplicated.map({True: 'Y', False: 'N'})
        
        # 3b. Fehlende Werte Erkennung (Gezielte Prüfung auf kritische Spalten)
        missing_critical_count = 0
        missing_mask = pd.Series([False] * len(df), index=df.index)
        quarantine_reasons = [] # Wird nun für die Log-Tabelle verwendet
        
        if not existing_critical_cols:
             # Protokolliere, falls kritische Spalten fehlen (WARNUNG)
             log_row["additional_info"] += f"WARNING: Critical columns for null check are missing or missing from data: {CRITICAL_NULL_COLS}. Null check skipped. | "
             
        elif existing_critical_cols:
            
            # Startmaske: Echte Pandas-Nullwerte
            missing_mask = df[existing_critical_cols].isnull().any(axis=1)
            
            # Überprüfung auf leere Strings (häufig bei Parquet/String-Spalten)
            for col in existing_critical_cols:
                if df[col].dtype == 'object':
                    try:
                        is_empty_string = (df[col] == '')
                        missing_mask = missing_mask | is_empty_string
                    except TypeError:
                        print(f"WARNUNG: Spalte {col} hat gemischte Typen, Prüfung auf leeren String ('') übersprungen.")

            missing_critical_count = missing_mask.sum()
            
            if missing_critical_count > 0:
                quarantine_reasons.append(f"Missing Critical Data ({'/'.join(existing_critical_cols)}): {missing_critical_count}")
        
        # Setze missing_flag
        df['missing_flag'] = missing_mask.map({True: 'Y', False: 'N'})

        # Gesamtanzahl der fehlerhaften Zeilen (entweder Missing ODER Duplicate) für das Logging
        total_quarantined = is_duplicated.sum() + missing_mask.sum() - (is_duplicated & missing_mask).sum()
        
        check_duration = time.time() - start_check 
        

        # 4. HAUPT-LADEN IN BIGQUERY (Staging Layer)
        start_bq_load = time.time()
        fulltable = f"{PROJECTID}.{DATASET}.{tablename}"
        
        job = bqclient.load_table_from_dataframe(df, fulltable)
        job.result()  
        bq_load_duration = time.time() - start_bq_load
        print(f"INFO: BigQuery Lade-Job abgeschlossen. Dauer: {bq_load_duration:.2f}s.")
        
        # 5. KRITISCHES LOGGING: Erfolg
        log_row["status"] = "success"
        
        # Aufbau der Timing-Metriken
        timing_info = (
            f"Total ETL Time: {time.time() - start_time:.2f}s | "
            f"Parquet Load Time: {load_duration:.2f}s | "
            f"Validation Time: {check_duration:.2f}s | "
            f"BQ Load Time: {bq_load_duration:.2f}s"
        )
        
        # Aufbau der Quarantäne-Metriken
        quarantine_rate = (total_quarantined / initial_row_count) * 100 if initial_row_count > 0 else 0
        if total_quarantined > 0:
            reason_info = f"Duplicates: {dupcount} | " + " | ".join(quarantine_reasons)
            quarantine_info = f"Quarantine: {total_quarantined} unique rows flagged ({quarantine_rate:.2f}%). Reasons: {reason_info}"
        else:
            quarantine_info = "Quarantine: No issues found."

        # Kombiniere Timing und Quarantäne und hänge es an eventuelle Warnings an
        log_row["additional_info"] = log_row["additional_info"] + f"{timing_info} | {quarantine_info}"

        insert_log_job(bqclient, log_row)
        
    except Exception as e:
        # 6. KRITISCHES LOGGING: Fehler
        log_row["status"] = "fail"
        log_row["additional_info"] = f"CRITICAL ETL failed: {type(e).__name__}: {str(e)}"
        print(f"FEHLER: Kritischer Verarbeitungsfehler für {gcs_path}: {log_row['additional_info']}")
        
        try:
             # Logge den Fehlerstatus
             insert_log_job(bqclient, log_row)
        except:
             print("WARNUNG: Konnte selbst den Fehlerstatus nicht protokollieren. Verarbeitung wird beendet.")
        
        raise

    print(f"Verarbeitung abgeschlossen (Status: {log_row['status']}): {gcs_path}")
    return tablename

def main():
    print("MAIN FN EXECUTED")
    
    ensure_audit_tables_exist(bqclient)
    
    mastermapping = {}
    for jsonfile in SCHEMAJSONFILES:
        mapping = loadschemamappingjsonfile(jsonfile)
        mastermapping.update(mapping)
        
    if not mastermapping:
        print("KRITISCHER FEHLER: Master-Schema-Mapping ist leer. Beende ETL.")
        return
        
    all_parquet_paths = []
    for prefix in TARGET_GCS_PREFIXES:
        paths = list_gcs_parquet_files(BUCKET_NAME, prefix)
        all_parquet_paths.extend(paths)
        
    if not all_parquet_paths:
        print("INFO: Keine Parquet-Dateien in den Ziel-Ordnern gefunden. Beende ETL.")
        return

    print(f"INFO: {len(all_parquet_paths)} Dateien in den Ziel-Ordnern gefunden.")
    
    successful_files = get_processed_files(bqclient)
    
    for gcs_path in all_parquet_paths:
        filename = gcs_path.split("/")[-1] 
        
        if filename in successful_files:
            print(f"INFO: Überspringe Datei {gcs_path} (bereits erfolgreich im Audit-Log gefunden).")
            continue
        
        if filename in mastermapping:
            try:
                processfile(bqclient, mastermapping, filename, gcs_path)
            except Exception as e:
                print(f"\nFATAL ERROR: Verarbeitung von {gcs_path} abgebrochen. Überprüfen Sie die Logs.")
                return 
        else:
            # Sende Datei trotzdem an processfile zur Log-Erstellung des 'quarantine'-Status.
            processfile(bqclient, mastermapping, filename, gcs_path)

if __name__ == "__main__":
    main()
    print("\nETL-Lauf abgeschlossen.")