import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from tempfile import NamedTemporaryFile

load_dotenv()


class ArchiveManager():
    def __init__(self):
        self.access_key = os.environ["AWS_ACCESS_KEYID"]
        self.secret_access_key = os.environ["AWS_SECRET_ACCESSKEY"]
        self.bucket_name = os.environ["AWS_STORAGE_BUCKET_NAME"]
        self.client = boto3.client('s3',
                                   aws_access_key_id=self.access_key,
                                   aws_secret_access_key=self.secret_access_key)

    def read_directory(self, prefix="archive/"):
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, Delimiter="/")

            initial_files = []

            # Handling files and immediate subfolders in the current folder
            if 'Contents' in response:
                for content in response['Contents']:
                    # Exclude the prefix itself if listed as a "folder"
                    if content.get('Key') != prefix:
                        file_key = content.get('Key')
                        file_name = file_key.split('/')[-1]

                        # Assume everything at this level is a file (since we're using Delimiter="/")
                        file_type = self.get_file_type(file_name)
                        initial_files.append({
                            "key": file_key,
                            "name": file_name,
                            "size": content.get('Size', 0),
                            "type": file_type,
                            "lastModified": content.get('LastModified').strftime('%Y-%m-%d %H:%M') if content.get('LastModified') else '',
                            "eTag": content.get('ETag', ''),
                            "createdBy": "unknown",
                            "lastModifiedBy": "unknown"
                        })

            # Direct subfolders (common prefixes)
            if 'CommonPrefixes' in response:
                for prefix_info in response['CommonPrefixes']:
                    folder_key = prefix_info.get('Prefix')
                    folder_name = folder_key.strip('/').split('/')[-1]

                    initial_files.append({
                        "key": folder_key,
                        "name": folder_name,
                        "size": 0,  # Folders don't have a size
                        "type": 'folder',
                        "lastModified": '',  # Folders don't have a last modified timestamp
                        "eTag": '',
                        "createdBy": "unknown",
                        "lastModifiedBy": "unknown"
                    })

            return {
                "name": prefix.strip('/').split('/')[-1] if prefix.strip('/') else 'root',
                "files": initial_files,
            }

        except ClientError as e:
            print(
                f"An error occurred reading {self.bucket_name} root directory: {e}")
            raise e

    def get_file_type(self, file_name):
        # Mapping extensions to a human-readable file type
        extension_to_type = {
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.svg': 'image',
            '.webp': 'image',
            '.pdf': 'pdf',
            '.doc': 'document',
            '.docx': 'document',
            '.xls': 'spreadsheet',
            '.xlsx': 'spreadsheet',
            '.ppt': 'presentation',
            '.pptx': 'presentation',
            '.txt': 'text',
            '.csv': 'csv',
            '.zip': 'archive',
            '.rar': 'archive',
            '.tar': 'archive',
            '.gz': 'archive',
            '.mp3': 'audio',
            '.wav': 'audio',
            '.ogg': 'audio',
            '.mp4': 'video',
            '.avi': 'video',
            '.mkv': 'video',
            '.mov': 'video',
            '.flv': 'video',
            '.wmv': 'video',
            '.webm': 'video',
            '.html': 'web',
            '.css': 'web',
            '.js': 'web',
            '.json': 'json',
            '.xml': 'xml',
        }

        default_type = 'file'

        extension = os.path.splitext(file_name)[1].lower()

        return extension_to_type.get(extension, default_type)

    def file_exists(self, object_name):
        """Check if a file exists in the bucket."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            # The file does not exist or other error
            return False

    def upload_file(self, file_object, file_name, folder_path):
        """Upload a file to a specified folder within the bucket, checking if the file already exists."""
        object_name = f'{folder_path}{file_name}' if folder_path else file_name
        if self.file_exists(object_name):
            print(f"File {object_name} already exists")
            return {"code": "fileExists", "message": "File already exists"}

        # else, continue uploading
        temp = NamedTemporaryFile(delete=False)
        try:
            contents = file_object.file.read()
            with open(temp.name, 'wb') as f:
                f.write(contents)
            self.client.upload_file(temp.name, self.bucket_name, object_name, ExtraArgs={
                                    "ACL": 'public-read', "ContentType": file_object.content_type})

            return {"code": "success", "message": "File uploaded successfully"}
        except ClientError as e:
            print(f"An error occurred uploading the file: {e}")
            return {"code": "error", "message": f"There was an error uploading the file: {e}"}
        finally:
            os.remove(temp.name)
            file_object.file.close()  # new added line

    def replace_file(self, file_object, file_name, folder_path=''):
        """Replace and existing file in a specified folder within the bucket."""
        object_name = f'{folder_path}{file_name}' if folder_path else file_name

        temp = NamedTemporaryFile(delete=False)
        try:
            contents = file_object.file.read()
            with open(temp.name, 'wb') as f:
                f.write(contents)
            self.client.upload_file(temp.name, self.bucket_name, object_name, ExtraArgs={
                                    "ACL": 'public-read', "ContentType": file_object.content_type})

            return {"code": "success", "message": "File uploaded successfully"}
        except:
            return {"code": "error", "message": "There was an error uploading the file"}
        finally:
            os.remove(temp.name)
            file_object.file.close()  # new added line

    def create_folder(self, folder_name, parent_path="archive/"):
        """
        Create a folder in the S3 bucket at the specified path.

        :param folder_name: The name of the new folder.
        :param parent_path: The path where the new folder will be created, ending with a slash.
        """
        # Ensure the parent_path ends with a slash
        if not parent_path.endswith('/'):
            parent_path += '/'

        # Construct the full path for the new folder
        full_folder_path = f"{parent_path}{folder_name}/"

        # Check if the folder already exists
        if self.file_exists(full_folder_path):
            print(f"Folder '{full_folder_path}' already exists in the bucket.")
            return {"code": "folderExists", "message": "Folder already exists"}

        try:
            # Create the folder by putting an empty object with a key ending in a slash
            self.client.put_object(
                Bucket=self.bucket_name, Key=full_folder_path)
            # print(f"Folder '{full_folder_path}' created successfully.")
            return {"code": "success", "message": f"Folder '{folder_name}' created successfully"}
        except ClientError as e:
            print(f"An error occurred creating the folder: {e}")
            return {"code": "error", "message": f"There was an error creating the folder: {e}"}
