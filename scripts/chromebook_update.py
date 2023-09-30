import os
import shutil
import tarfile
import tempfile
import subprocess as sub
from urllib.request import urlopen
from labutil.utils import err, run_cmd

# Get resources path for script
repo_dir = os.path.dirname(os.path.abspath(__file__))
resource_dir = os.path.join(repo_dir, "resources")

# First, make sure we're running on a chromebook
if not os.path.exists("/usr/share/eupnea"):
    err("This script should only be run on Chromebooks running Linux.")


# Define some utility functions

def sudo_copy(src, dst, replace=True):
    # Make sure src exists and dst doesn't exist
    if not os.path.exists(src):
        err("Source file '{0}' does not exist.".format(dst))
    if os.path.exists(dst):
        if replace:
            if not os.path.isdir(dst):
                success = run_cmd(['sudo', 'rm', dst])
                if not success:
                    err("Unable to replace existing file '{0}'.".format(dst))
        else:
            err("File already exists at destination '{0}'.".format(dst))
    # Actually copy the file
    success = run_cmd(['sudo', 'cp', src, dst])
    if not success:
        err("Unable to copy '{0}' to '{1}'.".format(src, dst))

def fetch_source(liburl):
    """Downloads and decompresses the source code for a given library.
    """
    # Download tarfile to temporary folder
    srctar = urlopen(liburl)
    srcfile = liburl.split("/")[-1]
    tmpdir = tempfile.mkdtemp(suffix="labutil")
    outpath = os.path.join(tmpdir, srcfile)
    with open(outpath, 'wb') as out:
        out.write(srctar.read())

    # Extract source from archive
    with tarfile.open(outpath, 'r:gz') as z:
        z.extractall(path=tmpdir)

    return os.path.join(tmpdir, srcfile.replace(".tar.gz", ""))


# Actually run the script

print("\n=== LBRF Chromebook Update Script ===\n")

# Ensure old eupnea RPM repository is disabled
sub.run(
    ['sudo', 'dnf', 'config-manager', '--disable', 'eupnea'],
    stdout=sub.PIPE
)


# Install some useful packages if not already installed
print(" - Installing useful packages...\n")
pkgs = ['neofetch', 'ark', 'sqlitebrowser', 'micro']
run_cmd(['sudo', 'dnf', 'install', '-y'] + pkgs)
print("")


# If keyd isn't installed, download and install it
if not shutil.which("keyd"):
    print(" - Installing keyd keyboard remapper...\n")
    quirks_path = os.path.join(resource_dir, "keyd.quirks")
    conf_path = os.path.join(resource_dir, "cros-lbrf.conf")
    # Add quirks file to fix trackpad palm rejection when using keyd
    quirks_path = os.path.join(resource_dir, "keyd.quirks")
    sudo_copy(quirks_path, "/usr/share/libinput/keyd.quirks")
    # Download and install keyd
    url = "https://github.com/rvaiya/keyd/archive/refs/tags/v2.4.3.tar.gz"
    srcdir = fetch_source(url)
    build_cmds = [
        ['make'],
        ['sudo', 'make', 'install'],
        ['sudo', 'systemctl', 'enable', 'keyd.service'],
        ['sudo', 'systemctl', 'start', 'keyd.service'],
    ]
    os.chdir(srcdir)
    for cmd in build_cmds:
        success = run_cmd(cmd)
        if not success:
            err("Error running command '{0}'.".format(cmd.join(" ")))
    print("")

# Install (or update) custom key mapping for Chromebook
if os.path.exists("/etc/keyd"):
    print(" - Updating custom keyboard mapping...")
    sudo_copy(conf_path, "/etc/keyd/cros-lbrf.conf")
    run_cmd(['sudo', 'keyd', 'reload'])


# If USB with ssh config attached, automatically install it
ssh_path = os.path.expanduser("~/.ssh")
ssh_conf_path = os.path.join(ssh_path, "config")
ssh_conf_path_usb = "/run/media/lbrf/USB360/lbrf_ssh_conf"
if os.path.exists(ssh_conf_path_usb):
    if not os.path.exists(ssh_conf_path):
        print(" - Adding ssh config file...")
        if not os.path.exists(ssh_path):
            os.mkdir(ssh_path)
            os.chmod(ssh_path, 0o700)
        shutil.copyfile(ssh_conf_path_usb, ssh_conf_path)
        os.chmod(ssh_conf_path, 0o600)

print("\n=== Updates Completed Successfully! ===\n")
