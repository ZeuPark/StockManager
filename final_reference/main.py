import threading
import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_VOLUME_PATH = os.path.join(BASE_DIR, 'new_volume.py')
MOITUJA_PATH = os.path.join(BASE_DIR, 'moituja.py')

def run_new_volume():
    subprocess.Popen([sys.executable, NEW_VOLUME_PATH])

def run_moituja():
    subprocess.Popen([sys.executable, MOITUJA_PATH])

if __name__ == "__main__":
    t1 = threading.Thread(target=run_new_volume)
    t2 = threading.Thread(target=run_moituja)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
