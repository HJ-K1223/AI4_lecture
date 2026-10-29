import os
from dotenv import load_dotenv

# .env 읽기
load_dotenv()

# 환경변수 읽어오기
os.getenv("host")
os.getenv("port")
os.getenv("dbname")
os.getenv("user")
os.getenv("password")
