import requests
import subprocess

def check_update(repo_url):
    try:
        response = requests.get(repo_url + "/commits/main")
        response.raise_for_status()  # Raise an exception for HTTP errors
        latest_commit = response.json()[0]["sha"]  # Get the SHA of the latest commit on the main branch
        local_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()  # Get the SHA of the local commit

        if latest_commit != local_commit:
            print("Une nouvelle version est disponible. Mise à jour en cours...")
            subprocess.run(["git", "pull"])  # Met à jour le code depuis GitHub
            print("Mise à jour terminée.")
        else:
            print("Votre script est déjà à jour.")
    except Exception as e:
        print("Erreur lors de la vérification de la mise à jour:", str(e))

if __name__ == "__main__":
    repo_url = "https://github.com/jonas52/systek"
    check_update(repo_url)



######
### python votre_script.py --update
######

__version__ = "1.0.0"
