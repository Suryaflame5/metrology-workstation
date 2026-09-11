# V5 DATABASE MIGRATION GUIDE — METROLOGY WORKSTATION

**From**: V4 Clean Production (`v1.0.0` / `v1.1.0`)  
**To**: V5 Production Engineering Workstation (`v5.0.0`)  

---

## 1. Non-Destructive Auto-Migration Architecture

Metrology Workstation V5 features zero-downtime, non-destructive automated database migration implemented in `metrology_app/db.py`:

```text
┌────────────────────────────────────────────────────────┐
│               EXISTING V4 SQLite DATABASE              │
│  • calculations (id, root_id, input_json, result_json) │
│  • audit_events (id, timestamp, event_hash)            │
└───────────────────────────┬────────────────────────────┘
                            │ init_db() Auto-Detection
                            ▼
┌────────────────────────────────────────────────────────┐
│               V5 UPGRADED SQLite DATABASE              │
│  [+] projects (id, name, customer_site, status)        │
│  [+] instruments (id, mfg, model, sn, status, due_date)│
│  [+] measurement_plans (id, measurand, nominal, tols)  │
│  [+] measurements (id, raw_values, mean, s, u_rep)     │
│  [*] calculations (ALTER TABLE ADD project_id, etc.)   │
│  [=] audit_events (Preserved with hash continuity)     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Migration Instructions

### Scenario A: Clean New Installation
1. Install Metrology Workstation V5 using `Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe`.
2. Launch the application.
3. Database initializes at `%LOCALAPPDATA%\MetrologyWorkstation\data\metrology_data.db` with 0 records.

### Scenario B: Existing V4 Customer Upgrade
1. Run the V5 setup installer over the existing installation.
2. Launch `MetrologyWorkstation.exe`.
3. `init_db()` inspects existing SQLite tables, executes `CREATE TABLE IF NOT EXISTS` for all new V5 entities, and applies `ALTER TABLE calculations ADD COLUMN` for foreign keys without modifying or deleting existing records.
4. All historical calibration records and SHA-256 audit ledger chains are 100% retained.
