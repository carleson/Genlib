# GitHub Quick Start Guide

This is a quick reference for uploading your Genlib project to GitHub.

## Pre-Upload Checklist

- [x] `.gitignore` updated (excludes `.env`, `CLAUDE.md`, database files)
- [x] `README.md` created (bilingual)
- [x] `LICENSE` created (MIT)
- [x] `CONTRIBUTING.md` created
- [x] `SECURITY.md` created
- [x] `CHANGELOG.md` created
- [x] GitHub issue templates created
- [x] GitHub Actions workflow created
- [ ] Update `LICENSE` with your name
- [ ] Update `SECURITY.md` with your email
- [ ] Verify no sensitive data in files
- [ ] Update repository URLs in documentation

## Step 1: Initialize Git Repository

```bash
# If not already initialized
cd /home/johan/repos/projekt/genlib
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Genlib v0.1.0"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `genlib`
3. Description (copy one):

**English:**
```
Web-based genealogy research management system built with Django. Organize persons, documents, and source materials with a user-friendly interface.
```

**Svenska:**
```
Webbaserat system för släktforskning byggt med Django. Organisera personer, dokument och källmaterial.
```

4. Choose visibility: **Public** or **Private**
5. **DO NOT** initialize with README (you already have one)
6. Click "Create repository"

## Step 3: Push to GitHub

```bash
# Add remote origin (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/genlib.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 4: Configure Repository Settings

### Add Topics

Go to your repository → Click ⚙️ next to "About" → Add topics:

**Primary Topics:**
- genealogy
- django
- python
- family-history
- document-management

**Secondary Topics:**
- genealogy-research
- django-application
- bootstrap5
- family-tree
- archive-management

### Repository Features

Enable:
- ✅ Issues
- ✅ Discussions (recommended)
- ✅ Projects (optional)

## Step 5: Create First Release

```bash
# Create and push tag
git tag -a v0.1.0 -m "Release v0.1.0 - Initial MVP"
git push origin v0.1.0
```

Then on GitHub:
1. Go to "Releases" → "Create a new release"
2. Choose tag: `v0.1.0`
3. Title: `v0.1.0 - Initial MVP Release`
4. Description: Copy from CHANGELOG.md
5. Click "Publish release"

## Step 6: Set Up Protection (Optional)

For serious projects:
1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - Require pull request reviews
   - Require status checks to pass

## GitHub Repository URLs

After creation, update these files with your actual URLs:

### Files to Update

1. **README.md** (2 places)
   - Line 43: `git clone https://github.com/YOUR_USERNAME/genlib.git`
   - Line 126: `git clone https://github.com/YOUR_USERNAME/genlib.git`

2. **CONTRIBUTING.md** (2 places)
   - Lines with repository clone URLs

3. **CHANGELOG.md** (bottom links)

Replace `YOUR_USERNAME` with your GitHub username.

## Quick Git Commands Reference

```bash
# Check status
git status

# Stage all changes
git add .

# Commit changes
git commit -m "feat: add new feature"

# Push changes
git push

# Pull latest changes
git pull

# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Merge branch
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

## Common Issues

### Issue: Permission denied (publickey)

**Solution:** Set up SSH key or use HTTPS with token
```bash
# Use HTTPS instead
git remote set-url origin https://github.com/YOUR_USERNAME/genlib.git
```

### Issue: Updates were rejected

**Solution:** Pull first, then push
```bash
git pull origin main --rebase
git push origin main
```

### Issue: Accidentally committed sensitive data

**Solution:** Remove from history
```bash
# Remove file from tracking but keep locally
git rm --cached .env

# Commit the change
git commit -m "Remove .env from tracking"

# Push
git push
```

If already pushed sensitive data:
1. Change all secrets immediately
2. Consider using `git filter-branch` or BFG Repo-Cleaner
3. Force push (use with caution)

## Next Steps

After successful upload:

1. **Star your repository** (for visibility)
2. **Share on social media**
   - Twitter/X: #genealogy #django #opensource
   - Reddit: r/django, r/genealogy
   - Dev.to: Write a blog post

3. **Add badges to README** (optional)
   ```markdown
   ![Django CI](https://github.com/YOUR_USERNAME/genlib/workflows/Django%20CI/badge.svg)
   ![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
   ![License](https://img.shields.io/badge/license-MIT-green.svg)
   ```

4. **Consider deployment**
   - Railway.app
   - Render.com
   - Fly.io
   - PythonAnywhere

5. **Set up project board** (GitHub Projects)
   - Plan future features
   - Track issues

## Support

For detailed information, see:
- [GITHUB_SETUP.md](GITHUB_SETUP.md) - Complete setup guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](SECURITY.md) - Security policy

---

**You're ready to share Genlib with the world!** 🚀
