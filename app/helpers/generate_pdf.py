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


def fill_pdf_contract(staff, s3_document_path='uploads/companies/documents/'):
    staff_name = staff['english_name']
    now = datetime.now()
    # formatted_now = now.strftime("_%Y%m%d_%H%M%S")  # Format the current time
    # Format the current time to year only suffix
    formatted_now = now.strftime("_%Y")

    new_contract_name = staff_name.replace(" ", "") + formatted_now + '.pdf'

    # s3_original_contract = 'uploads/staff/contracts/mys_contract.pdf'
    s3_new_contract = s3_document_path + new_contract_name

    original_file = os.path.join(STATIC_DIR, "mys_contract.pdf")

    # contract_fields = fillpdfs.get_form_fields(original_file)
    # change all values from None to ""
    # contract_fields = {k: '' if v is None or "" else v for k, v in contract_fields.items()}

    # convert all values to string
    # contract_fields = {k: '' for k, v in contract_fields.items()}
    # contract_fields['staff_name'] = str(staff_name)

    staff_name = staff['english_name']

    fields = {
        "staff_name": staff_name,
    }

    with TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, new_contract_name)

        # Create a new BytesIO buffer for the filled PDF
        new_contract_buffer = BytesIO()
        fillpdfs.write_fillable_pdf(original_file, new_contract_buffer, fields)

        # Write the filled PDF to the temporary directory
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(new_contract_buffer.getvalue())

        # upload to one drive
        # upload_file_to_onedrive(new_contract_buffer, new_contract_name)

        # Upload the filled PDF to S3 with the new name
        s3.upload_file(temp_file_path, Bucket=bucket_name, Key=s3_new_contract, ExtraArgs={
                       'ACL': 'public-read', 'ContentType': 'application/pdf'})

    s3_read_url = generate_s3_url(s3_new_contract, 'read')

    print(s3_read_url)
    return [s3_read_url]


def fill_pdf_sputum_training(staff, patient, institution, date_entry, s3_document_path='uploads/companies/documents/'):
    now = datetime.now()
    # formatted_now = now.strftime("_%Y%m%d_%H%M%S")  # Format the current time
    # Format the current time to year only suffix
    formatted_now = now.strftime("_%Y")

    new_doc_name = f"{staff['english_name'].replace('', '')}_喀痰吸引の実地研修OJT.pdf"

    original_file = os.path.join(STATIC_DIR, "sputum_training.pdf")

    circle_image = os.path.join(STATIC_DIR, "selectItem.png")

    s3_new_document = s3_document_path + new_doc_name

    # doc_fields = fillpdfs.get_form_fields(original_file)

    # convert all values to string
    # doc_fields = {k: '' for k, v in contract_fields.items()}

    # address is concatenation of prefecture, municipality, town, building
    
    staff_address = staff['prefecture'] + \
        staff['municipality'] + staff['town'] + staff['building']
    staff_address.replace("　", "")

    staff_postal_code = staff['postal_code']
    #add '-' to postal code
    staff_postal_code = f"{staff_postal_code[:3]}-{staff_postal_code[3:]}"
    staff_age = f"{staff['age']}歳"
    # the birth_date is like this, 1973-06-11 it should be formatted to this 1973年6月11日生まれ
    staff_birth_date = datetime.strptime(staff['birth_date'], '%Y-%m-%d')
    # staff_birth_date = staff_birth_date.strftime("%Y年%m月%d日生まれ")
    staff_birth_date = staff_birth_date.strftime("%Y年%m月%d日 ")
    # patient

    patient_address = patient['prefecture'] + \
        patient['municipality'] + patient['town'] + patient['building']

    patient_birth_date = datetime.strptime(patient['birth_date'], '%Y-%m-%d')
    patient_birth_date = patient_birth_date.strftime("%Y年%m月%d日")

    # convert date entry to string and then strftime("%Y年%m月%d日")
    date_entry = datetime.strptime(date_entry, "%Y-%m-%dT%H:%M:%S.%fZ")
    # remove T03:36:51.268Z
    date_entry = date_entry.strftime("%Y年%m月%d日")

    # medical institution
    mi_name = institution['medical_institution_name']
    mi_address = f"{institution['medical_institution_address1']} {institution['medical_institution_address2']}"
    mi_postal_code = institution['medical_institution_postal_code']
    mi_poc = institution['medical_institution_poc']
    mi_phone = institution['medical_institution_phone']
    mi_fax = institution['medical_institution_fax']
    mi_email = institution['medical_institution_email']
    mi_type = institution['medical_institution_type']
    licenses = institution['licenses']
    license_number = institution['license_number']
    date_obtained = institution['date_obtained']
    ojt_implementation_name = institution['ojt_implementation_name']
    physician_name_kanji = institution['physician_name_kanji']
    physician_name_kana = institution['physician_name_kana']
    physician_age = f"{institution['physician_age']}"
    physician_birth_date = datetime.strptime(
        institution['physician_birth_date'], '%Y-%m-%d')
    physician_birth_date = physician_birth_date.strftime("%Y年%m月%d日")
    physician_work = institution['physician_work']
    entity_name = institution['entity_name']
    entity_poc = institution['entity_poc']

    fields_dict = {
        "home_address": staff_address,
        "postal_code": staff_postal_code,
        "english_name": staff['english_name'],
        "japanese_name": staff['japanese_name'],
        "age": staff_age,
        "birth_date": staff_birth_date,
        "patient_name_kanji": patient['name_kanji'],
        "patient_name_kana": patient['name_kana'],
        # "company_section_name": staff['affiliation'],
        "patient_address": patient_address,
        "patient_birth_date": patient_birth_date,
        "current_date": date_entry,     # medical institution
        # ,"medical_institution_license": licenses
        "medical_institution_name": mi_name,
        "medical_institution_address": mi_address,
        "medical_institution_postal_code": mi_postal_code,
        "medical_institution_poc": mi_poc,
        "medical_institution_phone": mi_phone,
        "medical_institution_fax": mi_fax,
        "medical_institution_email": mi_email,
        "medical_institution_type": mi_type,
        "license_number": license_number,
        "date_obtained": date_obtained,
        "ojt_implementation_name": ojt_implementation_name,
        "physician_name_kanji": physician_name_kanji,
        "physician_name_kana": physician_name_kana,
        "physician_age": physician_age,
        "physician_birth_date": physician_birth_date,
        "physician_work": physician_work,
        "entity_name": entity_name,
        "entity_poc": entity_poc


    }

    # print(fields_dict)

    # female coordinates 526.32,183.6
    # male coordinates 496.8, 183.6
    male_coordinates = (496.8, 183.6)
    female_coordinates = (526.32, 183.6)
    # create a variable that set x y coordinates in a list , if staff["gender"] == "男性" set male coordinates else set female
    gender_coordinates = (
        male_coordinates if staff["gender"] == "男性" else female_coordinates)

    with TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, new_doc_name)

        # Create a new BytesIO buffer for the filled PDF
        new_contract_buffer = BytesIO()
        fillpdfs.write_fillable_pdf(
            original_file, new_contract_buffer, fields_dict)

        # Write the filled PDF to the temporary directory
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(new_contract_buffer.getvalue())

            # fillpdfs.place_image(
            #     circle_image, gender_coordinates[0], gender_coordinates[1], new_contract_buffer, temp_file, 1, width=24, height=24)

        # upload to one drive
        # upload_file_to_onedrive(new_contract_buffer, new_doc_name)

        # Upload the filled PDF to S3 with the new name
        s3.upload_file(temp_file_path, Bucket=bucket_name, Key=s3_new_document, ExtraArgs={
                       'ACL': 'public-read', 'ContentType': 'application/pdf'})

    s3_read_url = generate_s3_url(s3_new_document, 'read')

    return [s3_read_url]
