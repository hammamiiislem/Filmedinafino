import os
import subprocess
import sys
import django
from django.core.management import call_command
import django.core.management.commands.makemessages as mm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

original_popen = mm.popen_wrapper

def debug_popen(args, **kwargs):
    # Print the command being executed
    print("\n" + "="*80)
    print("EXECUTING COMMAND:")
    print(" ".join(args))
    print("="*80 + "\n")
    
    # Run the command and capture output
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print("!!! ERROR DETECTED !!!")
        print(f"Exit Code: {process.returncode}")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    
    # Return a fake process object that the original code expects
    # Actually, we can just return the real process we just ran if we don't need it to be interactive
    # But Django expects a pipe-like object. 
    # Let's just use the original popen but print the args
    return original_popen(args, **kwargs)

mm.popen_wrapper = debug_popen

try:
    print("Starting makemessages...")
    call_command('makemessages', locale=['fr'], ignore_patterns=['venv/*'])
except Exception as e:
    print(f"\nDjango caught an error: {e}")
