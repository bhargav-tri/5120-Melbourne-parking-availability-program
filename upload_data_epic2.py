import os
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values

# Connection string for the target Railway Postgres instance
DATABASE_URL = "postgresql://postgres:eSyUrNgzoGjZybYhxZRwLKaSbAxkQmIQ@trolley.proxy.rlwy.net:13392/railway"

# Establish connection
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Local folder containing the CSV files
base_path = "/Users/ruiqisu/Desktop/FIT5120/TA47 On-boarding project"

# -------- Table 1: on_street_parking_bay_sensors --------
df1 = pd.read_csv(f"{base_path}/on-street-parking-bay-sensors.csv", dtype=str)
df1.columns = df1.columns.str.strip()

# Parse and clean columns
df1['Lastupdated'] = pd.to_datetime(df1['Lastupdated'], errors='coerce')
df1['Status_Timestamp'] = pd.to_datetime(df1['Status_Timestamp'], errors='coerce')
df1['Zone_Number'] = pd.to_numeric(df1['Zone_Number'], errors='coerce')
df1['KerbsideID'] = pd.to_numeric(df1['KerbsideID'], errors='coerce')
df1 = df1.dropna(subset=['Lastupdated','Status_Timestamp','Zone_Number','KerbsideID'])
df1['Zone_Number'] = df1['Zone_Number'].astype(int)
df1['KerbsideID'] = df1['KerbsideID'].astype(int)

cur.execute("""
CREATE TABLE IF NOT EXISTS on_street_parking_bay_sensors (
    kerbsideid       INTEGER,
    zone_number      INTEGER,
    lastupdated      TIMESTAMP WITHOUT TIME ZONE,
    status_timestamp TIMESTAMP WITHOUT TIME ZONE,
    location         TEXT,
    PRIMARY KEY (kerbsideid, zone_number)
)
""")

records1 = df1[['KerbsideID','Zone_Number','Lastupdated','Status_Timestamp','Location']].values.tolist()
execute_values(cur, """
INSERT INTO on_street_parking_bay_sensors
    (kerbsideid, zone_number, lastupdated, status_timestamp, location)
VALUES %s
ON CONFLICT (kerbsideid, zone_number) DO NOTHING
""", records1)
print("Table 1 uploaded")

# -------- Table 2: on_street_parking_bays --------
df2 = pd.read_csv(f"{base_path}/on-street-parking-bays.csv", dtype=str)
df2.columns = df2.columns.str.strip()

df2['LastUpdated'] = pd.to_datetime(df2['LastUpdated'], errors='coerce')
df2['RoadSegmentID'] = pd.to_numeric(df2['RoadSegmentID'], errors='coerce')
df2['KerbsideID']    = pd.to_numeric(df2['KerbsideID'], errors='coerce')
df2['Latitude']      = pd.to_numeric(df2['Latitude'], errors='coerce')
df2['Longitude']     = pd.to_numeric(df2['Longitude'], errors='coerce')
df2 = df2.dropna(subset=['LastUpdated','RoadSegmentID','KerbsideID','Latitude','Longitude'])
df2 = df2.astype({
    'RoadSegmentID': 'int',
    'KerbsideID':    'int',
    'Latitude':      'float',
    'Longitude':     'float'
})

cur.execute("""
CREATE TABLE IF NOT EXISTS on_street_parking_bays (
    roadsegmentid          INTEGER PRIMARY KEY,
    kerbsideid             INTEGER,
    roadsegmentdescription TEXT,
    latitude               DOUBLE PRECISION,
    longitude              DOUBLE PRECISION,
    lastupdated            TIMESTAMP WITHOUT TIME ZONE,
    location               TEXT
)
""")

records2 = df2[['RoadSegmentID','KerbsideID','RoadSegmentDescription',
                'Latitude','Longitude','LastUpdated','Location']].values.tolist()
execute_values(cur, """
INSERT INTO on_street_parking_bays
    (roadsegmentid, kerbsideid, roadsegmentdescription, latitude, longitude, lastupdated, location)
VALUES %s
ON CONFLICT (roadsegmentid) DO NOTHING
""", records2)
print("Table 2 uploaded")

# -------- Table 3: parking_zones_linked_to_street_segments --------
df3 = pd.read_csv(f"{base_path}/parking-zones-linked-to-street-segments.csv", dtype=str)
df3.columns = df3.columns.str.strip()

df3['Segment_ID'] = pd.to_numeric(df3['Segment_ID'], errors='coerce')
df3 = df3.dropna(subset=['Segment_ID'])
df3['Segment_ID'] = df3['Segment_ID'].astype(int)

cur.execute("""
CREATE TABLE IF NOT EXISTS parking_zones_linked_to_street_segments (
    parkingzone TEXT,
    onstreet     TEXT,
    streetfrom   TEXT,
    streetto     TEXT,
    segment_id   INTEGER,
    PRIMARY KEY (parkingzone, segment_id)
)
""")

records3 = df3[['ParkingZone','OnStreet','StreetFrom','StreetTo','Segment_ID']].values.tolist()
execute_values(cur, """
INSERT INTO parking_zones_linked_to_street_segments
    (parkingzone, onstreet, streetfrom, streetto, segment_id)
VALUES %s
ON CONFLICT (parkingzone, segment_id) DO NOTHING
""", records3)
print("Table 3 uploaded")

# -------- Table 4: sign_plates_located_in_each_parking_zone --------
df4 = pd.read_csv(f"{base_path}/sign-plates-located-in-each-parking-zone.csv", dtype=str)
df4.columns = df4.columns.str.strip()

df4['Time_Restrictions_Start'] = pd.to_datetime(
    df4['Time_Restrictions_Start'], format='%H:%M', errors='coerce'
).dt.time
df4['Time_Restrictions_Finish'] = pd.to_datetime(
    df4['Time_Restrictions_Finish'], format='%H:%M', errors='coerce'
).dt.time
df4 = df4.dropna(subset=['Time_Restrictions_Start','Time_Restrictions_Finish'])

cur.execute("""
CREATE TABLE IF NOT EXISTS sign_plates_located_in_each_parking_zone (
    parkingzone              TEXT,
    restriction_days         TEXT,
    time_restrictions_start  TIME WITHOUT TIME ZONE,
    time_restrictions_finish TIME WITHOUT TIME ZONE,
    restriction_display      TEXT,
    PRIMARY KEY (parkingzone, time_restrictions_start, time_restrictions_finish)
)
""")

records4 = df4[['ParkingZone','Restriction_Days',
                'Time_Restrictions_Start','Time_Restrictions_Finish','Restriction_Display']].values.tolist()
execute_values(cur, """
INSERT INTO sign_plates_located_in_each_parking_zone
    (parkingzone, restriction_days, time_restrictions_start, time_restrictions_finish, restriction_display)
VALUES %s
ON CONFLICT (parkingzone, time_restrictions_start, time_restrictions_finish) DO NOTHING
""", records4)
print("Table 4 uploaded")

# Commit and close connection
conn.commit()
cur.close()
conn.close()
print("All tables uploaded successfully")