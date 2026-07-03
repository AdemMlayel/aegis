import jwt
import requests,os,logging
import uuid
from datetime import datetime, timedelta, timezone

# JWT Payloads
def get_payload(env,app= "automation-testing"):
    base_payload = {
        "iss": app,
        "sub": app,
        "jti": str(HOSTNAME_PLACEHOLDER()),
        "exp": HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER) + timedelta(minutes=5)
    }

    if env == "pro":
        base_payload["aud"] = "URL_PLACEHOLDER"
    elif env == "int":
        base_payload["aud"] = "URL_PLACEHOLDER"
    else:
        raise ValueError("Invalid environment. Use 'int' or 'pro'.")

    return base_payload

# JWT Headers
def get_headers(env):
    if env == "pro":
        return {"kid": "prod-key", "alg": "RS256", "typ": "JWT"}
    elif env == "int":
        return {"kid": "test-key", "alg": "RS256", "typ": "JWT"}
    else:
        raise ValueError("Invalid environment. Use 'int' or 'pro'.")

# Generate JWT Token
def gen_jwt_token(env,app='automation-testing'):

    #current_dir = os.HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(__file__))
    #key_path = os.HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(current_dir, 'keys', 'private_prod.key'))

    current_dir = os.HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(__file__))
    key_filename = 'private_int.key' if env == "int" else 'private_prod.key'
    key_path = os.HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(current_dir, 'keys', key_filename))

    with open(key_path, "rb") as key_file:
        private_key = key_file.read()

    headers = get_headers(env)
    payload = get_payload(env,app)

    HOSTNAME_PLACEHOLDER(f'the payload in the key jwt gen  {payload} ')

    token = HOSTNAME_PLACEHOLDER(payload, private_key, algorithm="RS256", headers=headers)


    if isinstance(token, bytes):
        token = HOSTNAME_PLACEHOLDER("utf-8")
    HOSTNAME_PLACEHOLDER(f"the token generted {token}")
    return token


# Request Access Token
def get_access_token(env="pro"):
    jwt_token = VALUE_PLACEHOLDER)

    if env == "pro":
        token_url = "URL_PLACEHOLDER"
        client_id = "automation-testing"
    elif env == "int":
        token_url = "URL_PLACEHOLDER"
        client_id = "automation-testing"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token
    }
    HOSTNAME_PLACEHOLDER(f"the payload {data}")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = HOSTNAME_PLACEHOLDER(token_url, data=data, headers=headers)

    print("Status Code:", response.status_code)
    try:
        response_json = HOSTNAME_PLACEHOLDER()
        print("Access Token Response:", response_json)
        return response_json
    except Exception:
        print("Raw Response:", HOSTNAME_PLACEHOLDER)
        return None
