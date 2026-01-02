# Security Policy

## Supported Versions

The following versions of Genlib are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Genlib seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

**Please do NOT create public GitHub issues for security vulnerabilities.**

Instead, please report security vulnerabilities by:
1. Sending an email to [your-email@example.com] with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

2. Allow us time to address the issue before public disclosure

### What to Expect

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days with initial assessment
- **Resolution:** We aim to release a fix within 30 days for critical issues

### Security Best Practices for Users

When deploying Genlib:

1. **Environment Variables:**
   - Always use strong, unique `SECRET_KEY`
   - Never commit `.env` file to version control
   - Use `.env.example` as template

2. **Production Settings:**
   - Set `DEBUG=0` in production
   - Configure `ALLOWED_HOSTS` properly
   - Use HTTPS in production
   - Keep dependencies updated

3. **Database:**
   - Use strong database passwords
   - Restrict database access
   - Regular backups

4. **File Uploads:**
   - The system validates file types
   - Maximum file size is enforced
   - Files are stored outside webroot

5. **User Authentication:**
   - Use strong passwords
   - Enable Django's password validation
   - Consider implementing 2FA (future feature)

### Known Security Considerations

1. **File Storage:**
   - Uploaded files are stored in `media/users/{user_id}/`
   - Configure your web server to prevent execution of uploaded files

2. **Session Security:**
   - Sessions expire after inactivity
   - Use secure session cookies in production

3. **CSRF Protection:**
   - CSRF protection is enabled by default
   - All forms use CSRF tokens

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 0.1.1)
- Announced in GitHub Releases
- Documented in CHANGELOG.md

## Credits

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged (with permission) in:
- Release notes
- CHANGELOG.md
- This security policy

---

**Thank you for helping keep Genlib and its users safe!**
