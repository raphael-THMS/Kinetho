# Kinetho pour Windows / Kinetho for Windows

## Demarrage

Double-cliquez sur **Kinetho.exe**. Python et FFmpeg sont inclus.
Pour une utilisation portable, copiez le dossier complet sur votre disque externe,
pas seulement l'EXE. Fermez Kinetho avant d'ejecter le disque.

Choisissez vos videos et dossiers de sortie dans l'application.
Kinetho memorise ces choix. Les annotations restent dans le dossier des images.

## Organisation

- `data` : noms de points (`points.txt`), langue et dossiers memorises
  (`kinetho_settings.json`). Conservez ce dossier lors des mises a jour.
- `docs` : guides complets en francais et en anglais, licence MIT.
- `_internal` : environnement Python, ressources graphiques et desinstalleur.
- `ffmpeg` : outils video et informations de licence GPLv3.

Ne deplacez pas ces dossiers separement de Kinetho.exe.
Le disque doit autoriser l'ecriture des reglages et disposer d'assez de place
dans les dossiers de sortie choisis.

Windows 10 ou 11 requis. Pour macOS, utilisez la version Mac.
L'EXE n'est pas signe : si SmartScreen ou un antivirus gere bloque son lancement,
contactez votre service informatique. Ne contournez pas les restrictions du poste.

## Quick start

Double-click **Kinetho.exe**. Python and FFmpeg are included.
For portable use, copy the entire folder, not just the EXE.
Keep `data`, `docs`, `_internal` and `ffmpeg` beside it.
Choose your input and output folders in the application; Kinetho remembers them.
Annotations stay beside your images. Preserve `data` when updating.

Full guides: `docs\README-fr.md` and `docs\README.md`.
Licenses: `docs\LICENSE` (Kinetho, MIT) and the notices in `ffmpeg` (GPLv3).
