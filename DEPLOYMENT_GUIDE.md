# Streamlit App Deployment Guide

**For:** Sharing with team members and project submission
**Deadline:** November 17, 2025

---

## ⚡ Option 1: Streamlit Community Cloud (RECOMMENDED)

**Best for:** Permanent, free hosting with custom URL
**Time to deploy:** 10-15 minutes
**Cost:** FREE
**URL:** `your-app-name.streamlit.app`

### Prerequisites

1. ✅ GitHub account (you probably have this)
2. ✅ Your code in a GitHub repository
3. ✅ Streamlit Community Cloud account (free)

### Step 1: Prepare Your Repository

Your app needs to be in a **public** GitHub repository. Let's check what needs to be committed:

```bash
# Navigate to your project
cd /mnt/c/Users/Nicholas/adv_ba_project

# Check git status
git status

# If not a git repo yet, initialize it
git init
```

### Step 2: Create `.gitignore` for Large Files

⚠️ **IMPORTANT**: GitHub has a 100MB file size limit. Your model files and data are too large!

**Solution**: Use **Git LFS** (Large File Storage) OR host models separately.

Create `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Data (too large for GitHub)
data/*/raw/listings_*.csv
data/*/raw/reviews_*.csv

# Model files (use Git LFS or external hosting)
*.pkl
*.joblib
*.h5
*.pt

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Streamlit
.streamlit/secrets.toml
```

### Step 3: Handle Large Model Files

You have 3 options:

#### **Option A: Git LFS (Large File Storage)** ⭐ RECOMMENDED

```bash
# Install Git LFS
git lfs install

# Track .pkl files
git lfs track "*.pkl"
git lfs track "*.parquet"

# Add .gitattributes
git add .gitattributes
```

**Pros:** Models stored with code
**Cons:** 1GB free bandwidth/month (should be enough for team testing)

#### **Option B: Google Drive/Dropbox Links**

1. Upload models to Google Drive
2. Get shareable links
3. Add download logic to app startup
4. Store links in Streamlit secrets

**Pros:** No GitHub limits
**Cons:** Slower first load, more setup

#### **Option C: Hugging Face Model Hub**

Upload models to Hugging Face, download in app.

**Pros:** Built for ML models
**Cons:** Extra account needed

### Step 4: Create `requirements.txt`

Already exists, but verify it includes:

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.14.0
scikit-learn>=1.3.0
xgboost>=2.0.0
folium>=0.14.0
branca>=0.6.0
pyarrow>=12.0.0
```

### Step 5: Test Locally First

```bash
cd app
source ../venv/bin/activate
streamlit run Home.py
```

Verify everything works!

### Step 6: Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Deploy vibe-aware pricing app for MIS5460 project"

# Create GitHub repo (go to github.com, create new repo)
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/vibe-pricing-app.git
git branch -M main
git push -u origin main
```

### Step 7: Deploy to Streamlit Community Cloud

1. **Go to:** https://share.streamlit.io/
2. **Sign in** with GitHub
3. **Click** "New app"
4. **Fill in:**
   - Repository: `YOUR_USERNAME/vibe-pricing-app`
   - Branch: `main`
   - Main file path: `app/Home.py`
   - App URL: `vibe-pricing` (or your choice)
5. **Click** "Deploy!"

**Wait 5-10 minutes** for initial build.

### Step 8: Share with Team

Your app will be available at:
```
https://vibe-pricing.streamlit.app
```

**Send this link to your teammates!**

---

## ⚡ Option 2: ngrok (Quick Temporary Solution)

**Best for:** Immediate sharing (next 2-3 hours)
**Time to deploy:** 2 minutes
**Cost:** FREE
**URL:** Random `xxx.ngrok.io` (changes each time)

### Quick Setup

```bash
# 1. Install ngrok
# Download from: https://ngrok.com/download
# Or on Windows: winget install ngrok

# 2. Sign up for free account at ngrok.com
# Get your authtoken

# 3. Configure ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN

# 4. Start your Streamlit app locally
cd /mnt/c/Users/Nicholas/adv_ba_project/app
source ../venv/bin/activate
streamlit run Home.py --server.port 8501

# 5. In a NEW terminal, start ngrok tunnel
ngrok http 8501
```

**You'll get a URL like:** `https://abc123.ngrok.io`

**Send this to your teammates!**

⚠️ **Limitations:**
- URL changes each time you restart
- Only works while your computer is on
- Free tier has limits on connections
- Tunnel closes when you close terminal

**Good for:** Quick demos, testing today
**Not good for:** Permanent sharing, grading

---

## 🚀 Option 3: Hugging Face Spaces (Alternative Free Hosting)

**Best for:** ML apps, alternative to Streamlit Cloud
**Time to deploy:** 15-20 minutes
**Cost:** FREE
**URL:** `huggingface.co/spaces/YOUR_USERNAME/vibe-pricing`

### Quick Setup

1. **Create account:** https://huggingface.co/
2. **Create new Space:**
   - Go to Spaces → Create new Space
   - Choose: Streamlit SDK
   - Name: `vibe-pricing`
   - Visibility: Public
3. **Clone the Space repo:**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/vibe-pricing
   ```
4. **Copy your app files:**
   ```bash
   cp -r app/* vibe-pricing/
   cp requirements.txt vibe-pricing/
   cp -r data vibe-pricing/  # May need Git LFS
   ```
5. **Create `README.md` in Space:**
   ```yaml
   ---
   title: Vibe-Aware Pricing
   emoji: 🏠
   colorFrom: blue
   colorTo: red
   sdk: streamlit
   sdk_version: "1.28.0"
   app_file: Home.py
   pinned: false
   ---
   ```
6. **Push to Hugging Face:**
   ```bash
   cd vibe-pricing
   git add .
   git commit -m "Initial deployment"
   git push
   ```

**Your app will be live at:**
```
https://huggingface.co/spaces/YOUR_USERNAME/vibe-pricing
```

---

## 📊 Comparison Table

| Feature | Streamlit Cloud | ngrok | Hugging Face |
|---------|----------------|-------|--------------|
| **Setup Time** | 10-15 min | 2 min | 15-20 min |
| **Permanence** | ✅ Permanent | ❌ Temporary | ✅ Permanent |
| **Custom URL** | ✅ Yes | ❌ Random | ✅ Yes |
| **Uptime** | ✅ 24/7 | ❌ Only when PC on | ✅ 24/7 |
| **File Limits** | Git LFS needed | ✅ No limits | Git LFS needed |
| **Best For** | **Final deployment** | Quick testing | ML-focused apps |
| **Recommendation** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎯 Recommended Approach for Your Project

**For immediate testing (today):**
1. Use **ngrok** (5 min setup)
2. Share tunnel URL with teammates
3. Get feedback quickly

**For project submission (by Nov 17):**
1. Deploy to **Streamlit Community Cloud** (permanent)
2. Include URL in your project report
3. Professor/TAs can access anytime

---

## 🛠️ Troubleshooting Common Issues

### Issue 1: "File too large" when pushing to GitHub

**Solution:** Use Git LFS
```bash
git lfs install
git lfs track "*.pkl"
git lfs track "*.csv"
git add .gitattributes
git commit -m "Add Git LFS"
```

### Issue 2: "ModuleNotFoundError" on deployed app

**Solution:** Update `requirements.txt`
```bash
# Generate from your venv
pip freeze > requirements.txt

# Or manually add missing packages
echo "missing-package==1.0.0" >> requirements.txt
```

### Issue 3: App runs locally but crashes on Streamlit Cloud

**Check:**
1. File paths are relative (not absolute)
2. No hardcoded `C:/Users/...` paths
3. All data files included in repo

**Fix file paths:**
```python
# ❌ Bad (absolute path)
data = pd.read_csv('C:/Users/Nicholas/...')

# ✅ Good (relative path)
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
data = pd.read_csv(BASE_DIR / 'data/london/raw/file.csv')
```

### Issue 4: Slow loading on Streamlit Cloud

**Solutions:**
1. Cache data loading with `@st.cache_data`
2. Use `.parquet` instead of `.csv` (faster)
3. Reduce model file sizes

### Issue 5: "Out of memory" errors

**Solutions:**
1. Load data on-demand (not at startup)
2. Use smaller sample datasets for demo
3. Upgrade to Streamlit Cloud paid tier (if needed)

---

## 📝 Pre-Deployment Checklist

**Code Quality:**
- [ ] No hardcoded absolute paths
- [ ] All imports in `requirements.txt`
- [ ] No sensitive data (API keys, passwords)
- [ ] README.md explains the project
- [ ] Comments in code for clarity

**Data:**
- [ ] Model files < 1GB (or using Git LFS)
- [ ] CSV files compressed or sampled
- [ ] No personal/sensitive data

**Testing:**
- [ ] App runs locally without errors
- [ ] All 3 cities work
- [ ] Navigation works
- [ ] Charts display correctly

**Documentation:**
- [ ] README explains how to use app
- [ ] Requirements listed
- [ ] Known issues documented

---

## 🎬 Quick Start (Recommended Path)

**Day 1 (Today) - Quick Share:**
```bash
# 1. Install ngrok
# 2. Start app
cd app && source ../venv/bin/activate && streamlit run Home.py

# 3. In new terminal: ngrok http 8501
# 4. Share the ngrok URL with teammates
```

**Day 2 (Tomorrow) - Permanent Deploy:**
```bash
# 1. Create GitHub repo
# 2. Push code (use Git LFS for models)
# 3. Deploy to Streamlit Community Cloud
# 4. Update project report with permanent URL
```

---

## 📧 Share Instructions for Teammates

**Email template:**

```
Subject: Test our Vibe-Aware Pricing App!

Hey team,

I've deployed our pricing app! Check it out:

🔗 URL: [YOUR_STREAMLIT_URL]

What to test:
1. Try all 3 cities (London, Austin, NYC)
2. Input different property types
3. Play with the price slider
4. Check if vibe scores make sense
5. Note any bugs or UI issues

Please send feedback by [DATE].

Features to explore:
- Neighborhood vibe profiles (radar charts)
- Market comparisons (k-NN)
- Revenue optimization curves
- Interactive price testing

Thanks!
[Your name]
```

---

## 🎓 For Project Submission

**Include in your report:**

```markdown
## Live Demo

Our vibe-aware pricing application is deployed and accessible at:
**https://vibe-pricing.streamlit.app**

The application provides:
- Interactive property pricing for London, Austin, and NYC
- Neighborhood vibe analysis from 148,000+ listings
- Revenue optimization recommendations
- Real-time occupancy predictions

**To use:**
1. Select a city
2. Enter property details
3. Click "Analyze Property"
4. Explore recommendations and revenue curves
```

---

**Last Updated:** November 14, 2025
**Status:** Ready to deploy
**Recommended:** Start with ngrok (today), then Streamlit Cloud (tomorrow)
