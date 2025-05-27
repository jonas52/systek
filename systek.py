#!/usr/bin/env python3
# installer avant {sudo apt-get install lm-sensors}
#│  ____              _                       ____ ____  
#│ | __ ) _   _      | | ___  _ __   __ _ ___| ___|___ \ 
#│ |  _ \| | | |  _  | |/ _ \| '_ \ / _` / __|___ \ __) |
#│ | |_) | |_| | | |_| | (_) | | | | (_| \__ \___) / __/ 
#│ |____/ \__, |  \___/ \___/|_| |_|\__,_|___/____/_____|
#│        |___/              petitpierre@duck.com
#╰──────────────────────────────────────────────────────╼
# https://www.developmenttools.com/ascii-art-generator/#p=testall&f=Bulbhead&t=
import os
import subprocess
import difflib
import sys
import socket
import fcntl
import struct
import netifaces
import re
import argparse
import shutil

SERVICE_NAME = "systek"
INSTALL_PATH = "/opt/systek"
BIN_PATH = f"/usr/local/bin/{SERVICE_NAME}"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


if os.geteuid() != 0:
    print("╰─╼ This script must be run as superuser (root).")
    sys.exit(1)

# Handle command-line arguments like --update and --remove
parser = argparse.ArgumentParser(description="Systek Command Options")
parser.add_argument('--update', action='store_true', help="Update the script from Git and restart the service")
parser.add_argument('--remove', action='store_true', help="Remove the service and script completely")
args, _ = parser.parse_known_args()



if args.update:
    print("│ Updating the script from Git...")
    if os.path.isdir(os.path.join(SCRIPT_DIR, ".git")):
        subprocess.run(["git", "-C", SCRIPT_DIR, "pull", "origin", "main"], check=True)
        print("│ Update complete.")
        print("│ Restarting the service...")
        subprocess.run(["sudo", "systemctl", "restart", SERVICE_NAME], check=True)
    else:
        print("╰─╼ Not a Git repository. Cannot update.")
    sys.exit(0)

if args.remove:
    print("│ Removing service and script...")
    subprocess.run(["sudo", "systemctl", "stop", SERVICE_NAME])
    subprocess.run(["sudo", "systemctl", "disable", SERVICE_NAME])
    subprocess.run(["sudo", "rm", f"/etc/systemd/system/{SERVICE_NAME}.service"])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    subprocess.run(["sudo", "systemctl", "reset-failed"])
    subprocess.run(["sudo", "rm", "-f", f"/usr/local/bin/{SERVICE_NAME}"])
    print(f"│ Deleting folder: {SCRIPT_DIR}")
    shutil.rmtree(/opt/systek)
    print("╰─╼ Removal complete.")
    sys.exit(0)


def clear_screen():
    os.system('clear')

def restart_service():
    clear_screen()
    print("│ Restart a service ")
    service = input("│ Name of service to restart : ")
    
    try:
        subprocess.check_call(['systemctl', 'restart', service])
        print("│ %s service restart completed successfully" % service)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print(f"│ An error occurred when restarting the service {service} :", e)
        input("╰─╼ Press Enter to continue...")
    except FileNotFoundError:
        clear_screen()
        print("│ The 'systemctl' command is not available. Make sure you are running the script on a compatible system.")
        input("╰─╼ Press Enter to continue...")

def restart_server():
    clear_screen()
    print("│ Server reboot ")
    confirm = input("│ Are you sure you want to restart the server ? (y/N) : ")
    
    if confirm.lower() in ['y', 'yes']:
        print("│ The server will be restarted ")
        print("╰─────────────────────────╼")
        try:
            subprocess.run(['sleep', '2'], check=True)
            subprocess.run(['sudo', 'reboot'], check=True)
        except subprocess.CalledProcessError as e:
            clear_screen()
            print("│ An error occurred while restarting the server "), e
            input("╰─╼ Press Enter to continue...")
        except FileNotFoundError:
            clear_screen()
            print("│ The 'sudo' or 'reboot' command is not available. Make sure you are running the script on a compatible system.")
            input("╰─╼ Press Enter to continue...")
    elif confirm.lower() in ['n', 'no']:
        clear_screen()
        print("│ The server will not be restarted")
        input("╰─╼ Press Enter to continue...")
    else:
        clear_screen()
        print("│ The server will not be restarted")
        input("╰─╼ Press Enter to continue...")

def shutdown_server():
    clear_screen()
    print("│ Server shutdown ")
    confirm = input("│ Are you sure you want to stop the server ? (y/N) : ")

    if confirm.lower() in ['y', 'yes']:
        print("│ The server will be stopped ")
        print("╰─────────────────────────╼")
        try:
            subprocess.run(['sleep', '2'], check=True)
            subprocess.run(['sudo', 'poweroff'], check=True)
        except subprocess.CalledProcessError as e:
            clear_screen()
            print(" │ The server will be stopped "), e
            input("╰─╼ Press Enter to continue...")
        except FileNotFoundError:
            clear_screen()
            print("│ The 'sudo' or 'poweroff' command is not available. Make sure you are running the script on a compatible system.")
            input("╰─╼ Press Enter to continue...")
    elif confirm.lower() in ['n', 'no']:
        print("│ The server will not be stopped")
        input("╰─╼ Press Enter to continue...")
    else:
        print("│ The server will not be stopped")
        input("╰─╼ Press Enter to continue...")

def update_system():
    clear_screen()
    print("│ System update ")

    try:
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'upgrade', '-y'], check=True)
        clear_screen()
        print("│ System update successfully completed")
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ An error occurred while updating the system :"), e
        input("╰─╼ Press Enter to continue...")
    except FileNotFoundError:
        clear_screen()
        print("│ The 'apt-get' command is not available. Make sure you are running the script on a compatible system.")
        input("╰─╼ Press Enter to continue...")

def enable_service():
    clear_screen()
    print("│ Activating a service ")
    service = input("│ Name of service to be activated : ")

    try:
        subprocess.run(['systemctl', 'enable', service], check=True)
        clear_screen()
        print("│ %s service activation successfully completed" % service)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print(f"│ An error has occurred while activating the {service} :", e)
        input("╰─╼ Press Enter to continue...")
    


def disable_service():
    clear_screen()
    print("│ Service deactivation")
    service = input("│ Name of service to be disabled : ")

    try:
        subprocess.run(['systemctl', 'disable', service], check=True)
        print("│ %s service deactivation successfully completed" % service)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print(f"│ An error has occurred while disabling the service {service} :", e)
        input("╰─╼ Press Enter to continue...")

    
def list_services():
    clear_screen()
    print("│ List of services")

    try:
        subprocess.run(['systemctl', 'list-units', '--type=service'], check=True)
        print("│ The list of available services has been successfully completed.")
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ An error occurred while retrieving the list of services :", e)
        input("╰─╼ Press Enter to continue...")

def monitor_service():
    clear_screen()
    print("│ Surveillance d'un service")
    service = input("│ Nom du service à surveiller ex (cron.service) : ")

    subprocess.call(['systemctl', 'status', service])


    print("│ Le monitorage du service %s c'est terminier avec succès" % service)
    input("╰─╼ Press Enter to continue...")

def check_resource_usage():
    clear_screen()
    print("│ Utilisation des ressources ")

    try:
        subprocess.run(['top'], check=True)
        print("│ Le check des resrouces c'est terminier avec succès")
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ Une erreur s'est produite lors de la vérification de l'utilisation des ressources :", e)
        input("╰─╼ Press Enter to continue...")

def check_disk_space():
    clear_screen()
    print("│ Espace disque ")
    try:
        subprocess.run(['df', '-h'], check=True)
        print("│ La vérification de l'espace disque c'est terminier avec succès")
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ Une erreur s'est produite lors de la vérification de l'espace disque :", e)
        input("╰─╼ Press Enter to continue...")
    
def check_network_connections():
    clear_screen()
    print("│ Connexions réseau ")

    try:
        subprocess.run(['netstat', '-tunap'], check=True)
        print("│ La vérification des connexions réseau c'est terminier avec succès")
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ Une erreur s'est produite lors de la vérification des connexions réseau :", e)
        input("╰─╼ Press Enter to continue...")

def check_memory_usage():
    clear_screen()
    print("│ Utilisation de la mémoire RAM ")
    result = subprocess.run(['free', '-m'], capture_output=True, text=True)
    if result.returncode == 0:
        output = result.stdout
        lines = output.split('\n')
        header = lines[0].split()
        values = lines[1].split()
        try:
            total_index = header.index('total')
            used_index = header.index('used')
            print(f"│ Total: {values[total_index+1]} MB")
            print(f"│ Utilisé: {values[used_index+1]} MB")
            print("│ L'affichage de l'ulitisation de la ram c'est terminier avec succès")
            input("╰─╼ Press Enter to continue...")
        except ValueError:
            clear_screen()
            print("│ Les informations de mémoire ne peuvent pas être récupérées.")
            input("╰─╼ Press Enter to continue...")
    else:
        clear_screen()
        print("│ Une erreur s'est produite :", result.stderr)
        input("╰─╼ Press Enter to continue...")

def check_cpu_usage():
    clear_screen()
    print("│ Utilisation du processeur ")
    result = subprocess.run(['top', '-bn', '1'], capture_output=True, text=True)
    if result.returncode == 0:
        output = result.stdout
        lines = output.split('\n')
        cpu_line = None
        for line in lines:
            if line.startswith('%Cpu(s)'):
                cpu_line = line
                break
        if cpu_line is not None:
            cpu_percent_str = re.search(r'(\d+\.\d+)', cpu_line)
            if cpu_percent_str:
                cpu_percent = float(cpu_percent_str.group(1))
                print(f"│ Pourcentage d'utilisation du processeur: {cpu_percent}%")
                print("│ L'affichage du pourcentage du CPU s'est terminé avec succès")
                input("╰─╼ Press Enter to continue...")
            else:
                clear_screen()
                print("│ Les informations d'utilisation du processeur ne peuvent pas être récupérées.")
                input("╰─╼ Press Enter to continue...")
    else:
        clear_screen()
        print("│ Une erreur s'est produite :", result.stderr)
        input("╰─╼ Press Enter to continue...")


def check_cpu_temperature():
    clear_screen()
    print("│ Température du processeur ")
    try:
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
        if result.returncode == 0:
            print(result.stdout)
            print("│ L'affichage de la température du CPU c'est terminier avec succès")
            input("╰─╼ Press Enter to continue...")
        else:
            clear_screen()
            print("│ Une erreur s'est produite :", result.stderr)
            input("╰─╼ Press Enter to continue...")
    except FileNotFoundError:
        clear_screen()
        print("│ La commande 'sensors' n'est pas disponible. Veuillez installer le package 'lm-sensors'.")
        input("╰─╼ Press Enter to continue...")

def mount_drive():
    clear_screen()
    print("│ Montage du lecteur ")
    drive = input("│ Nom du lecteur : ")
    mount_point = input("│ Point de montage : ")
    result = subprocess.run(['sudo', 'mount', drive, mount_point], capture_output=True, text=True)
    if result.returncode == 0:
        print("│ Le lecteur a été monté avec succès.")
        input("╰─╼ Press Enter to continue...")
    else:
        clear_screen()
        print("│ Une erreur s'est produite lors du montage du lecteur :", result.stderr)
        input("╰─╼ Press Enter to continue...")

def list_block_devices():
    clear_screen()
    print("│ Liste des dispositifs de bloc ")
    result = subprocess.run(['lsblk', '-fe7'], capture_output=True, text=True)
    if result.returncode == 0:
        print("│ %s" % result.stdout)
        input("╰─╼ Press Enter to continue...")
    else:
        clear_screen()
        print("│ Une erreur s'est produite lors de la récupération des dispositifs de bloc :", result.stderr)
        input("╰─╼ Press Enter to continue...")

def display_logs():
    # Ouvrir un flux de lecture pour les logs du serveur
    log_stream = subprocess.Popen(['tail', '-f', '/var/log/syslog'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Boucle pour lire les logs en temps réel
    while True:
        output = log_stream.stdout.readline()
        if output == b'' and log_stream.poll() is not None:
            break
        if output:
            print(output.decode(), end='')

    # Fermer le flux de lecture
    log_stream.stdout.close()

def save_logs():
    # Ouvrir un flux d'écriture pour le fichier de logs
    with open('server_logs.log', 'a') as log_file:
        # Ouvrir un flux de lecture pour les logs du serveur
        log_stream = subprocess.Popen(['tail', '-f', '/var/log/syslog'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Boucle pour lire les logs et les écrire dans le fichier de logs
        while True:
            output = log_stream.stdout.readline()
            if output == b'' and log_stream.poll() is not None:
                break
            if output:
                log_file.write(output.decode())

    # Fermer le flux de lecture
    log_stream.stdout.close()
    
def add_packadge():
    clear_screen()
    print("│ Installation d'un packadge")
    package_a_installer = input("│ Nom du packadge à installer : ")
    try:
        subprocess.call(['sudo', 'apt', 'install', package_a_installer, '-y'])
        print("│ L'installation de %s c'est terminier avec succès" % package_a_installer)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ Une erreur s'est produite lors de l'installation du packadge :", e)
        input("╰─╼ Press Enter to continue...")

def remove_packadge():
    clear_screen()
    print("│ Déinstallation d'un packadge")
    package_a_installer = input("│ Nom du packadge à Déinstallation : ")
    try:
        subprocess.call(['sudo', 'apt', 'remove', package_a_installer, '-y'])
        print("│ La déinstallation de %s c'est terminier avec succès" % package_a_installer)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ Une erreur s'est produite lors de la déinstallation du packadge :", e)
        input("╰─╼ Press Enter to continue...")
        
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])    
    
    
def get_ip_address(interface):
    try:
        ip_address = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        return ip_address
    except (KeyError, IndexError):
        return None

def check_ip_address():
    clear_screen()
    try:
        hostname = socket.gethostname()
        interface = "ens33"  # Remplacez par votre interface réseau
        ip_address = get_ip_address(interface)

        if ip_address:
            print(f"│ Nom d'hôte : {hostname}")
            print(f"│ Adresse IP : {ip_address}")
        else:
            print(f"│ Aucune adresse IP trouvée pour l'interface {interface}")

        input("╰─╼ Press Enter to continue...")
    except Exception as e:
        print("│ Une erreur s'est produite lors de la récupération de l'adresse IP :", e)
        input("╰─╼ Press Enter to continue...")

def ufw_status():
    clear_screen()
    print("│ Affichage des paramètre firewall (ufw) ")
    try:
        subprocess.run(['sudo', 'ufw', 'status'], check=True)
        print("│ Mise à jour du systhème terminier avec succès")
        input("╰─╼ Press Enter to continue...")
        clear_screen()
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ Une erreur s'est produite lors de l'affichage du firewall' :"), e
        input("╰─╼ Press Enter to continue...")
    except FileNotFoundError:
        clear_screen()
        print("│ La commande 'ufw' n'est pas disponible. Assurez-vous que vous exécutez le script sur un système compatible.")
        input("╰─╼ Press Enter to continue...")

def enable_ufw():
    clear_screen()
    print("│ Activer le firewall (ufw) ")
    confirm = input("│ Êtes-vous sûr de activer le firewall (peut interompre votre connection ssh) ? (y/N) : ")

    if confirm.lower() in ['y', 'yes']:
        print("│ ufw a été activé")
        print("╰─────────────────────────╼")
        try:
            subprocess.run(['sudo', 'ufw', 'enable'], check=True)
            clear_screen()
        except subprocess.CalledProcessError as e:
            clear_screen()
            print("│ Une erreur s'est produite lors de la activation du firewall "), e
            input("╰─╼ Press Enter to continue...")
        except FileNotFoundError:
            clear_screen()
            print("│ La commande 'sudo' ou 'ufw' n'est pas disponible. Assurez-vous que vous exécutez le script sur un système compatible.")
            input("╰─╼ Press Enter to continue...")
    elif confirm.lower() in ['n', 'no']:
        print("│ Le firewall ne sera pas activer")
        input("╰─╼ Press Enter to continue...")
    else:
        print("│ Le firewall ne sera pas activer")
        input("╰─╼ Press Enter to continue...")

def disable_ufw():
    clear_screen()
    print("│ Désactiver le firewall (ufw) ")
    confirm = input("│ Êtes-vous sûr de Désactiver le firewall (peut interompre votre connection ssh) ? (y/N) : ")

    if confirm.lower() in ['y', 'yes']:
        print("│ ufw a été desactivé")
        print("╰─────────────────────────╼")
        try:
            subprocess.run(['sudo', 'ufw', 'disable'], check=True)
            clear_screen()
        except subprocess.CalledProcessError as e:
            clear_screen()
            print("│ Une erreur s'est produite lors de la désactivation du firewall "), e
            input("╰─╼ Press Enter to continue...")
        except FileNotFoundError:
            clear_screen()
            print("│ La commande 'sudo' ou 'ufw' n'est pas disponible. Assurez-vous que vous exécutez le script sur un système compatible.")
            input("╰─╼ Press Enter to continue...")
    elif confirm.lower() in ['n', 'no']:
        print("│ Le firewall ne sera pas desactivé")
        input("╰─╼ Press Enter to continue...")
    else:
        print("│ Le firewall ne sera pas desactivé")
        input("╰─╼ Press Enter to continue...")

def add_ufw_rules():
    clear_screen()
    print("│ Ajouter un règle au firewall ")
    rules = input("│ Quelle port souhaitez-vous autoriser (/tcp ou /udp), rien correspont au deux?")
    confirm = input("│ Êtes-vous sûr de vouloir ouvrir le port %s ? (y/N) : " % rules)

    if confirm.lower() in ['y', 'yes']:
        print("│ Le port %s a été ouvert" % rules)
        print("╰─────────────────────────╼")
        try:
            subprocess.run(['sudo', 'ufw', 'allow', rules], check=True)
        except subprocess.CalledProcessError as e:
            clear_screen()
            print("│ Une erreur s'est produite lors de l'ajout de la règle "), e
            input("╰─╼ Press Enter to continue...")
        except FileNotFoundError:
            clear_screen()
            print("│ La commande 'sudo' ou 'ufw' n'est pas disponible. Assurez-vous que vous exécutez le script sur un système compatible.")
            input("╰─╼ Press Enter to continue...")
    elif confirm.lower() in ['n', 'no']:
        print("│ La règle ne seras pas ajouter")
        input("╰─╼ Press Enter to continue...")
    else:
        print("│ La règle ne seras pas ajouter")
        input("╰─╼ Press Enter to continue...")

def remove_ufw_rules():
    clear_screen()
    print("│ Supprimer un règle du firewall ")
    print("│ Liste actuelle du firewall ")
    subprocess.run(['sudo', 'ufw', 'status'], check=True)
    rules = input("│ Choisiser la ligne de la règle ?")
    confirm = input("│ Êtes-vous sûr de vouloir supprimer la règle %s ? (y/N) : " % rules)

    if confirm.lower() in ['y', 'yes']:
        print("│ Le port %s a été fermé" % rules)
        print("╰─────────────────────────╼")
        try:
            subprocess.run(['sudo', 'ufw', 'delete', rules], check=True)
        except subprocess.CalledProcessError as e:
            clear_screen()
            print(" │ Une erreur s'est produite lors de la suppression de la règle "), e
            input("╰─╼ Press Enter to continue...")
        except FileNotFoundError:
            clear_screen()
            print("│ La commande 'sudo' ou 'ufw' n'est pas disponible. Assurez-vous que vous exécutez le script sur un système compatible.")
            input("╰─╼ Press Enter to continue...")
    elif confirm.lower() in ['n', 'no']:
        print("│ La règle ne seras pas supprimer")
        input("╰─╼ Press Enter to continue...")
    else:
        print("│ La règle ne seras pas supprimer")
        input("╰─╼ Press Enter to continue...")

def install_cockpit():
    clear_screen()
    print("│ Cockpit installation")
    interface = "ens33"
    ip_address = get_ip_address(interface)
    try:
        subprocess.call(['sudo', 'systemctl', 'stop', 'NetworkManager'])
        subprocess.call(['sudo', 'systemctl', 'disable', 'NetworkManager'])
        subprocess.call(['sudo', 'apt', 'install', 'cockpit', '-y'])
        clear_screen()
        print("│ Cockpit installation successfully completed ")
        print("│ Connect to https://%s:9090 " % ip_address)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ An error occurred while installing the package :", e)
        input("╰─╼ Press Enter to continue...")
def hold_package():
    clear_screen()
    print("│ Package to exclude from updates")
    package_a_exclude = input("│ Name of the package to exclude : ")
    try:
        subprocess.call(['sudo', 'apt-mark', 'hold', package_a_exclude])
        clear_screen()
        print("│ package %s has been successfully excluded" % package_a_exclude)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ Une erreur s'est produite lors de l'exclusion du packadge :", e)
        input("╰─╼ Press Enter to continue...")
def unhold_package():
    clear_screen()
    print("│ Package to include updates")
    package_a_reinclude = input("��� Package name to include : ")
    try:
        subprocess.call(['sudo', 'apt-mark', 'unhold', package_a_reinclude])
        clear_screen()
        print("│ package %s has been successfully included" % package_a_reinclude)
        input("╰─╼ Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        clear_screen()
        print("│ An error occurred while including the package : ", e)
        input("╰─╼ Press Enter to continue...")

def print_menu():
    clear_screen()
    print('''
 ___  _  _  ___  ____  ____  _  _ 
/ __)( \/ )/ __)(_  _)( ___)( )/ )
\__ \ \  / \__ \  )(   )__)  )  ( 
(___/ (__) (___/ (__) (____)(_)\_)          
                    By Jonas52
│ 1 Update the system
│ 2 Add a packadge
│ 3 Delete a packadge
│ 4 Restart the server
│ 5 Stop the server
│ 6 Restart a service
│ 7 Activate a service
│ 8 Disable a service
│ 9 Show list of services
│ 10 Monitor a service
│ 11 Check resource usage
│ 12 Check disk space
│ 13 Check network connections
│ 14 Check IP address
│ 15 Check RAM Usage
│ 16 Check CPU Usage
│ 17 Check CPU temperature (not compatible with a VM)
│ 18 Mount the disc
│ 19 List of connected disks
│ 20 View server logs
│ 21 Back up server logs
│ 22 Display of firewall parameters (ufw)
│ 23 Activate the firewall (ufw)
│ 24 Disable the firewall (ufw)
│ 25 Add a rule to the firewall
│ 26 Delete a rule from the firewall
│ 27 Install cockpit
│ 28 Exclude a packadge from updates
│ 29 Re-include an update packadge
│ q or e Exit
╰──────────────────────────────────────────────────╼
''')


def execute_option(lang):
    try:
        match lang:
            case '1':
                update_system()
            case '2':
                add_packadge()
            case '3':
                remove_packadge()
            case '4':
                restart_server()
            case '5':
                shutdown_server()
            case '6':
                restart_service()
            case '7':
                enable_service()
            case '8':
                disable_service()
            case '9':
                list_services()
            case '10':
                monitor_service()
            case '11':
                check_resource_usage()
            case '12':
                check_disk_space()
            case '13':
                check_network_connections()
            case '14':
                check_ip_address()
            case '15':
                check_memory_usage()
            case '16':
                check_cpu_usage()
            case '17':
                check_cpu_temperature()
            case '18':
                mount_drive()
            case '19':
                list_block_devices()
            case '20':
                display_logs()
            case '21':
                save_logs()
            case '22':
                ufw_status()
            case '23':
                enable_ufw()
            case '24':
                disable_ufw()                
            case '25':
                add_ufw_rules()  
            case '26':
                remove_ufw_rules()
            case '27':
                install_cockpit()
            case '28':    
                hold_package()
            case '29':    
                unhold_package()     
            case '30' | 'EXIT' | 'exit' | 'e' | 'E' | 'Q' | 'q':
                clear_screen()
                quit()
            case _:
                print("╰─╼ Invalid option. Please enter a valid number.")
                subprocess.call(['sleep', '1'])
    except Exception as e:
        print("│ An error has occurred :", str(e))
        input("╰─╼ Press Enter to continue...")

#    elif (confirm.lower() == 'N' or confirm.lower() == 'No' or confirm.lower() == 'no' or confirm.lower() == 'NO' or confirm.lower() == 'n'):

# Boucle principale
while True:
    clear_screen()
    print_menu()
    lang = input("├──╼ Choose an option : ")
    
    if lang == '30':
        clear_screen()
        break
    
    execute_option(lang)

clear_screen()
