from tortoise.contrib.fastapi import register_tortoise
import os
from dotenv import load_dotenv

load_dotenv()

# db_uri = os.environ['DB_URI']
    
def initialize_db(app):
    register_tortoise(
        app,
        db_url='postgres://postgres:admin@localhost:5432/kaisha_db',# local postgres
        # db_url='postgres://postgres:admin@postgresql/kaisha_db', #docker pgadmin
        # db_url=db_uri,    
        modules={
            'models': [
                'app.models.user', 
                'app.models.employee',
                'app.models.employee_immigration_details',
                'app.models.employee_relatives',
                'app.models.employee_qualifications',
                'app.models.employee_school_work_history',
                # 'models.user_img',
            ]
        },
        generate_schemas=True,
        add_exception_handlers=True
    )
    print('db initialized')
    