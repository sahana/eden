
import os
from os.path import join, exists
from os import stat, makedirs


# create folder for cache:
# mkdir -p /tmp/climate_data_portal/images/recent/
# mkdir -p /tmp/climate_data_portal/images/older/

MAX_CACHE_FOLDER_SIZE = 2**24 # 16 MiB

class TwoStageCache(object):
    def __init__(self, folder, max_size):
        self.folder = folder
        self.max_size
    
    def purge(self):
        pass
    
    def retrieve(self, file_name, generate_if_not_found):
        pass

import os, errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

def get_cached_or_generated_file(cache_file_name, generate):
    # this needs to become a setting
    climate_data_image_cache_path = join(
        "/tmp","climate_data_portal","images"
    )
    recent_cache = join(climate_data_image_cache_path, "recent")
    mkdir_p(recent_cache)
    older_cache = join(climate_data_image_cache_path, "older")
    mkdir_p(older_cache)
    recent_cache_path = join(recent_cache, cache_file_name)
    if not exists(recent_cache_path):
        older_cache_path = join(older_cache, cache_file_name)
        if exists(older_cache_path):
            # move the older cache to the recent folder
            rename(older_cache_path, recent_cache_path)
        else:
            generate(recent_cache_path)
        file_path = recent_cache_path
            
        # update the folder size file (race condition?)
        folder_size_file_path = join(climate_data_image_cache_path, "size")
        folder_size_file = open(folder_size_file_path, "w+")
        folder_size_file_contents = folder_size_file.read()
        try:
            folder_size = int(folder_size_file_contents)
        except ValueError:
            folder_size = 0
        folder_size_file.seek(0)
        folder_size_file.truncate()
        folder_size += stat(file_path).st_size
        if folder_size > MAX_CACHE_FOLDER_SIZE:
            rmdir(older_cache)

        folder_size_file.write(str(folder_size))
        folder_size_file.close()
    else:
        # use the existing cached image
        file_path = recent_cache_path
    return file_path

