# Modern Django Blog

A modern blog application built with Django 5 and Bootstrap 5.

## Features

- User authentication
- Create, edit, and delete blog posts
- Draft posts
- Comment system with approval
- Responsive design
- Modern UI with Bootstrap 5

## Requirements

- Python 3.12
- Django 5.0+
- Other dependencies listed in requirements.txt

## Installation

### Using uv (Recommended)

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/blog.git
   cd blog
   ```

2. Create a virtual environment using uv:
   ```
   uv venv .blog_venv --python=3.12
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     .blog_venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source .blog_venv/bin/activate
     ```

4. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```

### Using pip

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/blog.git
   cd blog
   ```

2. Create a virtual environment:
   ```
   python -m venv .blog_venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     .blog_venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source .blog_venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

### Using the provided scripts

- Windows:
  ```
  run_local.bat
  ```

- macOS/Linux:
  ```
  chmod +x run_local.sh
  ./run_local.sh
  ```

### Manual setup

1. Activate the virtual environment (if not already activated)

2. Navigate to the project directory:
   ```
   cd mysite
   ```

3. Apply migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

6. Access the application at http://localhost:8000

## Usage

1. Log in with the superuser account you created
2. Create new posts from the "New Post" button
3. Posts can be saved as drafts or published immediately
4. Manage comments through the post detail view

## License

This project is licensed under the MIT License - see the LICENSE file for details.
