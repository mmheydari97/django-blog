#!/bin/bash
echo "Activating virtual environment..."
source .blog_venv/bin/activate

echo "Running migrations..."
cd mysite
python manage.py makemigrations
python manage.py migrate

echo "Creating superuser (if needed)..."
echo "If you already have a superuser, press Ctrl+C when prompted for username"
python manage.py createsuperuser

echo "Starting development server..."
python manage.py runserver

read -p "Press Enter to continue..."
