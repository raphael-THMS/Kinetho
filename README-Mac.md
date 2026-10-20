# Kinetho pour macOS - Intel et Apple Silicon

Deux builds distincts sont prepares : Intel x86_64 avec cible macOS 13.0 (Ventura), et Apple Silicon ARM64 avec cible macOS 14.0. La machine de test disponible est un Intel Core i7 sous Ventura 13.7.8. Ces adaptations doivent encore etre compilees et testees sur Mac ; ne considerez pas la compatibilite Ventura comme certifiee.

## Version cle en main pour l'utilisateur

L'utilisateur ouvre le DMG, glisse Kinetho.app dans Applications et lance le logiciel. Python, Tkinter, Pillow et FFmpeg sont inclus. Aucune installation de developpement ni Homebrew n'est requise. Voir `README-Installation-Mac.md` pour les instructions destinees a l'utilisateur.

Le ZIP de sources `Kinetho-Mac-sources.zip` n'est pas une application utilisateur. Distribuez le DMG ou le ZIP contenant Kinetho.app, pas ce ZIP de sources.

## Construction automatique via GitHub

1. Commitez et poussez les sources et le workflow `.github/workflows/macos.yml` sur la branche principale.
2. Sur GitHub, ouvrez Actions > Build Kinetho for macOS > Run workflow.
  Pour rendre les paquets disponibles durablement, cochez `Publish the tested packages as a GitHub pre-release` et conservez le nouveau tag `v0.3.0-macos.1` pour cette version 0.3.0. Sans cette option, le workflow produit seulement des artefacts temporaires.
3. Deux jobs independants construisent FFmpeg 8.0.1 et x264 depuis des commits fixes, puis Kinetho.app, le ZIP et le DMG : Apple Silicon sur `macos-14`, Intel sur `macos-15-intel` avec cible de compilation 13.0.
4. Le workflow teste l'application compilee avec un dossier utilisateur isole et sans Homebrew dans le PATH, verifie sa signature ad hoc et l'image disque.
5. Pour Ventura sur Intel, telechargez `Kinetho-macOS-Intel-Ventura`, contenant les fichiers `macOS-x86_64.dmg` et `.zip`. Pour Apple Silicon, prenez `Kinetho-macOS-Apple-Silicon`, contenant les fichiers `macOS-arm64`. Les artefacts expirent apres 30 jours ; publiez les fichiers valides dans une release GitHub pour les conserver durablement.

Si la publication est cochee, un job separe attend la reussite des deux architectures, cree un brouillon de preversion, charge les quatre paquets, les empreintes SHA-256 et le guide, puis rend la preversion publique apres verification des fichiers. Les paquets sont lies au commit exact du workflow. Un tag deja utilise est refuse ; pour un nouvel essai du meme code, utilisez par exemple `v0.3.0-macos.2`. La release stable Windows reste intacte. Le fichier `scripts/publish_macos.py` utilise le token ephemere fourni par GitHub Actions ; aucun token personnel ne doit etre ajoute au code. Si un chargement echoue, un brouillon peut rester a examiner avant une nouvelle tentative.

Les fichiers seront accessibles dans https://github.com/raphael-THMS/Kinetho/releases une fois ce workflow reussi. Leur presence n'est pas garantie par la simple mise a jour des sources. Ne distribuez pas l'archive `Kinetho-Mac-sources.zip` comme installateur. Comme il s'agit d'une preversion, utilisez la liste des releases plutot que `/releases/latest`, qui peut encore pointer sur Windows.

Le script controle les commandes Mach-O de chaque binaire du bundle et refuse un minimum superieur a la cible, y compris pour Python, Tk et les extensions. Une variable de compilation ne modifie pas les dependances deja compilees : si le controle echoue, il faut remplacer ou recompiler la dependance en cause. Les tests GitHub s'executent sur des macOS plus recents, pas sur Ventura ; testez donc cette preversion sur votre Intel Ventura avant de la considerer comme stable. Le build utilise FFmpeg et x264 statiques plus les bibliotheques systeme macOS ; leurs sources, licences et recette sont incluses.

Pour compiler localement, installez les Command Line Tools, Python avec Tkinter et pkg-config, ainsi que nasm sur Intel, puis lancez `python3 scripts/build_ffmpeg_macos.py` avant `python3 scripts/macos.py --build`. Utilisez un Python natif correspondant a votre processeur. Les environnements et sorties sont separes par architecture ; aucun build Windows n'est modifie.

## Premier test depuis les sources

Transferez le dossier complet `Kinetho-Mac` sur votre Mac, dans un dossier local. N'incluez pas les environnements Windows ni les EXE Windows.

1. Installez Python 3.13 pour macOS depuis https://www.python.org/downloads/macos/ ; ce Python inclut Tkinter. Utilisez un Python x86_64 sur Intel, ARM64 sur Apple Silicon.
2. Installez un FFmpeg macOS pour les essais. Si Homebrew est deja installe, `brew install ffmpeg` convient aux essais depuis les sources. Sur Apple Silicon, assurez-vous que `/opt/homebrew/bin` est dans le PATH du Terminal.
3. Dans Terminal, placez-vous dans le dossier transfere puis lancez :

```bash
cd "/chemin/vers/Kinetho-Mac"
python3 scripts/macos.py
```

Le script verifie Tkinter, cree `.venv-mac/<architecture>` et installe Pillow/PyInstaller. Une connexion Internet est necessaire pour cette preparation, pas pour l'utilisation finale de l'application autonome.

Pour lancer par double-clic, rendez les lanceurs executables depuis Terminal :

```bash
chmod +x scripts/*.command
```

## Construire Kinetho.app autonome

Le FFmpeg Windows fourni dans les autres dossiers ne fonctionne pas sur macOS. Un FFmpeg Homebrew depend habituellement de bibliotheques externes : il est accepte pour les essais, mais refuse par ce premier script de packaging autonome.

Le script `build_ffmpeg_macos.py` prepare les fichiers ci-dessous. Pour utiliser un autre FFmpeg, fournissez un binaire autonome de la meme architecture, compatible avec la redistribution GPLv3 et contenant libx264, avec ses documents et sources correspondantes :

```text
Third-party/FFmpeg-Mac/<architecture>/
  bin/ffmpeg
  COPYING.GPLv3.txt
  FFmpeg-GPLv3-Notice.txt
  README.txt
  source/<archive-source-correspondante>.tar.xz
```

La notice et README.txt doivent decrire ce build macOS, sa provenance, sa configuration et sa licence, pas le build Windows. L'archive FFmpeg seule peut ne pas couvrir toutes les obligations des bibliotheques GPL liees : reunir egalement leurs sources et informations requises avant redistribution publique. Ne reutilisez pas les sources 9.0.2 si le binaire macOS correspond a une autre version.

```bash
python3 scripts/macos.py --build
```

Un autre emplacement peut etre indique via `--ffmpeg-folder "/chemin/vers/FFmpeg-Mac/x86_64"`. Le script verifie l'architecture, les dependances dynamiques et libx264, puis produit `.build-mac/<architecture>/dist/Kinetho.app`, `release-mac/Kinetho-<version>-macOS-<architecture>.zip` et le DMG correspondant.

Les outils Apple `lipo`, `otool` et `codesign` sont requis. Si macOS vous demande les Command Line Tools, installez-les via `xcode-select --install`.

La signature ad hoc sert a la coherence locale du bundle ; ce n'est pas une signature Developer ID ni une notarisation Apple. Gatekeeper peut bloquer une application transferee. N'enlevez pas globalement les protections de macOS. Pour une distribution publique sans cette friction, il reste a configurer un certificat Developer ID et la notarisation Apple, avec des secrets stockes dans GitHub Actions, jamais dans le code source.

## Donnees et essais a effectuer

Les points et reglages modifiables sont dans `~/Library/Application Support/Kinetho`. Kinetho n'y cree pas de dossiers de travail : vous choisissez vos dossiers de videos et d'images, et les derniers dossiers utilises sont memorises dans `kinetho_settings.json`. Les annotations CSV restent dans le dossier des images choisi. Supprimer la `.app` ne supprime pas ces donnees. Le bouton de desinstallation Windows n'est pas affiche sur macOS.

Verifier d'abord sur l'Intel Ventura 13.7.8, puis sur Apple Silicon quand disponible : langue FR/EN, lancement de l'annotateur depuis l'accueil, sauvegarde/reouverture CSV, glissement et suppression des points, les deux modes, zoom molette/trackpad, recherche de FFmpeg, extraction JPG/PNG, decoupage video et annulation. Tester sans Python ni Homebrew pour confirmer l'autonomie. Les tests Windows et les controles de minimum macOS ne remplacent pas ces essais reels.