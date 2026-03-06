import os
import glob
import zipfile

DB_DIR = 'prospektus_db'
ZIP_NAME = 'prospektus_db.zip'

if not os.path.exists(DB_DIR):
    parts = sorted(glob.glob('db_part_*.dat'))
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
        
        # İç içe klasör oluşmuşsa (prospektus_db/prospektus_db_full) dosyaları dışarı çıkar
        nested_dir = os.path.join(DB_DIR, 'prospektus_db_full')
        if os.path.exists(nested_dir):
            import shutil
            print("Nested directory detected. Moving files to the root of prospektus_db...")
            for item in os.listdir(nested_dir):
                shutil.move(os.path.join(nested_dir, item), DB_DIR)
            os.rmdir(nested_dir)
            
        print("Cleaning up ZIP...")
        os.remove(ZIP_NAME)
        print("Database successfully prepared.")
    else:
        print("Warning: Database chunks not found! Make sure they were uploaded.")
else:
    print("Database already exists. Skipping reassembly.")
