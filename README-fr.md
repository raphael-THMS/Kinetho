# Kinetho

Kinetho est une application Windows pour préparer des vidéos, en extraire des images et annoter des points sur celles-ci.

## Installer Kinetho

1. Extrayez `Kinetho-Windows.zip`.
2. Double-cliquez sur `Install Kinetho.bat`.
3. Dans la fenêtre d’installation, choisissez le dossier de destination et indiquez si vous souhaitez créer un raccourci sur le Bureau. Le dossier proposé par défaut est `%LOCALAPPDATA%\Programs\Kinetho`.
4. Cliquez sur **Install** et attendez la fin de la copie. Kinetho ne se lance pas automatiquement.
5. Lancez Kinetho avec le raccourci du Bureau, si vous l’avez choisi, ou ouvrez `Kinetho.exe` dans le dossier d’installation. Python n’a pas besoin d’être installé séparément.
6. Choisissez **Traitement vidéo** pour préparer des vidéos ou extraire des images, ou **Annotateur de points** pour configurer et annoter des points nommés.

Utilisez le menu de langue sur la page d’accueil pour passer du français à l’anglais. Kinetho mémorise votre choix.

Pour **Découper par durée**, saisissez des secondes (`30s`), des minutes (`5m`), des heures (`1h`), `mm:ss` ou `hh:mm:ss`. Un nombre sans unité est interprété comme un nombre de minutes.

Pour supprimer Kinetho et la dépendance FFmpeg intégrée, utilisez **Désinstaller Kinetho** sur la page d’accueil et confirmez. Le raccourci et les fichiers de l’application sont supprimés ; la configuration des points, les vidéos, les images extraites et les annotations sont conservées dans le dossier d’installation.

## Prérequis

- Windows 10 ou Windows 11
- Python n’est pas requis : l’environnement d’exécution est inclus dans `Kinetho.exe`.
- FFmpeg 9.0.2 est inclus dans le paquet ; aucune installation FFmpeg séparée n’est nécessaire.

Le build FFmpeg inclus contient `libx264` et est distribué sous licence GPLv3. Consultez `ffmpeg\FFmpeg-GPLv3-Notice.txt`, la licence et les informations de compilation avant de redistribuer Kinetho.

L’EXE distribué n’est pas signé. Windows SmartScreen ou les règles de sécurité d’une organisation peuvent afficher un avertissement ou le bloquer. Pour une distribution sans avertissement, l’éditeur doit signer le programme avec un certificat de signature de code approuvé.

## Données et dossiers

- `%LOCALAPPDATA%\Programs\Kinetho\` : application installée, FFmpeg, et configuration des noms de points
- `Video edition\Videos_before_modifications\` : vidéos source
- `Videos\` : vidéos traitées
- `Image folders\` : images extraites, regroupées par vidéo source
- `annotations.csv` : annotations enregistrées à côté des images

Les vidéos, images extraites et annotations ne sont pas incluses dans le paquet logiciel. La désinstallation les conserve.

## Licence

Kinetho est distribué sous licence MIT. Copyright (c) 2026 Raphael Thomas. Voir `LICENSE`.

L’exécutable FFmpeg fourni est un programme séparé, distribué sous GPLv3 ; voir `ffmpeg\FFmpeg-GPLv3-Notice.txt`.
