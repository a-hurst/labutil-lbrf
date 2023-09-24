import os
import shutil
import subprocess as sub
from labutil.utils import err

# Get resources path for script
repo_dir = os.path.dirname(os.path.abspath(__file__))
resource_dir = os.path.join(repo_dir, "resources")

# First, make sure we're running on a chromebook
if not os.path.exists("/usr/share/eupnea"):
    err("This script should only be run on Chromebooks running Linux.")


print("\n=== LBRF Chromebook Update Script ===\n")

# Since numlock is permanently stuck on, remap numpad to regular number keys
keyd_confdir = "/usr/share/eupnea/keyboard-layouts"
keyd_conf_old = os.path.join(keyd_confdir, "cros-standard.conf")
keyd_conf_bak = keyd_conf_old + ".bak"
keyd_conf_new = os.path.join(resource_dir, "cros-lbrf.conf")
if os.path.exists(keyd_conf_old):
    if os.path.exists(keyd_conf_bak):
        sub.run(["sudo", "rm", keyd_conf_bak])
    # Rename old config before replacing
    ret = sub.run(["sudo", "mv", keyd_conf_old, keyd_conf_bak])
    ret.check_returncode()
    # Copy new config file from repo to replace old one
    print(" - Updating keyboard layout...")
    ret = sub.run(["sudo", "cp", keyd_conf_new, keyd_conf_old])
    # If copying new config fails, replace old config and raise error
    if ret.returncode != 0:
        sub.run(["sudo", "mv", keyd_conf_old + ".bak", keyd_conf_old])
        ret.check_returncode()
    # Reload new config
    ret = sub.run(["sudo", "keyd", "reload"])
    ret.check_returncode()


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
