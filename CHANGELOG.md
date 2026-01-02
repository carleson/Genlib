# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Relation management between persons (parent-child, married, etc.)
- Family tree visualization
- GEDCOM import/export
- Advanced search with full-text
- OCR for scanned documents
- Export to PDF reports

## [0.1.0] - 2026-01-02

### Added

#### Core Features
- User authentication system (registration, login, logout)
- Dashboard with statistics and recent activity
- Responsive design with Bootstrap 5

#### Person Management
- Create, read, update, delete persons
- Person fields: first name, last name, birth/death dates, notes
- Automatic directory name generation
- Search functionality in persons
- Sorting by name
- Pagination (20 items per page)

#### Document Management
- Upload documents to persons
- Document metadata: source info, description, tags
- Automatic file size and type detection
- Support for txt, pdf, jpg, png, gif files
- Maximum file size: 10MB
- Document grouping by type
- Download documents

#### Document Types
- Configurable document types (CRUD)
- Predefined types: certificates, census records, church books, portraits
- Custom target directory and filename per type

#### Directory Templates
- Template system for directory structures
- Three predefined templates:
  - **default**: documents/, images/, notes/, media/, sources/
  - **extended**: Extended structure with subcategories
  - **minimal**: documents/, notes/
- CRUD operations for templates via Django Admin

#### Security
- CSRF protection
- XSS protection
- SQL injection protection (Django ORM)
- User-specific data isolation
- Secure file upload validation
- Authentication required for all operations

#### Technical
- Django 6.0
- Python 3.12+
- SQLite3 database
- Bootstrap 5 UI
- Swedish language interface
- Management command: `setup_initial_data`

### Documentation
- Complete README.md (Swedish/English)
- Installation guide (INSTALLATION.md)
- System overview (GENLIB_OVERVIEW.md)
- Contributing guidelines (CONTRIBUTING.md)
- Security policy (SECURITY.md)
- GitHub setup guide (GITHUB_SETUP.md)

### Infrastructure
- Docker support (Dockerfile, docker-compose.yml)
- Backup/restore scripts
- Environment variable configuration
- uv package manager integration

## [0.0.1] - Initial Development

### Added
- Initial project setup
- Basic Django structure
- App creation (accounts, persons, documents, core)

---

## Version History

### Types of Changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

[Unreleased]: https://github.com/your-username/genlib/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-username/genlib/releases/tag/v0.1.0
