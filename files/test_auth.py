import s3fs
fs = s3fs.S3FileSystem(
    key="VOTRE_ACCESS_KEY",
    secret="VOTRE_SECRET_KEY",
    client_kwargs={"endpoint_url": "https://s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud"},
)
with fs.open("bu002i010448/publication/.../fichier.csv", "rb") as f:
    df = pl.read_csv(f)
