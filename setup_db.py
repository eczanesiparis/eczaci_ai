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
        
        print("Extracting ZIP file...", flush=True)
        os.makedirs(DB_DIR, exist_ok=True)
        with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
            zip_ref.extractall(DB_DIR) 
        
        # İç içe klasör oluşmuşsa (prospektus_db/prospektus_db_full) dosyaları dışarı çıkar
        nested_dir = os.path.join(DB_DIR, 'prospektus_db_full')
        if os.path.exists(nested_dir):
            print("Nested directory detected. Moving files to the root of prospektus_db...", flush=True)
            for item in os.listdir(nested_dir):
                shutil.move(os.path.join(nested_dir, item), DB_DIR)
            os.rmdir(nested_dir)
            
        print("Cleaning up ZIP...", flush=True)
        if os.path.exists(ZIP_NAME):
            os.remove(ZIP_NAME)
        print("Database successfully prepared.", flush=True)
    else:
        print("Warning: Database chunks not found! Make sure they were uploaded.", flush=True)
else:
    print("Database already exists and structure is solid. Skipping reassembly.", flush=True)
