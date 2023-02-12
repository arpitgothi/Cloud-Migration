import os
import shutil
import logging

def restore_directory(src, dst, force_restore=False):
    try:
        if not os.path.exists(dst) or force_restore:
            shutil.copytree(src, dst)
            logging.info(f"Directory {src} restored to {dst}")
        else:
            logging.info(f"Directory {dst} already exists. Skipping restore.")
    except Exception as e:
        logging.error(f"Error restoring directory {src}: {e}")

logging.basicConfig(filename="restore.log", level=logging.INFO)
backup_location = "/path/to/backup/location"
original_location = "/path/to/original/location"
force_restore = True

for dir_name in os.listdir(backup_location):
    backup_dir = os.path.join(backup_location, dir_name)
    original_dir = os.path.join(original_location, dir_name)
    if os.path.isdir(backup_dir):
        for sub_dir_name in os.listdir(backup_dir):
            backup_sub_dir = os.path.join(backup_dir, sub_dir_name)
            original_sub_dir = os.path.join(original_dir, sub_dir_name)
            if sub_dir_name in ['local', 'lookups'] and os.path.isdir(backup_sub_dir):
                restore_directory(backup_sub_dir, original_sub_dir, force_restore)
