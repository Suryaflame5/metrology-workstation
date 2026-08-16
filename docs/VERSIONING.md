# VERSIONING SPECIFICATION — METROLOGY WORKSTATION

**Canonical Version**: `1.0.0`  
**Standard**: Semantic Versioning 2.0.0 (`MAJOR.MINOR.PATCH`)  

---

## 1. Versioning Semantics

Given a version number `MAJOR.MINOR.PATCH`:
- **MAJOR (`1.x.x`)**: Incompatible API changes, major mathematical standard shifts, or breaking schema migrations.
- **MINOR (`x.1.x`)**: New backwards-compatible capabilities (e.g. adding new instrument procedures, new export formats).
- **PATCH (`x.x.1`)**: Backwards-compatible bug fixes, UI styling refinements, and performance improvements.

---

## 2. Authoritative Version Source

The canonical version is maintained in:
- `metrology_app/__init__.py`: `__version__ = "1.0.0"`
- `metrology_core/__init__.py`: `__version__ = "1.0.0"`

All downstream components (desktop application UI, installer metadata, GitHub release tags, and website download cards) must synchronize directly with this authoritative version.
