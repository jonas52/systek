#│  ____              _                       ____ ____  
#│ | __ ) _   _      | | ___  _ __   __ _ ___| ___|___ \ 
#│ |  _ \| | | |  _  | |/ _ \| '_ \ / _` / __|___ \ __) |
#│ | |_) | |_| | | |_| | (_) | | | | (_| \__ \___) / __/ 
#│ |____/ \__, |  \___/ \___/|_| |_|\__,_|___/____/_____|
#│        |___/              petitpierre@duck.com
#╰──────────────────────────────────────────────────────╼
#import
import argparse
import subprocess
import sys
from src.Utils.update import check_update
from src.Utils.installer import main_install
from src.Main.systek import clear_screen
def launch_systek():
    try:
        subprocess.run(['sudo', 'systek'], check=True)
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ The systek command is not available. Make sure you are running the script on a compatible system. "), e
        input("╰─╼ Press Enter to continue...")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Manage your linux server")
    parser.add_argument("--update", action="store_true", help="Check for updates.")
    parser.add_argument("--install", action="store_true", nargs='?', help="Install the systek")
    args = parser.parse_args()

    if args.update:
        print(":::::::::::::::::::::::::::::::::::::: UPDATE :::::::::::::::::::::::::::::::::::::::::::::")
        subprocess.call(['sleep', '3'])
        check_update()
        launch_systek()
    elif args.install:
        main_install()
        launch_systek()
        return
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()