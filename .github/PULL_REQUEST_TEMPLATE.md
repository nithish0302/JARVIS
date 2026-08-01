## Description

Provide a clear and concise description of the changes proposed in this Pull Request, including the rationale.

## Related Issues / Tickets

Fixes # (issue number)
Resolves ticket: `docs/tickets/JAR-XXX.md`

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring / Code quality improvement

## Verification Plan

### Automated Tests
- Run `pnpm --filter desktop test:run` and verify vitest passes.
- Run `uv run pytest services/jarvis-engine` and verify backend tests pass.

### Manual Verification
- Describe the exact steps taken to verify the changes.

## Checklist

- [ ] My code follows the code style guidelines of this project (Ruff, Black, ESLint, Prettier, rustfmt).
- [ ] I have performed a self-review of my own code.
- [ ] I have commented my code, particularly in hard-to-understand areas.
- [ ] I have made corresponding changes to the documentation.
- [ ] My changes generate no new warnings.
- [ ] I have added tests that prove my fix is effective or that my feature works.
- [ ] New and existing unit tests pass locally with my changes.
