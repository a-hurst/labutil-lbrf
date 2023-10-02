import os
import shutil
import tarfile
import tempfile
import subprocess as sub
from urllib.request import urlopen
from click import secho
from labutil.utils import err, run_cmd, cmd_output

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
        srcdir = z.getnames()[0]

    return os.path.join(tmpdir, srcdir)


# Actually run the script

secho("\n=== LBRF Chromebook Update Script ===\n", bold=True, fg='bright_green')

# Install any desired packages
secho(" * Installing useful packages...\n", bold=True)
sub.run(
    # Ensures old eupnea RPM repository is disabled
    ['sudo', 'dnf', 'config-manager', '--disable', 'eupnea'],
    stdout=sub.PIPE
)
pkgs = ['neofetch', 'ark', 'sqlitebrowser', 'micro', 'libusb1-devel']
run_cmd(['sudo', 'dnf', 'install', '-y'] + pkgs)
print("")


# If keyd isn't installed, download and install it
if not shutil.which("keyd"):
    secho(" * Installing keyd keyboard remapper...\n", bold=True)
    quirks_path = os.path.join(resource_dir, "keyd.quirks")
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
    secho(" * Updating custom keyboard mapping...\n", bold=True)
    conf_path = os.path.join(resource_dir, "cros-lbrf.conf")
    sudo_copy(conf_path, "/etc/keyd/cros-lbrf.conf")
    run_cmd(['sudo', 'keyd', 'reload'])


# If USB with ssh config attached, automatically install it
ssh_path = os.path.expanduser("~/.ssh")
ssh_conf_path = os.path.join(ssh_path, "config")
ssh_conf_path_usb = "/run/media/lbrf/USB360/lbrf_ssh_conf"
if os.path.exists(ssh_conf_path_usb):
    if not os.path.exists(ssh_conf_path):
        secho(" * Adding ssh config file...\n", bold=True)
        if not os.path.exists(ssh_path):
            os.mkdir(ssh_path)
            os.chmod(ssh_path, 0o700)
        shutil.copyfile(ssh_conf_path_usb, ssh_conf_path)
        os.chmod(ssh_conf_path, 0o600)


# Install labjack USB driver from source (if not already installed)
has_exodriver = os.path.exists('/usr/local/lib/liblabjackusb.so')
if not has_exodriver:
    secho(" * Installing LabJack USB driver...\n", bold=True)
    # Download and install LabJack driver
    url = "https://github.com/labjack/exodriver/archive/refs/tags/v2.7.0.tar.gz"
    srcdir = fetch_source(url)
    os.chdir(srcdir)
    success = run_cmd(['sudo', './install.sh'])
    if not success:
        err("Error running command '{0}'.".format(cmd.join(" ")))
    print("")


# Fix permissions for using USB serial adapters
user_groups = cmd_output(['groups']).split(" ")
if not "dialout" in user_groups:
    secho(" * Fixing USB serial adapter permissions...\n", bold=True)
    success = run_cmd(['sudo', 'gpasswd', '-a', 'lbrf', 'dialout'])
    if not success:
        err("Unable to add user to dialout group.")
    print("Permissions updated, please restart for the changes to take effect!\n")

secho("=== Updates Completed Successfully! ===\n", bold=True, fg='bright_green')
