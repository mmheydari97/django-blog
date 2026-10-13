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

## Deploying to PythonAnywhere

On the server, the secret key lives in `mysite/mysite/settings_local.py`. That file is gitignored, so
it never reaches GitHub and `git pull` never touches it. It imports the normal settings and adds the
key on top:
```python
# mysite/mysite/settings_local.py (on the server only, never committed)
from .settings import *  # noqa

SECRET_KEY = '<your secret key>'
```
Don't set `DEBUG = True` in the server copy; `DEBUG` stays off unless you do. Leave `ALLOWED_HOSTS`
alone too, because `settings.py` already allows `mmheydari97.pythonanywhere.com`.

Django only reads this file when `DJANGO_SETTINGS_MODULE` is `mysite.settings_local`. Plain
`mysite.settings` has no key, so every page fails with "The SECRET_KEY setting must not be empty".

### One-time setup (first deploy after the security fixes)

1. **Pull the code.** In a Bash console, go to the repo. If the server copy of `settings.py` still
   has the old secret key edited in, it will clash with the pull, so discard that edit first:
   ```
   git checkout -- mysite/mysite/settings.py
   git pull
   ```
2. **Generate a new secret key.** Don't reuse the old one: the 2019 key is in public git history.
   ```
   python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
   ```
3. **Create `mysite/mysite/settings_local.py`** as shown above, with the key from step 2.
4. **Point Django at it.**
   - Web app: on the Web tab, open the WSGI configuration file and make sure the settings line reads:
     ```python
     os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings_local'
     ```
   - `manage.py` commands in the console: add this to the virtualenv's `postactivate` script (or
     `~/.bashrc`) so they use the same settings:
     ```
     export DJANGO_SETTINGS_MODULE=mysite.settings_local
     ```
5. **Install the new package (`django-axes`) and create its tables:**
   ```
   workon <your-venv>   # or source .../bin/activate
   pip install -r requirements.txt
   cd mysite && python manage.py migrate
   ```
6. **Change the admin password.** Its hash is in the database file that was committed in "v 2025",
   which is public:
   ```
   python manage.py changepassword admin
   ```
7. **Check static files.** On the Web tab, "Static files" should map `/static/` to
   `.../mysite/static`. Run `python manage.py collectstatic` if anything looks unstyled.
8. **Click Reload**, then check:
   - A made-up URL shows a plain "Not Found" page, not the yellow Django debug page.
   - `/post/22/` returns 404 when you're logged out.
   - CSS and the admin pages load normally.
9. **Check the login lockout sees real IPs.** On the live site, log in once with a wrong password,
   then run `python manage.py axes_list_attempts`. It should show your own public IP. If it shows
   an internal 10.x address, every visitor shares one lockout, and the way the IP is read in
   `blog/views.py` (`client_ip`) needs changing.

### Every later deploy

```
git pull
workon <your-venv>
pip install -r requirements.txt
cd mysite && python manage.py migrate
python manage.py collectstatic   # only if CSS or JS changed
```
Then click **Reload** on the Web tab. `settings_local.py` stays as it is.

### Login lockouts

Five failed logins from one IP lock that IP out of `/accounts/login/` and `/admin/` for an hour.
To clear a lockout early (for example if you lock yourself out):
```
python manage.py axes_reset
```

## Usage

1. Log in with the superuser account you created
2. Create new posts from the "New Post" button
3. Posts can be saved as drafts or published immediately
4. Manage comments through the post detail view

## License

This project is licensed under the MIT License - see the LICENSE file for details.
