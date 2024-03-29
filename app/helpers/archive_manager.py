import os
import boto3
from dotenv import load_dotenv
import zipfile
from botocore.exceptions import ClientError
from tempfile import NamedTemporaryFile, TemporaryDirectory

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

                        try:
                            metadata_response = self.client.head_object(
                                Bucket=self.bucket_name,
                                Key=file_key
                            )
                            last_modified_by = metadata_response.get(
                                'Metadata', {}).get('last_modified_by', 'unknown')
                        except ClientError as e:
                            print(f"Could not fetch metadata for {file_key}: {e}")
                            last_modified_by = "unknown"

                        file_type = self.get_file_type(file_name)
                        initial_files.append({
                            "key": file_key,
                            "name": file_name,
                            "size": content.get('Size', 0),
                            "type": file_type,
                            "lastModified": content.get('LastModified').strftime('%Y-%m-%d %H:%M') if content.get('LastModified') else '',
                            "eTag": content.get('ETag', ''),
                            "createdBy": last_modified_by,  # Using last_modified_by which defaults to "system" if not present
                            "lastModifiedBy": last_modified_by
                        })

            # Direct subfolders (common prefixes)
            if 'CommonPrefixes' in response:
                for prefix_info in response['CommonPrefixes']:
                    folder_key = prefix_info.get('Prefix')
                    folder_name = folder_key.strip('/').split('/')[-1]

                    # No metadata is fetched for folders as they are virtual in S3
                    initial_files.append({
                        "key": folder_key,
                        "name": folder_name,
                        "size": 0,
                        "type": 'folder',
                        "lastModified": '',
                        "eTag": '',
                        "createdBy": "unknown",
                        "lastModifiedBy": "unknown"
                    })

            return {
                "name": prefix.strip('/').split('/')[-1] if prefix.strip('/') else 'root',
                "files": initial_files,
            }

        except ClientError as e:
            print(f"An error occurred reading {self.bucket_name} root directory: {e}")
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

    def upload_file(self, file_object, file_name, folder_path, last_modified_by="unknown"):
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
                                    "ACL": 'public-read', "ContentType": file_object.content_type, "Metadata": {"last_modified_by": last_modified_by}})

            return {"code": "success", "message": "File uploaded successfully"}
        except ClientError as e:
            print(f"An error occurred uploading the file: {e}")
            return {"code": "error", "message": f"There was an error uploading the file: {e}"}
        finally:
            os.remove(temp.name)
            file_object.file.close()  # new added line

    def replace_file(self, file_object, file_name, folder_path='', last_modified_by="unknown"):
        """Replace and existing file in a specified folder within the bucket."""
        object_name = f'{folder_path}{file_name}' if folder_path else file_name

        temp = NamedTemporaryFile(delete=False)
        try:
            contents = file_object.file.read()
            with open(temp.name, 'wb') as f:
                f.write(contents)
            self.client.upload_file(temp.name, self.bucket_name, object_name, ExtraArgs={
                                    "ACL": 'public-read', "ContentType": file_object.content_type, "Metadata": {"last_modified_by": last_modified_by}})

            return {"code": "success", "message": "File uploaded successfully"}
        except:
            return {"code": "error", "message": "There was an error uploading the file"}
        finally:
            os.remove(temp.name)
            file_object.file.close()  # new added line

    def create_folder(self, folder_name, parent_path="archive/", last_modified_by="unknown"):
        """
        Create a folder in the S3 bucket at the specified path with metadata indicating the user who created it.

        :param folder_name: The name of the new folder.
        :param parent_path: The path where the new folder will be created, ending with a slash.
        :param last_modified_by: The identifier of the user or process creating the folder.
        """
        if not parent_path.endswith('/'):
            parent_path += '/'

        full_folder_path = f"{parent_path}{folder_name}/"

        if self.file_exists(full_folder_path):
            print(f"Folder '{full_folder_path}' already exists in the bucket.")
            return {"code": "folderExists", "message": "Folder already exists"}

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=full_folder_path,
                Metadata={'last_modified_by': last_modified_by}
            )
            return {"code": "success", "message": f"Folder '{folder_name}' created successfully, last modified by {last_modified_by}"}
        except ClientError as e:
            print(f"An error occurred creating the folder: {e}")
            return {"code": "error", "message": f"There was an error creating the folder: {e}"}

    def download_files(self, keys):
        """
        Creates a ZIP archive of the specified files and returns a presigned URL for downloading the archive.

        :param keys: A list of keys representing the files to include in the download.
        """
        # Create a temporary directory to store the files
        with TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "archive.zip")

            # Create a ZIP file
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for key in keys:
                    # Attempt to download each file
                    try:
                        file_path = os.path.join(
                            temp_dir, os.path.basename(key))
                        self.client.download_file(
                            self.bucket_name, key, file_path)
                        zipf.write(file_path, arcname=os.path.basename(key))
                    except ClientError as e:
                        print(f"Error downloading file {key}: {e}")
                        continue  # Skip files that couldn't be downloaded

            # Generate a presigned URL for the ZIP file
            return self.upload_temporary_file(zip_path, "download.zip")

    def upload_temporary_file(self, file_path, s3_key):
        """
        Uploads a temporary file to S3 and generates a presigned URL for accessing it.

        :param file_path: Path to the local file to upload.
        :param s3_key: S3 key under which to store the file.
        """
        try:
            # Upload the ZIP file to S3
            self.client.upload_file(file_path, self.bucket_name, s3_key, ExtraArgs={
                                    "ContentType": "application/zip"})
            # Generate a presigned URL for the ZIP file
            url = self.client.generate_presigned_url('get_object', Params={
                                                     'Bucket': self.bucket_name, 'Key': s3_key}, ExpiresIn=3600)  # URL expires in 1 hour
            return {"url": url}
        except ClientError as e:
            print(f"Error uploading temporary file: {e}")
            return {"error": "Failed to generate download URL"}

    def delete_files(self, keys):
        """
        Delete multiple files or folders (and their contents) from the S3 bucket.

        :param keys: A list of keys representing the files or folders to delete.
        """
        objects_to_delete = []

        for key in keys:
            if key.endswith('/'):  # If the key ends with '/', it's considered a folder
                # List all objects under the folder
                response = self.client.list_objects_v2(
                    Bucket=self.bucket_name, Prefix=key)
                if 'Contents' in response:
                    objects_to_delete.extend(
                        [{'Key': obj['Key']} for obj in response['Contents']])
            else:
                objects_to_delete.append({'Key': key})

        # Delete the objects
        if objects_to_delete:
            try:
                response = self.client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                print("Delete response:", response)
                deleted_items = response.get('Deleted', [])
                errors = response.get('Errors', [])
                if errors:
                    print("Errors occurred while deleting objects:", errors)
                    return {"code": "error", "message": "Some errors occurred while deleting files/folders", "errors": errors}
                return {"code": "success", "message": f"{len(deleted_items)} files/folders deleted successfully"}
            except ClientError as e:
                print(f"An error occurred while deleting files/folders: {e}")
                return {"code": "error", "message": f"There was an error deleting files/folders: {e}"}
        else:
            return {"code": "info", "message": "No files or folders to delete"}

    def delete_file(self, s3_key):
        """
        Deletes a file from the S3 bucket.

        :param s3_key: The S3 key of the file to delete.
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f"Successfully deleted {s3_key} from bucket.")
        except ClientError as e:
            print(f"Failed to delete {s3_key} from bucket: {e}")
