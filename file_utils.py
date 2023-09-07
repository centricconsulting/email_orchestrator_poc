import os
from datetime import datetime, timedelta


def append_text_to_file(file_name, content):
    try:
        # Open file in "append" mode (if it exists) or "write" mode (if it doesn't exist)
        with open(file_name, 'a', encoding='utf-8') as file:
            file.write(f"{content}\n")
    except IOError:
        print(f"An error occurred while writing to the file: {file_name}")


# Define a function to get the last run time from a file
def get_last_run_time(filename="last_run_time.txt"):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return datetime.strptime(f.read().strip(), '%Y-%m-%d %H:%M:%S')
    return datetime.now() - timedelta(days=1)  # Returns 24 hours ago if file doesn't exist


# Define a function to save the last run time to a file
def save_last_run_time(dt, filename="last_run_time.txt"):
    with open(filename, 'w') as f:
        f.write(dt.strftime('%Y-%m-%d %H:%M:%S'))


def load_file_contents(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding="utf-8") as f:
            return f.read()
    return ""


def delete_files():
    files_to_delete = ["todos.txt", "summary.txt", "token_usage.txt", "errors.txt"]
    for file_name in files_to_delete:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Deleted {file_name}")
        else:
            print(f"{file_name} does not exist")
