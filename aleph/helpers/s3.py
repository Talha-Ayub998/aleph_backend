import boto3

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

    def s3_push(self, file_name, bucket_name, key="credentials.json"):
        try:
            self.s3.Bucket(bucket_name).upload_file(
                Filename=file_name, Key=key)
        except Exception as e:
            print(e)

    def download_from_s3(self, s3_file, s3_bucket, local_file):
        try:
            self.s3.Bucket(s3_bucket).download_file(s3_file, local_file)
            print("Successfully Downloaded")
        except Exception as e:
            print(e)

    def get_document_url(self, s3_file, s3_bucket):
        try:
            bucket = self.s3.Bucket(s3_bucket)
            object_url = f"https://{bucket.name}.s3.amazonaws.com/{s3_file}"
            return object_url
        except Exception as e:
            print(e)
            return None

    def delete_file(self, s3_file, s3_bucket):
        try:
            self.client.delete_object(Bucket=s3_bucket, Key=s3_file)
            print(f"Successfully deleted {s3_file} from {s3_bucket}")
        except Exception as e:
            print(e)