import sys
import os

# Sæt stier korrekt uanset hvorfra serveren startes:
# - sys.path sikrer at imports finder modulerne i Auth API/
# - os.chdir sikrer at databasefilen oprettes i Auth API/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from auth_rest_api import Auth_rest_api

api = Auth_rest_api()
app = api.app

# Start serveren:
#
#   cd "Auth API"
#   uvicorn main:app --reload
#
# Swagger UI:
#   http://127.0.0.1:8000/docs
