# GitHub Setup Guide for Genlib

This document contains recommendations for setting up your Genlib repository on GitHub.

## Repository Description

### Short Description (max 350 characters)
**English:**
```
Web-based genealogy research management system built with Django. Organize persons, documents, and source materials with a user-friendly interface. Features include document management, customizable templates, and secure authentication.
```

**Svenska:**
```
Webbaserat system för släktforskning byggt med Django. Organisera personer, dokument och källmaterial med ett användarvänligt gränssnitt. Funktioner inkluderar dokumenthantering, anpassningsbara mallar och säker autentisering.
```

## GitHub Topics

Add the following topics to your repository for better discoverability:

### Primary Topics
- `genealogy`
- `django`
- `python`
- `family-history`
- `document-management`

### Secondary Topics
- `genealogy-research`
- `django-application`
- `bootstrap5`
- `sqlite`
- `family-tree`
- `archive-management`
- `historical-research`
- `source-management`

### Technical Topics
- `django6`
- `python312`
- `uv`
- `web-application`

## Repository Settings

### General Settings

1. **Website:** Add your deployment URL (if applicable)
2. **Include in the home page:**
   - ✅ Releases
   - ✅ Packages
   - ✅ Deployments (if applicable)

3. **Features:**
   - ✅ Issues
   - ✅ Projects (optional)
   - ✅ Discussions (recommended for community support)
   - ✅ Wiki (optional, for extended documentation)

4. **Pull Requests:**
   - ✅ Allow squash merging
   - ✅ Allow merge commits
   - ✅ Automatically delete head branches

### Branch Protection (Recommended)

For the `main` branch:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Include administrators

## Social Preview Image

Create a social preview image (1280x640px) with:
- Genlib logo or name
- Tagline: "Genealogy Research Management System"
- Key features icons (documents, family tree, search)
- Color scheme matching your brand

## Issue Templates

Create `.github/ISSUE_TEMPLATE/` directory with templates:

### Bug Report Template
```markdown
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python Version: [e.g. 3.12]
 - Django Version: [e.g. 6.0]

**Additional context**
Add any other context about the problem here.
```

### Feature Request Template
```markdown
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## GitHub Actions (Optional CI/CD)

Create `.github/workflows/django.yml`:

```yaml
name: Django CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12']

    steps:
    - uses: actions/checkout@v4
    - name: Install uv
      uses: astral-sh/setup-uv@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: uv sync
    - name: Run migrations
      run: uv run python manage.py migrate
    - name: Run tests
      run: uv run pytest
```

## Labels

Create the following labels for better issue management:

| Label | Color | Description |
|-------|-------|-------------|
| `bug` | `#d73a4a` | Something isn't working |
| `enhancement` | `#a2eeef` | New feature or request |
| `documentation` | `#0075ca` | Improvements or additions to documentation |
| `good first issue` | `#7057ff` | Good for newcomers |
| `help wanted` | `#008672` | Extra attention is needed |
| `question` | `#d876e3` | Further information is requested |
| `wontfix` | `#ffffff` | This will not be worked on |
| `priority: high` | `#b60205` | High priority |
| `priority: medium` | `#fbca04` | Medium priority |
| `priority: low` | `#0e8a16` | Low priority |

## Release Strategy

### Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version: incompatible API changes
- **MINOR** version: add functionality (backwards-compatible)
- **PATCH** version: backwards-compatible bug fixes

Example: `v1.2.3`

### Release Process

1. Update `pyproject.toml` version
2. Update `CHANGELOG.md` (create if needed)
3. Create a git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub Release with changelog

## Security

### Security Policy

Create `SECURITY.md`:

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please send an email to [your-email@example.com].
Please do not create public GitHub issues for security vulnerabilities.

We will respond within 48 hours and work with you to resolve the issue.
```

### Dependabot

Enable Dependabot for automatic dependency updates:
- Go to Settings → Security & analysis
- Enable Dependabot alerts
- Enable Dependabot security updates

## Community Files

### Code of Conduct (Optional)

Create `CODE_OF_CONDUCT.md` using GitHub's template:
- Go to "Add file" → "Create new file"
- Name it `CODE_OF_CONDUCT.md`
- Click "Choose a code of conduct template"
- Select "Contributor Covenant"

## Initial Push Checklist

Before pushing to GitHub:

- [ ] Update `.gitignore` to exclude sensitive files
- [ ] Remove all secrets from `.env` (use `.env.example` instead)
- [ ] Update `README.md` with correct repository URL
- [ ] Review all files for personal information
- [ ] Ensure database files are excluded
- [ ] Ensure `media/` directory is excluded
- [ ] Remove `CLAUDE.md` if it contains project-specific info

## After Initial Push

1. **Set repository visibility** (Public/Private)
2. **Add topics** (as listed above)
3. **Add description**
4. **Create releases** for major versions
5. **Set up GitHub Pages** (optional, for documentation)
6. **Enable Discussions** for community interaction
7. **Star your own repo** (for visibility)

## Deployment Options

### Free Hosting Options for Django

1. **Railway.app**
   - Easy Django deployment
   - Free tier available
   - PostgreSQL support

2. **Render.com**
   - Free tier for web services
   - Automatic deployments from GitHub
   - PostgreSQL included

3. **PythonAnywhere**
   - Free tier for beginners
   - Good for learning/testing

4. **Fly.io**
   - Modern deployment platform
   - Free tier available
   - Good performance

### Deployment Configuration Files

You may want to create:
- `render.yaml` for Render.com
- `railway.json` for Railway.app
- `Procfile` for Heroku-like platforms
- `docker-compose.yml` for containerized deployment (already exists)

## Marketing Your Repository

1. **Social Media:**
   - Share on Twitter/X with hashtags: #genealogy #django #opensource
   - Post in genealogy communities
   - Share in Django communities

2. **Forums and Communities:**
   - Reddit: r/django, r/genealogy
   - Dev.to article about your project
   - Hacker News (Show HN)

3. **Package Registries:**
   - Consider publishing to PyPI if it becomes a reusable package

## Monitoring

Set up monitoring for:
- GitHub Stars (track popularity)
- Issues and PRs (engagement)
- Contributors (community growth)
- Downloads/Clones (usage metrics)

---

**Good luck with your GitHub repository!**
