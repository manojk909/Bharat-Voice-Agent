import os
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class VultrStorageClient:
    def __init__(self):
        endpoint_url = os.getenv("VULTR_S3_ENDPOINT")
        access_key = os.getenv("VULTR_S3_ACCESS_KEY")
        secret_key = os.getenv("VULTR_S3_SECRET_KEY")
        self.bucket_name = os.getenv("VULTR_S3_BUCKET_NAME")
        
        if not all([endpoint_url, access_key, secret_key, self.bucket_name]):
            raise ValueError("Missing Vultr S3 configuration variables.")

        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """Generate a presigned URL to share an S3 object."""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
        return response

    def upload_file_obj(self, file_obj, object_name: str) -> str:
        """Upload a file-like object to Vultr S3."""
        try:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
            logger.info(f"File {object_name} uploaded successfully.")
            return self.generate_presigned_url(object_name)
        except ClientError as e:
            logger.error(f"Failed to upload file to Vultr S3: {e}")
            raise
