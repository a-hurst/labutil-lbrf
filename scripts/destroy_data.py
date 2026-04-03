import os
import sys
import shutil
from click import prompt, secho


def err(txt):
    secho("Error: " + txt, fg="red", bold=True)
    print("\nAborting...")
    sys.exit(1)


# Get database paths and ensure backup db exists

print("")
if not os.path.exists("ExpAssets"):
    err("Not a valid klibs project, unable to remove data!")

db_path = None
backup_path = None
db_names = set()
for item in os.listdir("ExpAssets"):
    # Skip invisible files
    if item[0] == ".":
        continue
    # Get paths of db and backup if they exist
    if "." in item:
        basename, ext = item.split(".", 1)
        if ext == "db":
            db_path = os.path.join("ExpAssets", item)
            db_names.add(basename)
        elif ext == "db.backup":
            backup_path = os.path.join("ExpAssets", item)
            db_names.add(basename)

if not len(db_names) == 1:
    err("Inconsistent database names in ExpAssets: " + str(list(db_names)))

if not backup_path:
    err("No backup database exists, unable to remove data!")

if not db_path:
    err("Unable to find database at " + str(db_path))


# Once we're sure everything's okay, remove the database and replace with the backup

secho(
    "Note: This will permanently delete all data from the last participant!\n",
    fg="red", bold=True
)

resp = prompt(
    "Press 'y' to confirm, or any other key to exit",
    default='n', show_default=False
)
print("\n")
if resp == 'y':
    os.remove(db_path)
    shutil.copyfile(backup_path, db_path)
    secho("Data from last participant destroyed successfully!")
else:
    secho("Aborted, no changes made.")
