#│  ____              _                       ____ ____  
#│ | __ ) _   _      | | ___  _ __   __ _ ___| ___|___ \ 
#│ |  _ \| | | |  _  | |/ _ \| '_ \ / _` / __|___ \ __) |
#│ | |_) | |_| | | |_| | (_) | | | | (_| \__ \___) / __/ 
#│ |____/ \__, |  \___/ \___/|_| |_|\__,_|___/____/_____|
#│        |___/              petitpierre@duck.com
#╰──────────────────────────────────────────────────────╼
import sys
from src.Utils.update import check_update
import subprocess
import src.Main.systek import clear_screen
import src.Utils.installer import *

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        check_update()
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "--install":
        
    else:
        try:
            subprocess.run(['sudo', 'systek'], check=True)
        except subprocess.CalledProcessError as e:
            clear_screen()
            print("│ The systek command is not available. Make sure you are running the script on a compatible system. "), e
            input("╰─╼ Press Enter to continue...")
            sys.exit(1)