#│  ____              _                       ____ ____  
#│ | __ ) _   _      | | ___  _ __   __ _ ___| ___|___ \ 
#│ |  _ \| | | |  _  | |/ _ \| '_ \ / _` / __|___ \ __) |
#│ | |_) | |_| | | |_| | (_) | | | | (_| \__ \___) / __/ 
#│ |____/ \__, |  \___/ \___/|_| |_|\__,_|___/____/_____|
#│        |___/              petitpierre@duck.com
#╰──────────────────────────────────────────────────────╼
#import
import sys
import subprocess
from src.Utils.update import check_update
from src.Utils.installer import install_systek
from src.Main.systek import clear_screen

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--update":
            check_update()
        elif sys.argv[1] == "--install":
            install_systek()
            return
    try:
        subprocess.run(['sudo', 'systek'], check=True)
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ The systek command is not available. Make sure you are running the script on a compatible system. "), e
        input("╰─╼ Press Enter to continue...")
        sys.exit(1)

if __name__ == "__main__":
    main()