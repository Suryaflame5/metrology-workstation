# Metrology V2 - Professional Metrology Platform

Version: 2.0.0
Edition: PRODUCTION
License: Commercial

A production-grade, auditable metrology platform for accredited laboratories, quality engineering teams, and precision manufacturing operations.

## Features

### Core Capabilities
- 50-digit exact decimal mathematics for uncompromising accuracy
- GUM uncertainty propagation with full audit trails
- TUR and guardband calculations for compliance
- ISO 14253-1 conformity assessment
- Immutable measurement history with version control
- Cryptographic audit evidence for reproducibility

### Premium Features
- Advanced Analytics with SPC, ML anomaly detection, and trend analysis
- Fleet Management with complete lifecycle tracking
- Enterprise Certificate Generation with digital signatures
- Full API Integration with REST, webhooks, and ERP/PLM connectors
- Plugin System with custom scripting capabilities
- Agentic UI Animations for professional user experience

## Quick Start

### Installation

#### Windows
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File install_windows.ps1
```

#### macOS
```bash
# Run with sudo
sudo ./install_macos.sh
```

#### Docker
```bash
docker-compose up -d
```

### Configuration

1. Set environment variables (see DEPLOYMENT.md)
2. Configure database connection
3. Run database migrations: alembic upgrade head
4. Start the application

### Running the Application

#### Desktop Application
```bash
python -m metrology_v2.desktop.application
```

#### Web API
```bash
python -m uvicorn metrology_v2.api.rest:app --host 0.0.0.0 --port 8000
```

## Documentation

- Deployment Guide: DEPLOYMENT.md
- Architecture Documentation: PREMIUM_ARCHITECTURE.md
- User Guide: PREMIUM_USER_GUIDE.md
- API Documentation: http://localhost:8000/api/docs

## Requirements

- Python 3.12+
- PostgreSQL 15+
- See requirements.txt for full dependencies

## Architecture

Metrology V2 follows a modular monolith architecture with domain-driven design.

## Support

- Email: novyrax04@gmail.com
- Website: https://novyrax.vercel.app
- Documentation: https://novyrax.vercel.app/docs

## License

Commercial License - See LICENSE file for details.

## Version

Current Version: 2.0.0
Edition: PRODUCTION

Metrology V2 - Professional Metrology Platform
Copyright 2026 NovyraX. All rights reserved.
