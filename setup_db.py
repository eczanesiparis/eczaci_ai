import os
import glob
import zipfile
import shutil

DB_DIR = 'prospektus_db'
ZIP_NAME = 'prospektus_db.zip'

# 1. Adım: Render önbellek kontrolü - Klasör var ama içi boşsa/bozuksa veya sadece otomatik oluşmuş boş veritabanıysa sil
if os.path.exists(DB_DIR):
    chroma_file = os.path.join(DB_DIR, 'chroma.sqlite3')
    # Eğer dosya yoksa VEYA dosya 1 MB'dan küçükse (boş langchain iskeletiyse):
    if not os.path.exists(chroma_file) or os.path.getsize(chroma_file) < 1000 * 1024:
        print("Bulunan klasör eksik veya bozuk (chroma.sqlite3 çok küçük/yok). Temizleniyor...", flush=True)
        shutil.rmtree(DB_DIR)

# 2. Adım: Klasör yoksa (veya az önce silindiyse) parçaları birleştir ve çıkar
if not os.path.exists(DB_DIR):
    parts = sorted(glob.glob('db_part_*.dat'))
    if parts:
        print(f"DEBUG - Found parts: {parts}", flush=True)
        for part in parts:
            print(f"DEBUG - {part} size: {os.path.getsize(part)} bytes", flush=True)

        # GİT LFS KONTROLÜ: GitHub bu büyük dosyaları text pointer olarak indirmiş olabilir (yaklaşık 130 byte)
        # Eğer ilk part 1 MB'dan küçükse, bu bir LFS pointer'ıdır ve asıl veri indirilmemiştir.
        if os.path.getsize(parts[0]) < 1000 * 1024:
            print("Uyarı: .dat dosyaları Git LFS pointer olarak inmiş. Asıl veriler indiriliyor...", flush=True)
            import subprocess
            try:
                subprocess.run(["git", "lfs", "install"], check=True)
                subprocess.run(["git", "lfs", "pull"], check=True)
                print("Git LFS verileri başarıyla indirildi.", flush=True)
            except Exception as e:
                print(f"LFS indirme hatası: {e}. Lütfen Render.com ayarlarından Git LFS'i aktif edin.", flush=True)

        print("Reassembling ZIP file from chunks...", flush=True)
        with open(ZIP_NAME, 'wb') as outfile:
            for part in parts:
                with open(part, 'rb') as infile:
                    outfile.write(infile.read())
        
        print(f"DEBUG - Assembled ZIP size: {os.path.getsize(ZIP_NAME)} bytes", flush=True)
        print("Extracting ZIP file...", flush=True)
        os.makedirs(DB_DIR, exist_ok=True)
        with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
            print(f"DEBUG - ZIP namelist preview: {zip_ref.namelist()[:5]}", flush=True)
            zip_ref.extractall(DB_DIR) 
        
        print(f"DEBUG - DB_DIR contents directly after extract: {os.listdir(DB_DIR)}", flush=True)
        
        # İç içe klasör oluşmuşsa dosyaları dışarı çıkar
        from pathlib import Path
        for item in os.listdir(DB_DIR):
            nested_path = os.path.join(DB_DIR, item)
            if os.path.isdir(nested_path) and "prospektus" in item.lower():
                print(f"Nested directory detected '{item}'. Moving files to the root of {DB_DIR}...", flush=True)
                for sub_item in os.listdir(nested_path):
                    shutil.move(os.path.join(nested_path, sub_item), DB_DIR)
                os.rmdir(nested_path)
            
        print("Cleaning up ZIP...", flush=True)
        if os.path.exists(ZIP_NAME):
            os.remove(ZIP_NAME)
        
        # Final Verification
        final_files = os.listdir(DB_DIR)
        print(f"DEBUG - Final DB_DIR contents: {final_files}", flush=True)
        db_file = os.path.join(DB_DIR, 'chroma.sqlite3')
        if os.path.exists(db_file):
            print(f"DEBUG - chroma.sqlite3 final size: {os.path.getsize(db_file)} bytes", flush=True)
        
        print("Database successfully prepared.", flush=True)
    else:
        print("Warning: Database chunks not found! Make sure they were uploaded.", flush=True)
else:
    print("Database already exists and structure is solid. Skipping reassembly.", flush=True)
