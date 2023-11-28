from tortoise.contrib.fastapi import register_tortoise
import os
from dotenv import load_dotenv

# load_dotenv()

db_uri = os.environ['DB_URI']

    
def initialize_db(app):
    # print(db_uri)
    # print("DB_URI: ", db_uri)
    register_tortoise(
        app,
        # db_url='postgres://postgres:admin@localhost:5432/mys_db',# local postgres
        # db_url='postgres://postgres:admin@postgresql/kaisha_db', #docker pgadmin
        db_url=db_uri,    
        modules={
            'models': [
                'app.models.user',
                'app.models.staff',
                'app.models.company',
                'app.models.japan_addresses',
                'app.models.patient',
                'app.models.medical_institution',
                'app.models.staff_shift',
                'app.models.shift_report',
                'app.models.leave_request',
            ]
        },
        generate_schemas=True,
        add_exception_handlers=True
    )
    print('db initialized')
    