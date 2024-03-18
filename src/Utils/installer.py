#│  ____              _                       ____ ____  
#│ | __ ) _   _      | | ___  _ __   __ _ ___| ___|___ \ 
#│ |  _ \| | | |  _  | |/ _ \| '_ \ / _` / __|___ \ __) |
#│ | |_) | |_| | | |_| | (_) | | | | (_| \__ \___) / __/ 
#│ |____/ \__, |  \___/ \___/|_| |_|\__,_|___/____/_____|
#│        |___/              petitpierre@duck.com
#╰──────────────────────────────────────────────────────╼
import subprocess
import os
import shutil
import sys

# Color codes for output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_color(msg, color=bcolors.OKBLUE):
    print(color + msg + bcolors.ENDC)

def download_from_github(repo_url, destination):
    try:
        subprocess.run(["git", "clone", repo_url, destination])
        return True
    except Exception as e:
        print_color(f"Error: Failed to download from GitHub - {str(e)}", bcolors.FAIL)
        return False

def install_service():
    # Define GitHub repository URL and destination directory
    repo_url = "https://github.com/jonas52/systek.git"
    destination_dir = "/opt/systek"

    print_color("Welcome to the program installation process.", bcolors.HEADER)
    print_color("This installer will download the program from GitHub and install it on your system.", bcolors.OKBLUE)

    # Check if the destination directory exists
    if os.path.exists(destination_dir):
        print_color("Destination directory already exists.", bcolors.WARNING)
        choice = input("Do you want to reinstall the program? (y/n): ").strip().lower()
        if choice != 'y':
            print_color("Installation aborted.", bcolors.FAIL)
            return False
        else:
            try:
                shutil.rmtree(destination_dir)
            except Exception as e:
                print_color(f"Error: Failed to remove existing directory - {str(e)}", bcolors.FAIL)
                return False

    # Download the program from GitHub
    print_color("Downloading from GitHub...", bcolors.OKBLUE)
    if not download_from_github(repo_url, destination_dir):
        return False

    # Proceed with installation
    print_color("Installation completed.", bcolors.OKGREEN)
    print_color("You can now use the program.", bcolors.OKGREEN)
    return True

if __name__ == "__main__":
    install_service()
