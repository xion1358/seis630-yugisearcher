import os
import sys
import time
import webbrowser
import platform
import requests
import socket
import signal
import subprocess
import argparse
import psycopg2  # Needed to check postgres connection

# This script should be run by developers to test the application while developing
# Users can run the script with "python .\run-dev.py"
# You can use a postgre database by running "python .\run-dev.py -db=postgre"
# Else the default is to use an embedded sqlite file
# The information for this database is defined under .\yugisearcher\yugisearcher\settings.py

def signal_handler(sig, frame):
    """Gracefully handle termination signals."""
    print("\nGracefully shutting down the application...")
    sys.exit(0)

# Register signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination request from the system

def check_database_connection(db_choice):
    """Attempt to check if the database is connectable."""
    if db_choice == "postgres":
        try:
            conn = psycopg2.connect(
                dbname=os.environ.get('POSTGRES_DB', 'yugisearcher'),
                user=os.environ.get('POSTGRES_USER', 'searcher'),
                password=os.environ.get('POSTGRES_PASSWORD', 'seis630'),
                host=os.environ.get('DB_HOST', 'localhost'),
                port=os.environ.get('DB_PORT', '5432'),
                connect_timeout=3
            )
            conn.close()
            print("Successfully connected to Postgres database.")
            return True
        except Exception as e:
            print(f"Failed to connect to Postgres database: {e}")
            return False
    return True  # Assume default sqlite is always available

def run_migrations():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    manage_py_path = os.path.join(script_dir, "manage.py")

    try:
        subprocess.run([sys.executable, manage_py_path, "migrate"], check=True)
        print("Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

def check_server_ready(url="http://127.0.0.1:8000/", timeout=120):
    """Poll the server to check if it's up and running."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            time.sleep(1)
    return False

def open_browser_cross_platform(url):
    system = platform.system().lower()
    release = platform.release().lower()

    try:
        if "microsoft" in release and "linux" in system:
            subprocess.run(["cmd.exe", "/c", "start", "", url])
        elif system == "windows":
            webbrowser.open(url)
        elif system == "darwin":  # macOS
            subprocess.run(["open", url])
        elif system == "linux":
            subprocess.run(["xdg-open", url])
        else:
            webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print(f"Please open this link manually: {url}")

def check_port_in_use(port=8000):
    """Check if the specified port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('127.0.0.1', port))
        return result == 0  # 0 means the port is in use

def main():
    parser = argparse.ArgumentParser(description="Run the Django application with optional database choice.")
    parser.add_argument('-db', type=str, help="Specify the database choice (e.g., 'postgres').", default="default")
    args = parser.parse_args()

    db_choice = args.db

    # Check the database connection if not default
    if db_choice != "default" and not check_database_connection(db_choice):
        print("Falling back to default (sqlite) database.")
        db_choice = "default"

    # Set environment variable for Django settings to pick up
    os.environ['DB_CHOICE'] = db_choice

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    manage_py_path = os.path.join(script_dir, "manage.py")
    url = "http://127.0.0.1:8000/"

    sys.stdout.write(f'Starting server with database: {db_choice}\n')

    try:
        run_migrations()

        # Check if the port is already in use
        if check_port_in_use(8000):
            print("Port 8000 is already in use. Please stop the server or choose another port.")
            return

        command = [sys.executable, manage_py_path, "runserver", "--noreload"]

        # Run the Django server and capture output directly in the parent process
        process = subprocess.Popen(command, stdout=sys.stdout, stderr=sys.stderr)

        # Check if the server is up and running
        if check_server_ready():
            open_browser_cross_platform(url)
        else:
            print("Server did not start within the timeout period.\nPlease wait for server to launch and then manually go to", url)

        # Wait for the server process to finish (handle termination)
        process.wait()

    except subprocess.CalledProcessError as e:
        print("\nFailed to start server:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
