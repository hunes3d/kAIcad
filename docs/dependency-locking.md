# Dependency Locking

## Regenerating requirements.lock

This project uses `pip-tools` for dependency locking to ensure reproducible builds.

### Prerequisites

```bash
pip install pip-tools
```

### Generate Lock File

Due to `kicad-skip` requiring Rust compilation, we use `pip freeze` for locking:

```bash
# After installing all dependencies
pip freeze > requirements.lock
```

### Alternative: Using pip-tools (if Rust toolchain available)

```bash
pip-compile --output-file=requirements.lock requirements.txt
```

### Installing from Lock File

```bash
pip install -r requirements.lock
```

### Updating Dependencies

1. Update version constraints in `requirements.txt` or `pyproject.toml`
2. Regenerate lock file using method above
3. Test thoroughly before committing

### CI/CD Integration

The lock file ensures consistent builds across environments. CI should install from `requirements.lock` instead of `requirements.txt`.

## Current Lock File Generation

As of October 20, 2025, the lock file is generated using `pip freeze` due to `kicad-skip==0.2.5` requiring Rust compilation which may not be available in all environments.

**Note**: Pre-built wheels for `kicad-skip` are available on PyPI, so standard `pip install` works without Rust.
