# DevOps Automation Scripts 🚀

Welcome to my personal collection of Bash automation scripts! As a backend developer, I built these tools to solve real-world CI/CD pipeline issues and streamline my daily Git and remote server workflows.

## 🛠️ How to Use Bash Scripts

In Linux/macOS, bash scripts (`.sh` files) are text files containing a series of terminal commands. To run them, you first need to give your operating system permission to execute them as an application.

### 1. Make the script executable (One-time setup)
Before running a script for the first time, you must grant it executable permissions using the `chmod` (change mode) command:
```bash
chmod +x script_name.sh
```

### 2. Run the script
Once executable, you can run the script directly from your terminal using `./` (which tells the terminal to look in the current directory):
```bash
./script_name.sh
```

---

## 📂 The Scripts

### 1. `push_to_vps.sh`
**Purpose:** Intelligently pushes only modified files from a local machine to a remote VPS.
**How it works:** Instead of blindly copying an entire project, this script uses `git status --porcelain` and `awk` to extract a clean list of specifically modified files. It then loops through that precise list and uses `scp` to push them to the server quietly in the background.

### 2. `pull_migrations.sh`
**Purpose:** Fixes a common CI/CD gap where database migrations generated on a remote server aren't synced back to version control.
**How it works:** This script dynamically loops through every directory in a Django project. If it detects an app contains a `migrations/` folder, it connects to the VPS via SSH and pulls the generated `00XX_*.py` files back down to the local machine so they can be securely committed to GitHub.

### 3. `clean_branches.sh`
**Purpose:** Cleans up the local Git workspace by forcefully deleting old, merged feature branches.
**How it works:** It uses command substitution `$(...)` and `grep` to filter out `main` and `dev` branches, targeting only branches prefixed with `feature/`, keeping your local repository clean and organized.

---
*Built with ❤️ for better backend workflows.*
