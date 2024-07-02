import boto3
import mimetypes

class S3Service:
    def __init__(self, s3="s3", region_name=None, aws_access_key_id=None, aws_secret_access_key=None) -> None:
        self.s3 = boto3.resource(
            service_name=s3,
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.client = boto3.client(
            service_name=s3,
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    def upload_to_s3(self, file_name, bucket_name, key=None):
        """
        Uploads a file to the specified S3 bucket.

        Args:
            file_name (str): The local path of the file to upload.
            bucket_name (str): The name of the S3 bucket.
            key (str, optional): The key (path) under which to store the file in the bucket. Defaults to None.

        Returns:
            bool: True if upload is successful, False otherwise.
        """
        try:
            # Guess the MIME type of the file
            content_type, _ = mimetypes.guess_type(file_name)
            if content_type is None:
                content_type = 'application/octet-stream'  # Fallback MIME type

            # Upload the file with the specified content type
            self.s3.Bucket(bucket_name).upload_file(
                Filename=file_name,
                Key=key,
                ExtraArgs={'ContentType': content_type}
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to upload {file_name} to {bucket_name}: {e}")
    
    def upload_image_to_s3(self, image_bytes, bucket_name, key=None):
        """
        Uploads image bytes to the specified S3 bucket.

        Args:
            image_bytes (bytes): The bytes of the image to upload.
            bucket_name (str): The name of the S3 bucket.
            key (str, optional): The key (path) under which to store the image in the bucket. Defaults to None.

        Returns:
            bool: True if upload is successful, False otherwise.
        """
        try:
            # Upload the image bytes
            self.s3.Bucket(bucket_name).put_object(
                Key=key,
                Body=image_bytes
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to upload image to {bucket_name}: {e}")

    def download_from_s3(self, s3_file, s3_bucket, local_file):
        """
        Downloads a file from the specified S3 bucket to the local filesystem.

        Args:
            s3_file (str): The key (path) of the file in the S3 bucket.
            s3_bucket (str): The name of the S3 bucket.
            local_file (str): The local path where the file will be saved.

        Returns:
            bool: True if download is successful, False otherwise.
        """
        try:
            self.s3.Bucket(s3_bucket).download_file(s3_file, local_file)
            return True
        except Exception as e:
            raise Exception(f"Failed to download {s3_file} from {s3_bucket}: {e}")

    def get_document_url(self, s3_file, s3_bucket):
        """
        Generates a pre-signed URL for accessing the specified file in the S3 bucket.

        Args:
            s3_file (str): The key (path) of the file in the S3 bucket.
            s3_bucket (str): The name of the S3 bucket.

        Returns:
            str: The pre-signed URL for accessing the file.
        """
        try:
            bucket = self.s3.Bucket(s3_bucket)
            object_url = f"https://{bucket.name}.s3.amazonaws.com/{s3_file}"
            return object_url
        except Exception as e:
            raise Exception(f"Failed to get URL for {s3_file} in {s3_bucket}: {e}")

    def delete_file(self, s3_file, s3_bucket):
        """
        Deletes the specified file from the S3 bucket.

        Args:
            s3_file (str): The key (path) of the file in the S3 bucket.
            s3_bucket (str): The name of the S3 bucket.

        Returns:
            bool: True if deletion is successful, False otherwise.
        """
        try:
            self.client.delete_object(Bucket=s3_bucket, Key=s3_file)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete {s3_file} from {s3_bucket}: {e}")

    def bulk_delete_files(self, file_keys, s3_bucket):
        """
        Deletes multiple files from the specified S3 bucket.

        Args:
            file_keys (list): List of file keys (paths) in the S3 bucket to be deleted.
            s3_bucket (str): The name of the S3 bucket.

        Returns:
            dict: A dictionary containing the results of the deletion operation.
        """
        try:
            objects_to_delete = [{'Key': key} for key in file_keys]
            response = self.client.delete_objects(Bucket=s3_bucket, Delete={'Objects': objects_to_delete})
            return response
        except Exception as e:
            raise Exception(f"Failed to delete files from {s3_bucket}: {e}")
