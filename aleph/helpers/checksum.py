import hashlib

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