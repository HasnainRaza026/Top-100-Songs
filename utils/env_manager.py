from dotenv import load_dotenv, set_key
import os

def load_env_variables():
    load_dotenv()
    return {
        "ACCESS_TOKEN": os.getenv("ACCESS_TOKEN"),
        "REFRESH_TOKEN": os.getenv("REFRESH_TOKEN"),
        "CLIENT_ID": os.getenv("CLIENT_ID"),
        "CLIENT_SECRETE": os.getenv("CLIENT_SECRETE"),
        "USER_ID": os.getenv("USER_ID"),
    }

def save_env_variable(key, value):
    set_key(".env", key, value)
