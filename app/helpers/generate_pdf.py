import os
import boto3
from dotenv import load_dotenv
from fillpdf import fillpdfs
from datetime import datetime
from app.helpers.s3_file_upload import generate_s3_url
from app.helpers.onedrive import upload_file_to_onedrive
from tempfile import TemporaryDirectory
from io import BytesIO
import msal

load_dotenv()

# Initialize S3 client
s3 = boto3.client('s3') 

# Define the directory for static files (relative to the current working directory)
STATIC_DIR = "app/static"
# os.makedirs(STATIC_DIR, exist_ok=True)

contracts_folder = 'uploads/staff/contracts/'

bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")

def save_to_onedrive():
    # app = msal.ConfidentialClientApplication(
    #     client_id, authority=authority,
    #     client_credential=client_secret,
    # )

    # result = None

    # result = app.acquire_token_for_client(scopes=scope)

    pass
    # print(result)


def fill_pdf_contract(staff):
    staff_name = staff['english_name']
    now = datetime.now()
    # formatted_now = now.strftime("_%Y%m%d_%H%M%S")  # Format the current time
    formatted_now = now.strftime("_%Y")  # Format the current time to year only suffix

    new_contract_name = staff_name.replace(" ", "") + formatted_now + '.pdf'

    s3_original_contract = 'uploads/staff/contracts/mys_contract.pdf'
    s3_new_contract = 'uploads/staff/contracts/' + new_contract_name

    original_file = os.path.join(STATIC_DIR, "mys_contract.pdf")

    contract_fields = fillpdfs.get_form_fields(original_file)
    # change all values from None to ""
    # contract_fields = {k: '' if v is None or "" else v for k, v in contract_fields.items()}

    # convert all values to string
    contract_fields = {k: '' for k, v in contract_fields.items()}

    contract_fields['staff_name'] = str(staff_name)

    # print(fields)

    # new_file = os.path.join(STATIC_DIR,new_contract_name)
    
    # fillpdfs.write_fillable_pdf(original_file, new_file, {"staff_name": str(staff_name)})

    # print(contract_fields)

    with TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, new_contract_name)

        # Create a new BytesIO buffer for the filled PDF
        new_contract_buffer = BytesIO()
        fillpdfs.write_fillable_pdf(original_file, new_contract_buffer, {"staff_name": str(staff_name)})

        # Write the filled PDF to the temporary directory
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(new_contract_buffer.getvalue())

        # upload to one drive
        upload_file_to_onedrive(new_contract_buffer, new_contract_name)

        # Upload the filled PDF to S3 with the new name
        s3.upload_file(temp_file_path, Bucket=bucket_name, Key=s3_new_contract, ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/pdf'})

    s3_read_url = generate_s3_url(s3_new_contract, 'read')

    return [s3_read_url]