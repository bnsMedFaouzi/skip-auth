import shutil
import tempfile

tmp_dir = tempfile.gettempdir()
before = shutil.disk_usage(tmp_dir).used

lf = pl.scan_csv("s3://bucket/fichier.csv", storage_options=storage_options)
df = lf.collect()

after = shutil.disk_usage(tmp_dir).used
print(f"Espace utilisé en plus dans {tmp_dir}: {(after - before) / 1024 / 1024:.2f} Mo")
