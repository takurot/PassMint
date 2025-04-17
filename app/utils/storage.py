import os
import aioboto3
from dotenv import load_dotenv
from typing import BinaryIO, Optional
from io import BytesIO

load_dotenv()

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "passmint")


class S3Storage:
    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
        self.endpoint_url = S3_ENDPOINT
        self.bucket_name = S3_BUCKET_NAME

    async def upload_file(
        self, 
        file_content: BinaryIO, 
        key: str, 
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to S3 storage.
        
        Args:
            file_content: File content to upload
            key: S3 key
            content_type: Optional content type
            
        Returns:
            URL to the uploaded file
        """
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        async with self.session.client(
            "s3", endpoint_url=self.endpoint_url
        ) as s3:
            # Create bucket if it doesn't exist
            try:
                await s3.head_bucket(Bucket=self.bucket_name)
            except:
                await s3.create_bucket(Bucket=self.bucket_name)

            # Upload file
            await s3.upload_fileobj(
                file_content, 
                self.bucket_name, 
                key, 
                ExtraArgs=extra_args
            )
            
            # Generate URL
            url = f"{self.endpoint_url}/{self.bucket_name}/{key}"
            return url

    async def get_file(self, key: str) -> BytesIO:
        """
        Get a file from S3 storage.
        
        Args:
            key: S3 key
            
        Returns:
            File content as BytesIO
        """
        file_content = BytesIO()
        
        async with self.session.client(
            "s3", endpoint_url=self.endpoint_url
        ) as s3:
            await s3.download_fileobj(
                self.bucket_name, 
                key, 
                file_content
            )
        
        file_content.seek(0)
        return file_content


# Create a singleton instance
storage = S3Storage() 