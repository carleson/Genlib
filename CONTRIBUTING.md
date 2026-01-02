# Contributing to Genlib

[🇸🇪 Svenska](#svenska) | [🇬🇧 English](#english)

---

## <a name="svenska"></a>🇸🇪 Svenska

Tack för att du vill bidra till Genlib! Vi uppskattar alla bidrag, oavsett om det är bugfixar, nya funktioner, dokumentation eller förbättringar.

### Hur kan jag bidra?

#### Rapportera buggar

Om du hittar en bugg, öppna gärna ett issue med följande information:
- Tydlig beskrivning av problemet
- Steg för att återskapa buggen
- Förväntad vs faktiskt beteende
- Din miljö (OS, Python-version, etc.)
- Screenshots om tillämpligt

#### Föreslå nya funktioner

Vi välkomnar förslag på nya funktioner! Öppna ett issue med:
- Tydlig beskrivning av funktionen
- Motivering - varför behövs denna funktion?
- Eventuella exempel eller mockups

#### Pull Requests

1. **Forka repot** och skapa en ny branch från `main`
   ```bash
   git checkout -b feature/min-nya-funktion
   ```

2. **Följ kodkonventionerna** (se nedan)

3. **Skriv tester** för ny funktionalitet

4. **Kör testerna** innan du skickar PR
   ```bash
   uv run pytest
   ```

5. **Committa med tydliga meddelanden**
   ```
   feat: lägg till export till GEDCOM-format
   fix: rätta fel i personsökning
   docs: uppdatera installationsguide
   ```

6. **Skicka din PR** med en tydlig beskrivning av ändringarna

### Kodkonventioner

#### Python-stil
- Följ **PEP 8**
- Använd **type hints** genomgående
- Docstrings i **Google-format**
- Radlängd: max **88 tecken** (Black-standard)

#### Namngivning
- Funktioner och variabler: `snake_case`
- Klasser: `PascalCase`
- Konstanter: `SCREAMING_SNAKE_CASE`

#### Django-specifikt
- Använd Django ORM istället för råa SQL-queries
- Följ Django's best practices för views, models och forms
- Använd Django's inbyggda säkerhetsfunktioner

### Utvecklingsmiljö

```bash
# Klona ditt fork
git clone https://github.com/ditt-användarnamn/genlib.git
cd genlib

# Installera beroenden
uv sync

# Skapa databas och kör migrationer
uv run python manage.py migrate

# Skapa initial data
uv run python manage.py setup_initial_data

# Starta utvecklingsserver
uv run python manage.py runserver
```

### Tester

```bash
# Kör alla tester
uv run pytest

# Kör med coverage
uv run pytest --cov=. --cov-report=term-missing

# Kör specifikt test
uv run pytest tests/test_persons.py
```

### Commit-meddelanden

Vi använder [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - ny funktionalitet
- `fix:` - buggfix
- `docs:` - dokumentation
- `test:` - tester
- `refactor:` - refaktorering utan funktionsändring
- `style:` - formattering, saknade semikolon, etc.
- `chore:` - uppdatering av byggverktyg, dependencies, etc.

### Code Review Process

1. Minst en annan utvecklare måste granska din PR
2. All feedback måste addresseras
3. Alla tester måste passera
4. Koden måste följa kodkonventionerna

### Frågor?

Om du har frågor, öppna gärna ett issue eller kontakta maintainers.

---

## <a name="english"></a>🇬🇧 English

Thank you for wanting to contribute to Genlib! We appreciate all contributions, whether it's bug fixes, new features, documentation or improvements.

### How can I contribute?

#### Report bugs

If you find a bug, please open an issue with the following information:
- Clear description of the problem
- Steps to reproduce the bug
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Screenshots if applicable

#### Suggest new features

We welcome suggestions for new features! Open an issue with:
- Clear description of the feature
- Justification - why is this feature needed?
- Any examples or mockups

#### Pull Requests

1. **Fork the repo** and create a new branch from `main`
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Follow the code conventions** (see below)

3. **Write tests** for new functionality

4. **Run the tests** before submitting PR
   ```bash
   uv run pytest
   ```

5. **Commit with clear messages**
   ```
   feat: add export to GEDCOM format
   fix: correct error in person search
   docs: update installation guide
   ```

6. **Submit your PR** with a clear description of the changes

### Code Conventions

#### Python Style
- Follow **PEP 8**
- Use **type hints** throughout
- Docstrings in **Google format**
- Line length: max **88 characters** (Black standard)

#### Naming
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `SCREAMING_SNAKE_CASE`

#### Django-specific
- Use Django ORM instead of raw SQL queries
- Follow Django's best practices for views, models and forms
- Use Django's built-in security features

### Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/genlib.git
cd genlib

# Install dependencies
uv sync

# Create database and run migrations
uv run python manage.py migrate

# Create initial data
uv run python manage.py setup_initial_data

# Start development server
uv run python manage.py runserver
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=term-missing

# Run specific test
uv run pytest tests/test_persons.py
```

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - new feature
- `fix:` - bug fix
- `docs:` - documentation
- `test:` - tests
- `refactor:` - refactoring without functional change
- `style:` - formatting, missing semicolons, etc.
- `chore:` - updating build tools, dependencies, etc.

### Code Review Process

1. At least one other developer must review your PR
2. All feedback must be addressed
3. All tests must pass
4. Code must follow code conventions

### Questions?

If you have questions, feel free to open an issue or contact maintainers.

---

**Thank you for contributing to Genlib!**
