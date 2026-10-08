# Kinetho pour macOS - preparation Apple Silicon

Cette version est en preparation. Machine de test prevue : macOS Tahoe 26.2 et puce M4. Aucun build macOS n'a encore ete construit ou certifie. Le minimum declare est macOS 14.0, a confirmer par les essais ; le build est ARM64 uniquement, pas Intel.

## Version cle en main pour l'utilisateur

L'utilisateur ouvre le DMG, glisse Kinetho.app dans Applications et lance le logiciel. Python, Tkinter, Pillow et FFmpeg sont inclus. Aucune installation de developpement ni Homebrew n'est requise. Voir `README-Installation-Mac.md` pour les instructions destinees a l'utilisateur.

Le ZIP de sources `Kinetho-Mac-sources.zip` n'est pas une application utilisateur. Distribuez le DMG ou le ZIP contenant Kinetho.app, pas ce ZIP de sources.

## Construction automatique via GitHub

1. Commitez et poussez les sources et le workflow `.github/workflows/macos.yml` sur la branche principale.
2. Sur GitHub, ouvrez Actions > Build Kinetho for macOS > Run workflow.
3. Le runner macOS ARM64 construit FFmpeg 8.0.1 et x264 depuis des commits fixes, puis Kinetho.app, le ZIP et le DMG.
4. Le workflow teste l'application compilee avec un dossier utilisateur isole et sans Homebrew dans le PATH, verifie sa signature ad hoc et l'image disque.
5. Si le workflow reussit, telechargez l'artefact `Kinetho-macOS-Apple-Silicon`. L'archive d'artefact contient le DMG et le ZIP utilisateur. Les artefacts expirent apres 30 jours ; publiez les fichiers valides dans une release GitHub pour les conserver durablement.

Aucune release n'est creee automatiquement. Testez le resultat sur le M4 avant publication. Le build utilise FFmpeg et x264 statiques plus les bibliotheques systeme macOS ; leurs sources, licences et la recette de compilation sont incluses dans l'application. Le runner standard est gratuit pour les depots publics selon les conditions GitHub Actions ; les depots prives sont soumis aux quotas du compte.

Pour compiler localement sur le Mac de developpement, installez les Command Line Tools, Python avec Tkinter et pkg-config, puis lancez `python3 scripts/build_ffmpeg_macos.py` avant `python3 scripts/macos.py --build`.

## Premier test depuis les sources

Transferez le dossier complet `Kinetho-Mac` sur votre Mac, dans un dossier local. N'incluez pas les environnements Windows ni les EXE Windows.

1. Installez Python 3.13 pour macOS depuis https://www.python.org/downloads/macos/ ; ce Python inclut Tkinter. Utilisez Python en mode natif ARM64, pas via Rosetta.
2. Installez un FFmpeg macOS pour les essais. Si Homebrew est deja installe, `brew install ffmpeg` convient aux essais depuis les sources. Sur Apple Silicon, assurez-vous que `/opt/homebrew/bin` est dans le PATH du Terminal.
3. Dans Terminal, placez-vous dans le dossier transfere puis lancez :

```bash
cd "/chemin/vers/Kinetho-Mac"
python3 scripts/macos.py
```

Le script verifie Tkinter, cree `.venv-mac` et installe Pillow/PyInstaller. Une connexion Internet est necessaire pour cette preparation, pas pour l'utilisation finale de l'application autonome.

Pour lancer par double-clic, rendez les lanceurs executables depuis Terminal :

```bash
chmod +x scripts/*.command
```

## Construire Kinetho.app autonome

Le FFmpeg Windows fourni dans les autres dossiers ne fonctionne pas sur macOS. Un FFmpeg Homebrew depend habituellement de bibliotheques externes : il est accepte pour les essais, mais refuse par ce premier script de packaging autonome.

Avant la construction, fournissez un FFmpeg ARM64 autonome compatible avec la redistribution GPLv3 et contenant libx264, avec ses vrais documents et sources correspondantes :

```text
Third-party/FFmpeg-Mac/
  bin/ffmpeg
  COPYING.GPLv3.txt
  FFmpeg-GPLv3-Notice.txt
  README.txt
  source/<archive-source-correspondante>.tar.xz
```

La notice et README.txt doivent decrire ce build macOS, sa provenance, sa configuration et sa licence, pas le build Windows. L'archive FFmpeg seule peut ne pas couvrir toutes les obligations des bibliotheques GPL liees : reunir egalement leurs sources et informations requises avant redistribution publique. Ne reutilisez pas les sources 9.0.2 si le binaire macOS correspond a une autre version.

```bash
chmod +x Third-party/FFmpeg-Mac/bin/ffmpeg
python3 scripts/macos.py --build
```

Un autre emplacement peut etre indique via `--ffmpeg-folder "/chemin/vers/FFmpeg-Mac"`. Le script verifie l'architecture, les dependances dynamiques et libx264, puis produit `.build-mac/dist/Kinetho.app`, `release-mac/Kinetho-<version>-macOS-arm64.zip` et le DMG correspondant.

Les outils Apple `lipo`, `otool` et `codesign` sont requis. Si macOS vous demande les Command Line Tools, installez-les via `xcode-select --install`.

La signature ad hoc sert a la coherence locale du bundle ; ce n'est pas une signature Developer ID ni une notarisation Apple. Gatekeeper peut bloquer une application transferee. N'enlevez pas globalement les protections de macOS. Pour une distribution publique sans cette friction, il reste a configurer un certificat Developer ID et la notarisation Apple, avec des secrets stockes dans GitHub Actions, jamais dans le code source.

## Donnees et essais a effectuer

Les points et reglages modifiables sont dans `~/Library/Application Support/Kinetho`. Les dossiers de travail par defaut sont dans son sous-dossier `Workspace`. Les annotations CSV restent dans le dossier des images choisi. Supprimer la `.app` ne supprime pas ces donnees. Le bouton de desinstallation Windows n'est pas affiche sur macOS.

Verifier sur le M4 : langue FR/EN, lancement de l'annotateur depuis l'accueil, sauvegarde/reouverture CSV, glissement et suppression des points, les deux modes, zoom molette/trackpad, recherche de FFmpeg, extraction JPG/PNG, decoupage video et annulation. Verifier ensuite la `.app` sur un autre Mac sans Python ni Homebrew pour confirmer son autonomie. Les tests realises sous Windows ne remplacent pas ces essais Mac.