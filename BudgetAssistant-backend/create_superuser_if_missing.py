import os
from dotenv import load_dotenv

load_dotenv()

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pybackend.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
def main():
    username = os.environ['DJANGO_SUPERUSER_USERNAME']
    User = get_user_model()
    if User.objects.filter(username=username).exists():
        print(f"Superuser {username} already exists.")
    else:
        print(f"Superuser with username {username} does not exist. Creating now...")
        password = os.environ['DJANGO_SUPERUSER_PASSWORD']
        email = os.environ['DJANGO_SUPERUSER_EMAIL']
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser {username} created.")



if __name__ == '__main__':
    print("Starting superuser creation script...")
    try:
        main()
        print("Script completed successfully.")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise
