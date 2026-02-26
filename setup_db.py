import os
import glob
import zipfile

DB_DIR = 'prospektus_db'
ZIP_NAME = 'prospektus_db.zip'

if not os.path.exists(DB_DIR):
    parts = sorted(glob.glob('chunk_*.dat'))
    if parts:
        print("Reassembling ZIP file from chunks...")
        with open(ZIP_NAME, 'wb') as outfile:
            for part in parts:
                with open(part, 'rb') as infile:
                    outfile.write(infile.read())
        
        print("Extracting ZIP file...")
        os.makedirs(DB_DIR, exist_ok=True)
        with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
            zip_ref.extractall(DB_DIR) 
            
        print("Cleaning up ZIP...")
        os.remove(ZIP_NAME)
        print("Database successfully prepared.")
    else:
        print("Warning: Database chunks not found! Make sure they were uploaded.")
else:
    print("Database already exists. Skipping reassembly.")
