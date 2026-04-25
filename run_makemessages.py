import os
import subprocess
import sys

# On s'assure d'utiliser le bon xgettext sans passer par les wrappers .bat qui peuvent poser problème
gettext_path = r"C:\Program Files\gettext-iconv\bin"
os.environ['PATH'] = gettext_path + os.pathsep + os.environ['PATH']

print(f"Extraction des messages avec : {gettext_path}\\xgettext.exe")

cmd = [
    sys.executable, 
    "manage.py", 
    "makemessages", 
    "-l", "fr", 
    "-l", "en", 
    "--ignore", "venv/*",
    "--ignore", "node_modules/*",
    "--ignore", "static/*",
]

result = subprocess.run(cmd, capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("ERREURS :")
    print(result.stderr)

if result.returncode == 0:
    print("Succès ! Compilation des messages...")
    subprocess.run([sys.executable, "manage.py", "compilemessages"])
else:
    print(f"Échec avec le code : {result.returncode}")
