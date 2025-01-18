import hmac
import hashlib
import base64
import boto3
import botocore
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..schemas.user_schema import CreateUserSchema

settings = get_settings()


AWS_REGION_NAME = settings.AWS_REGION_NAME
AWS_COGNITO_APP_CLIENT_ID = settings.AWS_COGNITO_APP_CLIENT_ID
AWS_COGNITO_USER_POOL_ID = settings.AWS_COGNITO_USER_POOL_ID


def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    # Create the message that will be signed (username + client_id)
    message = username + client_id

    # Calculate the HMAC-SHA256 hash using the client secret
    secret_hash = hmac.new(
        client_secret.encode("utf-8"),  # App client secret
        message.encode("utf-8"),  # Username + client_id
        hashlib.sha256,  # HMAC-SHA256
    ).digest()

    # Base64 encode the hash and return it as a string
    return base64.b64encode(secret_hash).decode()


class AWS_Cognito:
    def __init__(self):
        self.client = boto3.client("cognito-idp", region_name=AWS_REGION_NAME)

    def user_signup(self, user: CreateUserSchema):
        response = self.client.sign_up(
            ClientId=AWS_COGNITO_APP_CLIENT_ID,
            Username=user.email,
            Password=user.password,
            # SecretHash='r1umgkh125cffeke0gqou414ufubc3n1j88sisosa567h3ju419',
            UserAttributes=[
                {"Name": "custom:role", "Value": "hotel_owner"},
                {"Name": "custom:company_name", "Value": user.company_name},
            ],
        )

        return response


class AuthService:
    def user_signup(user: CreateUserSchema, cognito: AWS_Cognito):
        try:
            response = cognito.user_signup(user)
        except botocore.exceptions.ClientError as e:
            print(e, "XXXXXXXXXXXXXXXXX")
            if e.response["Error"]["Code"] == "UsernameExistsException":
                raise HTTPException(
                    status_code=409,
                    detail="An account with the given email already exists",
                )
            else:
                raise HTTPException(status_code=500, detail="Internal Server")
        else:
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                content = {
                    "message": "User created successfully",
                    "sub": response["UserSub"],
                }
                return JSONResponse(
                    content=content, status_code=status.HTTP_201_CREATED
                )


def get_aws_cognito() -> AWS_Cognito:
    return AWS_Cognito()


auth_router = APIRouter(prefix="/api/v1/auth")

# USER SIGNUP


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def signup_user(
    user: CreateUserSchema, cognito: AWS_Cognito = Depends(get_aws_cognito)
):
    return AuthService.user_signup(user, cognito)
