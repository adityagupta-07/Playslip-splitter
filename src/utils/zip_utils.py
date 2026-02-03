import os
import zipfile

def create_zip(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(source_dir):
            full_path = os.path.join(source_dir, file)
            zipf.write(full_path, arcname=file)
