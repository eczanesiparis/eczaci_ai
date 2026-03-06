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
        print("Extracting ZIP file manually to handle Windows backslashes...", flush=True)
        os.makedirs(DB_DIR, exist_ok=True)
        with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                # Windows'taki ters slaslari platform bagimsiz slash'e cevir
                target_path = zip_info.filename.replace('\\', '/')
                
                # Sadece 'prospektus_db_full/' on ekini temizle, dogrudan DB_DIR icine at
                if target_path.startswith('prospektus_db_full/'):
                    target_path = target_path[len('prospektus_db_full/'):]
                
                # Eger temizlendikten sonra bosa dusmusse (klasorun kendisi) gec
                if not target_path:
                    continue

                full_path = os.path.join(DB_DIR, target_path)
                
                # Eger bu bir klasorse, onu olustur
                if zip_info.is_dir() or target_path.endswith('/'):
                    os.makedirs(full_path, exist_ok=True)
                    continue
                
                # Eger dosya ise, bulundugu klasoru once guvence altina al, sonra dosyayi yaz
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # OUT OF MEMORY (OOM) ÇÖZÜMÜ: 
                # sunucunun (Render) RAM'i (512MB), dosyanın (830MB) boyutundan küçük olduğu için 
                # file.read() ile tüm dosyayı RAM'e almak yerine parça parça akıtarak yazıyoruz!
                with zip_ref.open(zip_info) as source, open(full_path, 'wb') as outfile:
                    shutil.copyfileobj(source, outfile, length=1024*1024)  # 1 MB'lik parçalarla aktar
            
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
