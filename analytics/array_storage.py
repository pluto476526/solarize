import json
import os
from django.conf import settings

# Base directory for all user array data
BASE_ARRAY_DIR = os.path.join(settings.BASE_DIR, "array_data")
os.makedirs(BASE_ARRAY_DIR, exist_ok=True)


def _get_user_dir(user):
    """Return the directory path for a specific user."""
    user_dir = os.path.join(BASE_ARRAY_DIR, f"user_{user.id}")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def _get_file_path(user, filename):
    """Return full file path for a specific user and filename."""
    user_dir = _get_user_dir(user)
    return os.path.join(user_dir, filename)


# ------------------ SAVE / LOAD ------------------

def save_array_file(user, filename, array_names):
    """Save array data to a file within the user’s directory."""
    file_path = _get_file_path(user, filename)
    with open(file_path, "w") as f:
        json.dump(array_names, f)


def load_array_file(user, filename):
    """Load a specific array file from a user’s directory."""
    file_path = _get_file_path(user, filename)
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as f:
        return json.load(f)


# ------------------ FILE MANAGEMENT ------------------

def list_user_files(user):
    """List all array files for the given user."""
    user_dir = _get_user_dir(user)
    return sorted(os.listdir(user_dir))


def delete_array_file(user, filename):
    """Delete a specific array file for the given user."""
    file_path = _get_file_path(user, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

