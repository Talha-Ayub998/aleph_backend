import hashlib
import os
from fs import open_fs
import mimetypes
import datetime

def calculate_checksum(file_path, file_name):
    # Initialize a SHA-256 hash object
    sha256_hash = hashlib.sha256()
    
    # Open the file in binary mode and read in chunks
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    # Include the original file name in the hash calculation
    sha256_hash.update(file_name.encode('utf-8'))
    
    # Return the hexadecimal representation of the hash
    return sha256_hash.hexdigest()

def get_file_metadata(file_path):
    # Open the filesystem
    fs = open_fs(os.path.dirname(file_path))
    
    # Get basic file information
    file_info = fs.getinfo(os.path.basename(file_path), namespaces=['basic', 'details', 'access'])
    
    # Get the file type using the mimetypes library
    file_type, _ = mimetypes.guess_type(file_path)
    file_type = file_type or 'unknown'
    
    # Extract detailed metadata
    metadata = {
        'Name': file_info.name,
        'Size (bytes)': file_info.size,
        'Type': file_type,
        'Is Directory': file_info.is_dir,
        'Permissions': file_info.permissions
    }
    
    return metadata