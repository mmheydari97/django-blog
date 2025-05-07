@echo off
echo Activating virtual environment...
call .blog_venv\Scripts\activate

echo Running migrations...
cd mysite
python manage.py makemigrations
python manage.py migrate

echo Creating superuser (if needed)...
echo If you already have a superuser, press Ctrl+C when prompted for username
python manage.py createsuperuser

echo Starting development server...
python manage.py runserver

pause
