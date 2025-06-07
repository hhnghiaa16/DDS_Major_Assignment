# import os
# from dotenv import load_dotenv
# from pydantic_settings import BaseSettings


# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
# dotenv_path = os.path.join(BASE_DIR, ".env")

# if not load_dotenv(dotenv_path):
#     print("load .env failed!")

# class Settings(BaseSettings):
#     TOGETHER_API_KEY: str
    
#     class Config:
#         env_file = dotenv_path
#         env_file_encoding = 'utf-8'
#         extra = "allow"
# settings = Settings()



