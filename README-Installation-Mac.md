# Kinetho pour Mac - installation utilisateur

Choisissez le paquet correspondant a votre processeur dans le menu Apple > A propos de ce Mac :

- Intel Core i5/i7/i9 : paquet `macOS-x86_64`, cible macOS Ventura 13.0 et suivants, dont 13.7.8.
- Apple Silicon M1/M2/M3/M4 et suivants : paquet `macOS-arm64`, cible macOS 14.0 et suivants.

Ces minimums sont des cibles de construction. Le script refuse les dependances qui declarent un minimum plus recent, mais un essai reel reste necessaire sur chaque version de macOS. Un paquet ARM64 ne fonctionne pas sur un Mac Intel.

1. Ouvrez `Kinetho-<version>-macOS-x86_64.dmg` sur Intel, ou `Kinetho-<version>-macOS-arm64.dmg` sur Apple Silicon.
2. Glissez `Kinetho.app` sur le raccourci `Applications`.
3. Ejectez l'image disque et lancez Kinetho depuis Applications.

Python, Tkinter, Pillow et FFmpeg sont integres. N'installez pas Homebrew, Python ou FFmpeg pour utiliser cette application. Une fois le fichier recupere, l'installation et le traitement des fichiers locaux ne necessitent pas de connexion Internet.

Alternative portable : extrayez le ZIP macOS et copiez `Kinetho.app` sur un disque externe compatible macOS. Copiez la .app complete, pas les fichiers internes separement. Les reglages restent sur chaque Mac, pas sur le disque externe.

Cette premiere distribution n'est pas signee avec un certificat Apple Developer ID et n'est pas notarisee. macOS peut la bloquer. Apres avoir verifie la provenance de l'application, consultez Reglages Systeme > Confidentialite et securite pour l'autorisation proposee par macOS. Si votre ordinateur est gere par une organisation, contactez son service informatique. Ne desactivez pas globalement Gatekeeper.

Les points et reglages (dont les derniers dossiers utilises) sont dans `~/Library/Application Support/Kinetho`. Les annotations CSV sont dans le dossier d'images choisi. Pour desinstaller, placez l'application dans la Corbeille ; cela conserve vos donnees.

Kinetho est sous licence MIT. FFmpeg et x264 sont des logiciels separes ; leurs licences, sources et informations de compilation sont incluses dans l'application.