import subprocess
import sys
import os
import time
import platform

def terminate_running_process(exe_name):
    os_type = platform.system().lower()
    try:
        if os_type == 'windows':
            print(f"Checking for running process: {exe_name}.exe")
            subprocess.run(f'taskkill /f /im {exe_name}.exe', check=True, shell=True)
            print(f"Successfully terminated the process: {exe_name}.exe")
        else:
            print(f"Checking for running process: {exe_name}")
            subprocess.run(f'pkill -f {exe_name}', check=True)
            print(f"Successfully terminated the process: {exe_name}")
    except subprocess.CalledProcessError:
        print(f"No running process found for {exe_name}.")
        return True
    except Exception as e:
        print(f"Error terminating process: {e}")
        return False
    return True

def remove_existing_executable(exe_path):
    retries = 5
    os_type = platform.system().lower()

    for i in range(retries):
        try:
            if os.path.exists(exe_path):
                print(f"Attempting to remove existing executable: {exe_path}")
                if os_type == 'windows':
                    subprocess.run(f'del /f /q "{exe_path}"', check=True, shell=True)
                else:
                    subprocess.run(f'rm -f "{exe_path}"', check=True, shell=True)
                print("Executable removed successfully.")
                break
        except PermissionError:
            print(f"Permission denied when trying to delete {exe_path}. Attempt {i+1}/{retries}.")
            time.sleep(2)
        except Exception as e:
            print(f"Error while removing executable: {e}")
            sys.exit(1)
    else:
        print(f"Failed to remove executable after {retries} attempts.")
        sys.exit(1)

def run_pyinstaller():
    output_name = "yugisearcher"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    manage_py_path = os.path.join(script_dir, "manage.py")
    api_templates_path = os.path.join(script_dir, "api", "templates")
    static_path = os.path.join(script_dir, "api", "static")
    dist_dir = script_dir
    exe_path = os.path.join(dist_dir, f"{output_name}.exe")

    terminate_running_process(output_name)
    remove_existing_executable(exe_path)

    for path in [manage_py_path, api_templates_path, static_path]:
        if not os.path.exists(path):
            print(f"Error: Required path not found: {path}")
            sys.exit(1)

    command = [
        "pyinstaller",
        "--onefile",
        "--noconfirm",
        "--name", output_name,
        "--distpath", dist_dir,
        "--workpath", os.path.join(script_dir, "build"),
        "--add-data", f"{static_path}:api/static",
        "--add-data", f"{api_templates_path}:api/templates",
        "--hidden-import=api.management.commands.import_card_inventory",
        "--hidden-import=api.management.commands.import_artworks",
        manage_py_path
    ]


    try:
        print("Running PyInstaller...")
        subprocess.run(command, check=True, stdout=sys.stdout, stderr=sys.stderr, cwd=script_dir)
        print("PyInstaller completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with exit code {e.returncode}")
        print(f"Command: {e.cmd}")
        sys.exit(1)
    except FileNotFoundError:
        print("PyInstaller not found. Is it installed and in your PATH?")
        sys.exit(1)

def cleanup_build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(script_dir, "build")
    spec_file = os.path.join(script_dir, "yugisearcher.spec")

    if os.path.exists(build_dir):
        print("Cleaning up the build directory...")
        retries = 5
        for i in range(retries):
            try:
                if os.name == 'nt':
                    subprocess.run(f'rmdir /S /Q "{build_dir}"', check=True, shell=True)
                else:
                    subprocess.run(f'rm -rf "{build_dir}"', check=True, shell=True)
                print("Build directory cleaned up.")
                break
            except subprocess.CalledProcessError as e:
                print(f"Error deleting build directory (attempt {i+1}/{retries}): {e}")
                time.sleep(1)
        else:
            print("Failed to clean up build directory after multiple attempts.")
    else:
        print("No build directory found. Nothing to clean.")

    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(".spec file cleaned up.")
        except Exception as e:
            print(f"Error deleting .spec file: {e}")
    else:
        print("No .spec file found. Nothing to clean.")

if __name__ == "__main__":
    run_pyinstaller()
    cleanup_build()
    print("Build process finished.")
