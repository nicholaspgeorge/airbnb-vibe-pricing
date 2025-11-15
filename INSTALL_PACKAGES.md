# Package Installation Instructions

The Python data science packages are not currently installed. Here are your options:

## Option 1: Install via Windows PowerShell (Recommended)

Since you're using WSL, the easiest approach is to install packages in Windows and access them from WSL:

### Step 1: Open Windows PowerShell as Administrator
Press `Win + X`, then select "Windows PowerShell (Admin)"

### Step 2: Install Python packages
```powershell
pip install pandas numpy matplotlib seaborn scikit-learn jupyter
pip install xgboost lightgbm shap plotly pyarrow
```

### Step 3: Verify installation
```powershell
python -c "import pandas; print('pandas:', pandas.__version__)"
```

---

## Option 2: Install in WSL (Requires sudo password)

### Step 1: Install pip
```bash
sudo apt-get update
sudo apt-get install python3-pip
```

### Step 2: Install packages
```bash
pip3 install -r requirements.txt
```

### Step 3: Verify
```bash
python3 -c "import pandas; print('✓ pandas installed')"
```

---

## Option 3: Use Conda/Anaconda (Alternative)

If you have Anaconda installed:

```bash
conda install pandas numpy matplotlib seaborn scikit-learn jupyter
conda install -c conda-forge xgboost lightgbm shap plotly pyarrow
```

---

## Quick Test After Installation

Run this to verify everything works:

```bash
python3 test_setup.py
```

---

## What to do NOW

1. Choose one of the installation methods above
2. Install the packages (should take 5-10 minutes)
3. Come back and let Claude know: "Packages installed, let's continue"
4. We'll then run the exploration notebook

---

**Note:** In the meantime, I'll create a basic data analysis script that uses only bash tools so we can get some initial insights right away!
