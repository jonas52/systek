# Systek V2

Systek est une TUI d'administration système Linux pensée pour les admins système.

## Points clés

- interface simple et lisible
- monitoring en haut façon dashboard sobre
- mode limité sans sudo
- mode complet avec sudo
- installateur global
- désinstalleur
- commande d'update

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/jonas52/systek/main/install.sh | sudo bash
```

## Utilisation

```bash
systek
```

Mode complet :

```bash
sudo systek
```

## Mise à jour

```bash
sudo systek --update
```

## Désinstallation

```bash
sudo /opt/systek/uninstall.sh
```

## Note importante

Sans sudo, certaines fonctionnalités d'administration sont limitées.
