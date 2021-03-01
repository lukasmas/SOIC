import subprocess

def print_soic():
    print('Welcome in SOIC, work are in progress...')  # Pres


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_soic()
    subprocess.run("python Node.py --sub 5001")
    subprocess.run("python Node.py --pub 5001")


