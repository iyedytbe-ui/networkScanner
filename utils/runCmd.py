import subprocess

def runCmd(cmd):
    subprocess.run(cmd, shell=True)
    