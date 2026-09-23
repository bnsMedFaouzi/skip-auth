import shutil
import tempfile

tmp_dir = tempfile.gettempdir()
before = shutil.disk_usage(tmp_dir).used

lf = pl.scan_csv("s3://bucket/fichier.csv", storage_options=storage_options)
df = lf.collect()

after = shutil.disk_usage(tmp_dir).used
print(f"Espace utilisé en plus dans {tmp_dir}: {(after - before) / 1024 / 1024:.2f} Mo")


import psutil
import threading
import time
import os

found_files = set()

def monitor():
    p = psutil.Process(os.getpid())
    while not stop_flag.is_set():
        for f in p.open_files():
            if "polars" in f.path and "file-cache" in f.path:
                found_files.add(f.path)
        time.sleep(0.1)

stop_flag = threading.Event()
t = threading.Thread(target=monitor)
t.start()

lf = pl.scan_csv("s3://bucket/fichier.csv", storage_options=storage_options)
df = lf.collect()

stop_flag.set()
t.join()
print("Fichiers cache détectés:", found_files)



import glob
import tempfile

pattern = f"{tempfile.gettempdir()}/polars-*/file-cache/**"
files = glob.glob(pattern, recursive=True)
print(files)


before = shutil.disk_usage(tmp_dir).used
lf.collect_schema()  # ne devrait lire que le header
after_schema = shutil.disk_usage(tmp_dir).used

lf.collect()  # lit tout
after_full = shutil.disk_usage(tmp_dir).used

print(f"Après schema: +{(after_schema-before)/1024:.1f} Ko")
print(f"Après collect complet: +{(after_full-before)/1024/1024:.1f} Mo")
