#│  ____              _                       ____ ____  
#│ | __ ) _   _      | | ___  _ __   __ _ ___| ___|___ \ 
#│ |  _ \| | | |  _  | |/ _ \| '_ \ / _` / __|___ \ __) |
#│ | |_) | |_| | | |_| | (_) | | | | (_| \__ \___) / __/ 
#│ |____/ \__, |  \___/ \___/|_| |_|\__,_|___/____/_____|
#│        |___/              petitpierre@duck.com
#╰──────────────────────────────────────────────────────╼
import os
import shutil
import subprocess

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

def add_dependencies():
    print_color("Installation des dépendances ...", bcolors.OKBLUE)
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.call(['sudo', 'apt', 'install', 'lm-sensors', '-y'], stdout=devnull, stderr=subprocess.STDOUT)
        print_color("Installation des dépendances terminée.", bcolors.OKGREEN)
    except subprocess.CalledProcessError as e:
        print_color("Une erreur s'est produite lors de l'installation des dépendances :", bcolors.FAIL)
        print_color(str(e), bcolors.FAIL)

def download_from_github(repo_url, destination):
    try:
        print_color("Téléchargement depuis GitHub...", bcolors.OKBLUE)
        subprocess.run(["git", "clone", repo_url, destination], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_color("Installation terminée.", bcolors.OKGREEN)
        print_color("Vous pouvez maintenant utiliser le programme.", bcolors.OKGREEN)
        return True
    except Exception as e:
        print_color(f"Erreur : Échec du téléchargement depuis GitHub - {str(e)}", bcolors.FAIL)
        return False

def install_service():
    # Définir l'URL du dépôt GitHub et le répertoire de destination
    repo_url = "https://github.com/jonas52/systek.git"
    destination_dir = "/opt/systek"
    
    print_color("Bienvenue dans le processus d'installation du programme.", bcolors.HEADER)
    print_color("Cet installateur téléchargera le programme depuis GitHub et l'installera sur votre système.", bcolors.OKBLUE)

    # Vérifier si le répertoire de destination existe
    if os.path.exists(destination_dir):
        print_color("Le répertoire de destination existe déjà.", bcolors.WARNING)
        choice = input("Voulez-vous réinstaller le programme ? (o/n) : ").strip().lower()
        if choice != 'o':
            print_color("Installation annulée.", bcolors.FAIL)
            return False
        else:
            try:
                shutil.rmtree(destination_dir)
            except Exception as e:
                print_color(f"Erreur : Impossible de supprimer le répertoire existant - {str(e)}", bcolors.FAIL)
                return False

    # Télécharger le programme depuis GitHub
    if not download_from_github(repo_url, destination_dir):
        return False

if __name__ == "__main__":
    install_service()