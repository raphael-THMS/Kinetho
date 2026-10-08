# Kinetho pour Mac - installation utilisateur

Version Apple Silicon : Mac M1, M2, M3, M4 et suivants. macOS 14 ou plus recent est le minimum declare du build ; la compatibilite doit etre confirmee sur les versions proposees. Cette version ne fonctionne pas sur les Mac Intel.

1. Ouvrez `Kinetho-<version>-macOS-arm64.dmg`.
2. Glissez `Kinetho.app` sur le raccourci `Applications`.
3. Ejectez l'image disque et lancez Kinetho depuis Applications.

Python, Tkinter, Pillow et FFmpeg sont integres. N'installez pas Homebrew, Python ou FFmpeg pour utiliser cette application. Une fois le fichier recupere, l'installation et le traitement des fichiers locaux ne necessitent pas de connexion Internet.

Alternative portable : extrayez le ZIP macOS et copiez `Kinetho.app` sur un disque externe compatible macOS. Copiez la .app complete, pas les fichiers internes separement. Les reglages restent sur chaque Mac, pas sur le disque externe.

Cette premiere distribution n'est pas signee avec un certificat Apple Developer ID et n'est pas notarisee. macOS peut la bloquer. Apres avoir verifie la provenance de l'application, consultez Reglages Systeme > Confidentialite et securite pour l'autorisation proposee par macOS. Si votre ordinateur est gere par une organisation, contactez son service informatique. Ne desactivez pas globalement Gatekeeper.

Les points, reglages et dossiers de travail par defaut sont dans `~/Library/Application Support/Kinetho`. Les annotations CSV sont dans le dossier d'images choisi. Pour desinstaller, placez l'application dans la Corbeille ; cela conserve vos donnees.

Kinetho est sous licence MIT. FFmpeg et x264 sont des logiciels separes ; leurs licences, sources et informations de compilation sont incluses dans l'application.