import boto3
import jwt
from datetime import datetime, timedelta
import json


class LineWorksAPIJWTManager:
    def __init__(self, secret_name, region_name='ap-northeast-1'):
        self.secret_name = secret_name
        self.region_name = region_name
        self.session = boto3.session.Session()
        self.client = self.session.client(
            service_name='secretsmanager', region_name=self.region_name)
        self.jwt_token = None
        self.expires_at = None

    def get_secret(self):
        """Retrieve secret from AWS Secrets Manager"""

        try:
            get_secret_value_response = self.client.get_secret_value(
                SecretId=self.secret_name
            )
        except self.client.exceptions.ResourceNotFoundException:
            print("The requested secret " + self.secret_name + " was not found")
        except self.client.exceptions.InvalidRequestException:
            print("The request was invalid due to:",
                  self.client.exceptions.InvalidRequestException)
        except self.client.exceptions.InvalidParameterException:
            print("The request had invalid params:",
                  self.client.exceptions.InvalidParameterException)
        except self.client.exceptions.InternalServiceError:
            print("An error occurred on the server side:",
                  self.client.exceptions.InternalServiceError)
        else:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)

    def generate_jwt_token(self, client_id, service_account_id, private_key):
        """Generate JWT token"""

        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(hours=24)

        payload = {
            "iss": client_id,
            "sub": service_account_id,
            "aud": "https://auth.worksmobile.com/oauth2/v2.0/token",  # Audience
            "exp": int(expires_at.timestamp()),
            "iat": int(issued_at.timestamp()),
        }

        # Ensure the private_key has correct newlines
        private_key_corrected = private_key.replace("\\n", "\n")

        print(payload)

        # print("private_key_corrected", private_key_corrected)

        jwt_token = jwt.encode(payload, private_key_corrected, algorithm='RS256')
        return jwt_token, expires_at

    def get_jwt_token(self):
        """ Get a valid JWT token, refreshing if necessary """

        if self.jwt_token and self.expires_at > datetime.utcnow():
            return self.jwt_token

        credentials = self.get_secret()
        client_id = credentials['client_id']
        service_account_id = credentials['service_account_id']
        private_key = credentials['private_key'].replace('\\n', '\n')
        self.jwt_token, self.expires_at = self.generate_jwt_token(client_id,
                                                                  service_account_id, private_key)

        return self.jwt_token
