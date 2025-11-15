# Environment Setup Guide (For All Developers)

This guide explains how every team member can set up the **same development environment** on their local computer.

The goal is:

- Everyone uses **the same Python version**.
- Everyone installs **the same libraries**.
- Everyone configures **the same environment variables**.
- The app runs the same way on all machines.

If you follow this step-by-step, you can assume:  
> “If it runs on my machine, it should run on yours.”

---

## 0. Before You Start

You will need:

- A laptop with:
  - Windows, macOS, or Linux  
  - Internet access
- Permission to install software (or help from whoever manages your computer)

You will use a **terminal**:

- **Windows:** Command Prompt, PowerShell, or Windows Terminal  
- **macOS:** Terminal app  
- **Linux:** Any terminal (GNOME Terminal, Konsole, etc.)

When you see commands like:

```bash
some command here
```

Type them **exactly** into your terminal and press **Enter**.

---

## 1. Install Git

Git is used for version control and to clone the repository.

### 1.1 Windows

1. Download Git from: https://git-scm.com/downloads  
2. Click **“Git for Windows”** and run the installer.  
3. When the installer asks about options:
   - Keep defaults (recommended).
   - Make sure an option like **“Add Git to PATH”** is enabled.

After installing, open a new terminal and run:

```bash
git --version
```

You should see something like:

```text
git version 2.xx.x
```

### 1.2 macOS

Open **Terminal** and run:

```bash
git --version
```

- If Git is already installed, you will see a version number.
- If not, macOS will prompt you to install **Xcode Command Line Tools**.
  - Accept and follow the instructions.
  - After installation, run `git --version` again to confirm.

### 1.3 Linux (Ubuntu/Debian example)

For Ubuntu/Debian-based systems:

```bash
sudo apt update
sudo apt install git
```

Then verify:

```bash
git --version
```

You should see a version string.

---

## 2. Install Python 3.11

The project expects **Python 3.11.x** so everyone shares the same runtime.

### 2.1 Check if Python is already installed

In your terminal, run:

```bash
python --version
```

or:

```bash
python3 --version
```

If you see `Python 3.11.x`, you’re good and can skip to **Section 3**.  
Otherwise, install Python 3.11 using the steps below.

### 2.2 Windows

1. Go to: https://www.python.org/downloads/  
2. Download the latest **Python 3.11.x** for Windows.  
3. Run the installer:
   - On the first screen, check **“Add Python to PATH”** at the bottom.
   - Click **“Install Now”** (default options are fine).

After installation, open a new terminal and run:

```bash
python --version
```

You should see:

```text
Python 3.11.x
```

If your system uses the `py` launcher, you can also check:

```bash
py -3.11 --version
```

### 2.3 macOS

#### Option A – Official Installer

1. Go to: https://www.python.org/downloads/mac-osx/  
2. Download the Python 3.11.x installer for macOS.  
3. Run the installer and follow the steps.

Then verify:

```bash
python3 --version
```

You should see `Python 3.11.x`.

#### Option B – Homebrew (if you already have Homebrew installed)

```bash
brew install python@3.11
```

Then verify:

```bash
python3.11 --version
```

### 2.4 Linux (Ubuntu/Debian example)

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-distutils
```

Then verify:

```bash
python3.11 --version
```

You should see `Python 3.11.x`.

---

## 3. (Optional) Install Docker

Docker is optional but useful for running the app in a standardized container.

1. Download Docker Desktop from:  
   https://www.docker.com/products/docker-desktop
2. Install Docker Desktop and follow the prompts.
3. After installation, open a new terminal and run:

```bash
docker --version
```

You should see something like:

```text
Docker version 27.x.x, build ...
```

If Docker is too heavy for your system, you can skip this.  
Local Python is enough for development.

---

## 4. Choose a Folder for the Project

Pick a folder where you want to keep your development projects.

Examples:

- **Windows:**  
  `C:\Users\<YourName>\dev\`
- **macOS/Linux:**  
  `/Users/<YourName>/dev/` or `/home/<YourName>/dev/`

Create the folder (if it doesn’t exist) and move into it:

```bash
mkdir -p ~/dev
cd ~/dev
```

(Use a different path if you prefer, but be consistent for your own setup.)

---

## 5. Clone the Repository

From your chosen folder (`~/dev`, or similar), run:

```bash
git clone https://github.com/<your-org>/sql-fight-club.git
cd sql-fight-club
```

> Replace `https://github.com/<your-org>/sql-fight-club.git` with the **actual** URL of your GitHub repo.

Check that you’re inside the project folder:

```bash
pwd
```

You should see a path that ends with `sql-fight-club`.

---

## 6. Create a Python Virtual Environment

A **virtual environment** keeps your project dependencies isolated from your system Python.

We’ll create one called `.venv` in the project root.

### 6.1 Create the virtual environment

From the `sql-fight-club` folder:

**Windows:**

```bash
python -m venv .venv
```

**macOS / Linux:**

```bash
python3 -m venv .venv
```

This creates a `.venv` folder in the project.

### 6.2 Activate the virtual environment

You need to activate the environment **every time** you open a new terminal for this project.

**Windows (PowerShell):**

```bash
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```bash
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Once activated, your terminal prompt usually shows `(.venv)` at the beginning.

To confirm which Python you’re using:

```bash
python --version
```

You should see `Python 3.11.x` and it should be coming from `.venv`.

---

## 7. Install Project Dependencies

With the virtual environment **activated** and you inside `sql-fight-club`, install the required Python packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all the libraries the project needs (DuckDB, Streamlit, OpenAI client, etc.).

You can see all installed packages with:

```bash
pip list
```

All team members should end up with similar package lists.

---

## 8. Set Up the `.env` File

The app uses a `.env` file to store configuration like your OpenAI API key.

### 8.1 Copy from the example

At the project root, run:

```bash
cp .env.example .env
```

This creates a new `.env` file based on the example template.

### 8.2 Edit the `.env` file

Open `.env` in a text editor.

**Windows (Notepad):**

```bash
notepad .env
```

**macOS / Linux (nano):**

```bash
nano .env
```

You should see something like:

```text
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4.1-mini
FIGHT_ROUNDS_DEFAULT=6
MAX_ROWS_PREVIEW=20
DUCKDB_DB_PATH=:memory:
```

Replace `your-api-key-here` with your actual OpenAI API key:

```text
OPENAI_API_KEY=sk-...
```

You can keep the other defaults for now.

Important notes:

- Do **not** commit `.env` to Git.
- `.env.example` is safe to commit (no secrets).

Save and close the file:

- In `nano`, press `CTRL + O` → Enter → `CTRL + X`.  
- In Notepad, just save and close.

---

## 9. Sanity Checks: DuckDB, Streamlit, and Python

Make sure your virtual environment is still **activated** (`(.venv)` in the prompt).

### 9.1 Check DuckDB

Run:

```bash
python -c "import duckdb; print(duckdb.__version__)"
```

You should see a version number printed (e.g. `1.1.0` or similar).

### 9.2 Check Streamlit

Run:

```bash
streamlit --version
```

You should see a version number, for example:

```text
Streamlit, version 1.x.x
```

If these both work, your basic environment is good.

---

## 10. Run the Application Locally

From the `sql-fight-club` folder, with the virtual environment active and `.env` configured, run:

```bash
streamlit run app/ui/streamlit_app.py
```

Streamlit will start a local web server and show something like:

```text
  Local URL: http://localhost:8501
```

Open that URL in your browser.

You should see the **SQL Fight Club** interface.

Try:

- Adjusting the number of rounds.  
- Clicking **“Start Fight”**.  
- Watching the SQL queries and results appear round-by-round.

---

## 11. Optional: Run Tests (If Available)

If you have tests set up (e.g. using `pytest`), you can run:

```bash
pytest
```

This will execute all tests in the project.

If they all pass, your environment is correctly configured.

---

## 12. Keeping Everyone in Sync

To keep all team members’ environments aligned:

### 12.1 When dependencies change (new libraries)

1. One person updates `requirements.txt`.  
2. Everyone else pulls the latest code:

   ```bash
   git pull
   ```

3. Then reinstall dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### 12.2 When environment variables change

1. Update `.env.example` with new keys (no secrets).  
2. Each team member updates their own `.env` to match.

### 12.3 Always activate the virtual environment when working

- If `streamlit` or `python` behaves strangely, check that you’re seeing `(.venv)` in the prompt.  
- Reactivate the environment if needed.

---

## 13. Troubleshooting

### 13.1 “python is not recognized”

On Windows, Python might not be on PATH.

- Close and reopen your terminal after installation.  
- Try:

  ```bash
  py -3.11 --version
  ```

If that works, use `py -3.11` instead of `python` in earlier commands.

### 13.2 “ModuleNotFoundError: No module named 'duckdb'” (or similar)

- Make sure the virtual environment is activated.  
- Re-run:

  ```bash
  pip install -r requirements.txt
  ```

### 13.3 Streamlit does not open a browser automatically

This is okay. Just copy the `http://localhost:8501` URL shown in the terminal and paste it into your browser manually.

### 13.4 Permission errors on Windows when activating the venv (PowerShell)

You may need to adjust the PowerShell execution policy:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again:

```bash
.venv\Scripts\Activate.ps1
```
