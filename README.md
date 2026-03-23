# Systek V2.1

Interface TUI d'administration Linux simple, lisible et pensée pour un usage admin système.

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/jonas52/systek/main/install.sh | sudo bash
```

## Utilisation

```bash
systek
sudo systek
```

Sans sudo, certaines fonctionnalités sont limitées.

## Commandes utiles

```bash
systek --doctor
systek --version
sudo systek --update
sudo /opt/systek/uninstall.sh
```

## Utilisation dans la TUI

- Flèches haut/bas : naviguer dans la liste des actions
- Entrée : exécuter l'action sélectionnée
- Taper un numéro dans la barre du bas puis Entrée : exécuter directement l'action
- Pour les actions avec argument : `9 nginx`, `4 htop`, `31 22/tcp`
- `r` : rafraîchir les stats
- `q` : quitter
