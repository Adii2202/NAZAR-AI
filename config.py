from decouple import config

USERNAME = config("USER")
PASSWORD = config("PASSWORD")
DB_URL = config("DB_URL")
SMS_WEBHOOK = "https://www.fast2sms.com/dev/bulkV2"
API_KEY = config("API_KEY")
AWS_KEY = config("AWS_KEY")
SECRET_KEY_AWS  = config("SECRET_KEY_AWS")
S3_BUCKET_NAME = "railrakshak"
GOOGLE_MAPS_API_KEY = config("GOOGLE_MAPS_API_KEY")