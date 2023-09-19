import os
import boto3
from dotenv import load_dotenv
from fillpdf import fillpdfs
from datetime import datetime
from app.helpers.s3_file_upload import generate_s3_url

load_dotenv()

# Initialize S3 client
s3 = boto3.client('s3')

# Define the directory for static files (relative to the current working directory)
STATIC_DIR = "app/static"
# os.makedirs(STATIC_DIR, exist_ok=True)

contracts_folder = 'uploads/staff/contracts/'

bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")

def fill_pdf_contract(staff):
    staff_name = staff['english_name']
    now = datetime.now()
    formatted_now = now.strftime("_%Y%m%d_%H%M%S")  # Format the current time

    new_contract_name = staff_name.replace(" ", "") + formatted_now + '.pdf'

    s3_original_contract = 'uploads/staff/contracts/mys_contract.pdf'
    s3_new_contract = 'uploads/staff/contracts/' + new_contract_name

    original_file = os.path.join(STATIC_DIR, "mys_contract.pdf")

    fields = fillpdfs.get_form_fields(original_file)
    # fields['staff_name'] = staff_name

    print(fields)

    new_file = os.path.join(STATIC_DIR,new_contract_name)
    
    fillpdfs.write_fillable_pdf(original_file, new_file, {"staff_name": str(staff_name)})

    # Upload the filled PDF to S3 with the new name
    s3.upload_file(original_file, Bucket=bucket_name, Key=s3_new_contract, ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/pdf'})

    # Delete the local file after uploading to S3
    # os.remove(new_file)

    # Generate a presigned URL for the original PDF in S3
    # original_contract_s3_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': s3_original_contract}, ExpiresIn=3600)

    # # Download the original PDF from S3 and save it to the static folder
    # static_contract_path = os.path.join(STATIC_DIR, new_contract_name)
    # with open(static_contract_path, 'wb') as static_contract_file:
    #     s3.download_fileobj(Bucket=bucket_name, Key=s3_original_contract, Fileobj=static_contract_file)

    # # Use fillpdfs library to access the PDF form text fields and fill them
    # contract_fields = fillpdfs.get_form_fields(static_contract_path)
    # contract_fields['staff_name'] = staff_name

    # Fill the PDF and save it with the new name
    # fillpdfs.write_fillable_pdf(static_contract_path, static_contract_path, contract_fields)

    # Upload the filled PDF to S3 with the new name
    # s3.upload_file(static_contract_path, Bucket=bucket_name, Key=s3_new_contract, ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/pdf'})

    # Delete the local file after uploading to S3
    # os.remove(static_contract_path)

    # new_file_url = generate_s3_url(s3_new_contract, "read")

    return [new_file]

    # return [original_contract_s3_url, s3_new_contract]