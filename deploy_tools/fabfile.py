import logging
import random

from fabric import Connection, task
from invoke import run

logging.basicConfig(level=logging.INFO)


REPO_URL = "https://github.com/b1ru/obey-the-testing-goat.git"


@task
def deploy(c: Connection):
    site_folder = f"/home/{c.user}/sites/{c.host}"
    c.run(f"mkdir -p {site_folder}")
    with c.cd(site_folder):
        _get_latest_source(c)
        _update_virtualenv(c)
        _create_or_update_dotenv(c)
        _update_static_files(c)
        _update_database(c)


def _get_latest_source(c):
    c.run(f"(test -d .git && git fetch) || git clone {REPO_URL} .")
    current_commit = run("git log -n 1 --format=%H").stdout
    c.run(f"git reset --hard {current_commit}")


def _update_virtualenv(c):
    c.run("test -f virtualenv/bin/pip || python3 -m venv virtualenv")
    c.run("./virtualenv/bin/pip install -r requirements.txt")


def _create_or_update_dotenv(c):
    c.run("echo DJANGO_DEBUG_FALSE=y >> .env")
    c.run(f"echo SITENAME={c.host} >> .env")
    current_contents = c.run("cat .env").stdout
    if "DJANGO_SECRET_KEY" not in current_contents:
        new_secret = "".join(
            random.SystemRandom().choices("abcdefghijklmnopqrstuvwxyz0123456789", k=50)
        )
        c.run(f"echo DJANGO_SECRET_KEY={new_secret} >> .env")

def _update_static_files(c):
    c.run("./virtualenv/bin/python manage.py collectstatic --noinput")


def _update_database(c):
    c.run("./virtualenv/bin/python manage.py migrate --noinput")
