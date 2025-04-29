import os
import sys
import traceback
import webbrowser
import threading
import time
import urllib.request
from django.core.management import call_command, execute_from_command_line

def start_server():
    call_command('runserver', '127.0.0.1:8000', use_reloader=False)

def wait_for_server(url, timeout=10):
    for _ in range(timeout * 2):  # Tries every 0.5 seconds for 'timeout' seconds
        try:
            urllib.request.urlopen(url)
            return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yugisearcher.settings')
        os.chdir(bundle_dir)

        try:
            import django
            django.setup()

            # Run Migrations
            print("Running database migrations...")
            try:
                call_command('migrate')
                print("Database migrations completed.")
            except Exception as e:
                print(f"Error during migrate: {e}")
                traceback.print_exc()
                sys.exit(1)

            # Start the server in a separate thread
            print("Starting Django development server...")
            server_thread = threading.Thread(target=start_server)
            server_thread.daemon = True
            server_thread.start()

            # Wait for server to be ready, then open browser
            if wait_for_server("http://127.0.0.1:8000", timeout=300):
                webbrowser.open("http://127.0.0.1:8000")
            else:
                print("Warning: Server did not start in time. Browser not opened.")

            # Keep main thread alive
            server_thread.join()

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            sys.exit(1)

    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yugisearcher.settings')
        execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
