# Kinetho

## Échelle dans l’annotateur de points

Dans un dossier d’images, affichez l’image de référence puis ouvrez le menu **Échelle**
en haut à droite et choisissez **Définir l’échelle**. Dans la même fenêtre, saisissez
la longueur réelle (par exemple `10`, ou `10,5`) et l’unité (`cm`, `mm`, `m`...),
puis cliquez sur les deux extrémités de l’échelle. Elles apparaissent en cyan sans modifier
la liste des points à annoter et sans passer automatiquement à l’image suivante.
Une seule échelle est enregistrée par dossier. **Voir l’image de référence** permet de la
retrouver ; **Définir l’échelle** permet de la remplacer et **Supprimer l’échelle** de la retirer.
Changer d’image ou d’outil, ou appuyer sur Suppr pendant le placement, annule un placement
inachevé et conserve l’échelle précédente.

L’échelle complète est enregistrée immédiatement dans `annotations.csv`, dans les colonnes
`scale_image`, `scale_x1`, `scale_y1`, `scale_x2`, `scale_y2`, `scale_length`, `scale_unit`,
`scale_pixels` et `scale_units_per_pixel`. Ces valeurs sont répétées sur chaque ligne pour
faciliter l’exploitation du tableau. Les coordonnées correspondent aux pixels de l’image
originale, même après zoom ou déplacement ; `scale_pixels` est la distance entre les extrémités
et `scale_units_per_pixel` vaut longueur réelle / distance en pixels.
Dans la fenêtre de définition, choisissez **Pixels** ou **Unité réelle saisie ci-dessus**
pour les coordonnées de sortie `x,y`. En unité réelle, chaque coordonnée est multipliée
par `scale_units_per_pixel` ; `x_pixel,y_pixel` conservent les pixels d’origine pour la reprise.
`coordinate_space` indique `pixel` ou `real` et `coordinate_unit` indique `px` ou l’unité saisie.
L’origine reste en haut à gauche, x vers la droite et y vers le bas, sans rotation des axes.
Les extrémités `scale_x1,scale_y1,scale_x2,scale_y2` restent toujours en pixels.
Le choix est mémorisé avec l’échelle, et remplacer ou supprimer l’échelle recalcule l’export
à partir des pixels d’origine. Sans échelle, une confirmation à la fermeture propose de
revenir à l’annotateur (Non) ou d’enregistrer en pixels et fermer (Oui).
L’échelle est rechargée à la réouverture du dossier. Sans échelle,
le CSV conserve son format à quatre colonnes ; les anciens CSV restent lisibles.
La conversion n’est pertinente pour les autres images que si le cadrage et l’échelle
physique restent identiques. Ouvrir puis enregistrer ce CSV avec une ancienne version de
Kinetho pourrait supprimer les colonnes d’échelle et interpréter les unités réelles comme
des pixels : utilisez uniquement la version mise à jour pour reprendre ces fichiers.

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
