# CLAUDE.md - AI Assistant Guide for yasooo Repository

This document provides comprehensive guidance for AI assistants working with the yasooo repository. It covers codebase structure, development workflows, conventions, and best practices.

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Development Workflow](#development-workflow)
- [Key Conventions](#key-conventions)
- [Working with Git](#working-with-git)
- [Common Tasks](#common-tasks)
- [Testing Guidelines](#testing-guidelines)
- [Deployment](#deployment)
- [AI Assistant Best Practices](#ai-assistant-best-practices)

---

## Project Overview

**Repository Name:** yasooo
**Owner:** elmansoory
**Status:** Active Development

### Purpose

[To be documented: Add project description, goals, and primary use cases]

### Tech Stack

[To be documented as technologies are added]

Common tech stack patterns to watch for:
- **Frontend:** React, Vue, Angular, Next.js, etc.
- **Backend:** Node.js, Python, Go, Java, etc.
- **Database:** PostgreSQL, MongoDB, Redis, etc.
- **Infrastructure:** Docker, Kubernetes, AWS, etc.

---

## Repository Structure

```
yasooo/
├── .git/                  # Git repository metadata
├── CLAUDE.md             # This file - AI assistant guide
└── [To be documented as project structure develops]
```

### Key Directories

[To be documented: Add descriptions of main directories as they are created]

**Example structure to watch for:**
- `src/` - Source code
- `test/` or `tests/` - Test files
- `docs/` - Documentation
- `config/` - Configuration files
- `scripts/` - Build and utility scripts
- `public/` or `static/` - Static assets
- `.github/` - GitHub workflows and templates

### Important Files

[To be documented: Add critical configuration files]

**Common important files:**
- `package.json` / `requirements.txt` / `go.mod` - Dependencies
- `README.md` - Project documentation
- `.gitignore` - Git ignore patterns
- `docker-compose.yml` - Container orchestration
- Configuration files (`.env`, `config.yaml`, etc.)

---

## Development Workflow

### Branch Strategy

**Main Branches:**
- `main` or `master` - Production-ready code
- Development branches follow the pattern: `claude/claude-md-*` for AI assistant work

**Branch Naming Convention:**
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- AI assistant branches: `claude/claude-md-[session-id]`

### Commit Message Format

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Formatting, missing semicolons, etc.
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance tasks

**Examples:**
```
feat(auth): add user login functionality
fix(api): resolve null pointer in user handler
docs(readme): update installation instructions
```

### Pull Request Process

1. Create feature branch from main
2. Make changes with clear, atomic commits
3. Push branch to remote
4. Create pull request with description
5. Address review feedback
6. Merge after approval

---

## Key Conventions

### Code Style

[To be documented based on project language and tooling]

**General Principles:**
- Follow language-specific style guides
- Use linters and formatters (ESLint, Prettier, Black, gofmt, etc.)
- Keep functions small and focused
- Write self-documenting code with clear names
- Add comments for complex logic only

### File Naming

[To be documented based on project patterns]

**Common conventions:**
- Use kebab-case for files: `user-service.js`
- Use PascalCase for components: `UserProfile.jsx`
- Use camelCase for utilities: `parseUserData.js`
- Test files: `*.test.js`, `*.spec.js`, `*_test.go`

### Error Handling

**Best Practices:**
- Always handle errors explicitly
- Log errors with context
- Use appropriate error types
- Don't expose sensitive information in error messages
- Provide helpful error messages

### Security Considerations

**Critical Rules:**
- Never commit secrets, API keys, or credentials
- Validate and sanitize all user input
- Use parameterized queries (prevent SQL injection)
- Escape output (prevent XSS)
- Implement proper authentication and authorization
- Keep dependencies updated
- Follow OWASP Top 10 guidelines

---

## Working with Git

### Setup

```bash
# Clone repository
git clone <repository-url>

# Configure user (if needed)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Daily Workflow

```bash
# Create new branch
git checkout -b feature/new-feature

# Stage changes
git add .

# Commit changes
git commit -m "feat: add new feature"

# Push to remote (use -u flag for new branches)
git push -u origin feature/new-feature

# For subsequent pushes
git push origin feature/new-feature
```

### AI Assistant Git Rules

**CRITICAL - Follow these rules when making git operations:**

1. **Branch Requirements:**
   - Develop on designated branch: `claude/claude-md-mi30tjffoo8cf2so-01KCLmWYW3mzKmuLz8sSggxh`
   - Create branch locally if it doesn't exist
   - NEVER push to different branches without permission

2. **Push Operations:**
   - Always use: `git push -u origin <branch-name>`
   - Branch must start with `claude/` and end with session ID
   - Retry network failures up to 4 times with exponential backoff (2s, 4s, 8s, 16s)

3. **Fetch/Pull Operations:**
   - Prefer: `git fetch origin <branch-name>`
   - Retry network failures up to 4 times with exponential backoff

4. **Commit Best Practices:**
   - Create commits only when requested
   - Never skip hooks (--no-verify)
   - Never force push to main/master
   - Check authorship before amending: `git log -1 --format='%an %ae'`
   - Use heredoc for commit messages:
     ```bash
     git commit -m "$(cat <<'EOF'
     feat: add new feature

     Detailed description here
     EOF
     )"
     ```

---

## Common Tasks

### Running the Project

[To be documented based on project setup]

```bash
# Example patterns to look for:
npm start / npm run dev
python main.py / python manage.py runserver
go run main.go
make run
docker-compose up
```

### Building

[To be documented]

```bash
# Common build commands:
npm run build
make build
go build
python setup.py build
```

### Testing

[To be documented]

```bash
# Common test commands:
npm test / npm run test
pytest
go test ./...
make test
```

### Linting and Formatting

[To be documented]

```bash
# Common linting commands:
npm run lint
eslint .
pylint src/
golangci-lint run
```

---

## Testing Guidelines

### Test Structure

[To be documented based on testing framework]

**General Principles:**
- Write tests for new features
- Maintain test coverage above [X]%
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert
- Mock external dependencies
- Test edge cases and error conditions

### Test Categories

1. **Unit Tests** - Test individual functions/methods
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test complete user workflows
4. **Performance Tests** - Test system performance

---

## Deployment

[To be documented based on deployment strategy]

### Environments

- **Development** - Local development
- **Staging** - Pre-production testing
- **Production** - Live environment

### Deployment Process

[To be documented: Add CI/CD pipeline details, deployment commands, etc.]

---

## AI Assistant Best Practices

### Before Starting Work

1. **Read this CLAUDE.md file completely**
2. **Check git status** - Understand current branch and changes
3. **Review recent commits** - Understand recent changes
4. **Use TodoWrite** - Plan complex tasks with todo list
5. **Search before creating** - Look for existing implementations

### During Development

1. **Use appropriate tools:**
   - Read tool for viewing files
   - Edit tool for modifying files
   - Glob/Grep for searching
   - Task tool for complex exploration
   - Bash for git operations and system commands

2. **Code quality:**
   - Follow existing patterns in the codebase
   - Write secure code (no SQL injection, XSS, etc.)
   - Add appropriate error handling
   - Include relevant tests
   - Update documentation

3. **Communication:**
   - Be concise and clear
   - Avoid emojis unless requested
   - Use markdown for formatting
   - Reference code with `file_path:line_number` pattern
   - Explain complex changes

### File Operations

**Prefer editing over creating:**
- ALWAYS prefer editing existing files
- NEVER create new files unless absolutely necessary
- Don't create documentation files unless requested

**Tool usage:**
- Use Read tool (not cat)
- Use Edit tool (not sed/awk)
- Use Write tool (not echo/heredoc)
- Use Glob for file patterns
- Use Grep for content search

### Git Operations

**Commit Process:**
1. Run `git status` to see changes
2. Run `git diff` to review changes
3. Review `git log` for commit message style
4. Stage relevant files with `git add`
5. Commit with clear message
6. Verify with `git status`

**When commits fail due to hooks:**
- Retry ONCE if pre-commit hook modifies files
- Check authorship before amending
- Create NEW commit if not safe to amend

### Task Management

**Use TodoWrite tool for:**
- Complex multi-step tasks (3+ steps)
- Non-trivial implementations
- User-provided task lists
- Tracking progress

**Don't use TodoWrite for:**
- Single straightforward tasks
- Trivial operations
- Purely conversational requests

**Todo management:**
- Mark tasks in_progress before starting
- Complete tasks immediately after finishing
- Only ONE task in_progress at a time
- Remove irrelevant tasks
- Update status in real-time

### Security Checklist

**Before committing, verify:**
- [ ] No hardcoded secrets or API keys
- [ ] No credentials in code
- [ ] Input validation implemented
- [ ] SQL queries use parameterization
- [ ] Output properly escaped
- [ ] Authentication/authorization in place
- [ ] No sensitive data in logs
- [ ] Dependencies are secure

---

## Project-Specific Notes

[This section will be updated as project-specific patterns emerge]

### Architecture Patterns

[To be documented: MVC, microservices, serverless, etc.]

### External Services

[To be documented: List third-party APIs, services, dependencies]

### Environment Variables

[To be documented: List required environment variables]

### Known Issues

[To be documented: Track known issues and workarounds]

### Performance Considerations

[To be documented: Add performance bottlenecks, optimization tips]

---

## Maintenance

### Updating This Document

This CLAUDE.md file should be updated when:
- New major features are added
- Architecture changes occur
- Development workflows change
- New conventions are established
- Common issues are discovered

**Last Updated:** 2025-11-17
**Version:** 1.0.0

---

## Quick Reference

### Essential Commands

```bash
# Git
git status
git add .
git commit -m "message"
git push -u origin <branch>

# [Add project-specific commands as they are established]
```

### File References

Use this pattern when referencing code:
- `path/to/file.js:123` - References line 123 in file.js

### Getting Help

- Check README.md for project overview
- Review existing code for patterns
- Check git history for context
- Use Task tool for complex exploration

---

*This document is a living guide that evolves with the project. Keep it updated to ensure AI assistants have accurate information.*
