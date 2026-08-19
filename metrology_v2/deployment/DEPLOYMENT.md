# Metrology V2 Deployment Guide

## Overview

Metrology V2 is a production-grade metrology platform designed for enterprise deployment. This guide covers deployment across multiple platforms and environments.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.13+, or Linux
- **Processor**: x64 architecture
- **Memory**: 8 GB RAM minimum, 16 GB recommended
- **Storage**: 500 MB for application, 10 GB for data
- **Network**: Local network or internet for initial setup

### Software Dependencies
- Python 3.12+
- PostgreSQL 15+
- (Optional) Docker for containerized deployment

## Installation Methods

### Windows Installation

1. **Download the installer**: `install_windows.ps1`
2. **Run as Administrator**: Right-click and select "Run as Administrator"
3. **Follow the prompts**: The installer will:
   - Install Python dependencies
   - Create application directories
   - Configure firewall rules
   - Create desktop shortcuts

### macOS Installation

1. **Download the installer**: `install_macos.sh`
2. **Make executable**: `chmod +x install_macos.sh`
3. **Run with sudo**: `sudo ./install_macos.sh`
4. **Follow the prompts**: The installer will:
   - Install Homebrew (if not present)
   - Install Python 3.12
   - Install required packages
   - Create .app bundle in Applications folder

### Docker Deployment

1. **Build the image**: `docker build -t metrology-v2 .`
2. **Run with Docker Compose**: `docker-compose up -d`
3. **Access the application**: `http://localhost:8000`

## Configuration

### Environment Variables

Configure the following environment variables:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=metrology_v2
DB_USER=metrology_user
DB_PASSWORD=your_password

# Application Configuration
METROLOGY_ENV=production
METROLOGY_DEPLOYMENT=local
SECRET_KEY=your_secret_key
MFA_ENABLED=true
ENABLE_ANIMATIONS=true
ENABLE_AGENTIC_UI=true

# Storage Configuration
STORAGE_PATH=/path/to/storage
```

### Database Setup

1. **Create PostgreSQL database**:
```sql
CREATE DATABASE metrology_v2;
CREATE USER metrology_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE metrology_v2 TO metrology_user;
```

2. **Run migrations**:
```bash
cd metrology_v2/infrastructure/database
alembic upgrade head
```

## Deployment Modes

### Local Deployment
- Single-user installation
- Local PostgreSQL database
- Desktop application with embedded server
- Ideal for individual laboratories

### Professional Deployment
- Desktop/web client
- Application server
- Shared PostgreSQL database
- File-based object storage
- Suitable for small teams

### Enterprise Deployment
- Multi-server setup
- Load balancer
- PostgreSQL with connection pooling
- Redis for caching and job queues
- S3-compatible object storage
- Background job workers
- High availability configuration

## Verification

### Health Check
```bash
curl http://localhost:8000/health
```

### Database Connection
```bash
psql -h localhost -U metrology_user -d metrology_v2
```

### Application Logs
```bash
# Windows
type %LOCALAPPDATA%\MetrologyV2\logs\app.log

# macOS/Linux
tail -f ~/.local/share/MetrologyV2/logs/app.log
```

## Troubleshooting

### Port Already in Use
Change the default port in the configuration:
```bash
export DEFAULT_PORT=8001
```

### Database Connection Failed
1. Verify PostgreSQL is running
2. Check connection parameters
3. Ensure firewall allows connections

### Permission Errors
1. Run installer as administrator (Windows) or with sudo (macOS/Linux)
2. Check file permissions on data directories

## Backup and Recovery

### Database Backup
```bash
pg_dump -U metrology_user metrology_v2 > backup.sql
```

### Database Restore
```bash
psql -U metro_user metrology_v2 < backup.sql
```

### Application Data Backup
```bash
# Windows
robocopy %LOCALAPPDATA%\MetrologyV2\data C:\backup\metrology_data /E

# macOS/Linux
cp -r ~/.local/share/MetrologyV2/data ~/backup/metrology_data
```

## Security Considerations

### Production Deployment
1. **Change default passwords**
2. **Enable HTTPS/TLS**
3. **Configure firewall rules**
4. **Enable audit logging**
5. **Regular security updates**
6. **Backup encryption**

### Network Security
1. **Use VPN for remote access**
2. **Implement rate limiting**
3. **Enable DDoS protection**
4. **Regular security audits**

## Monitoring

### Application Metrics
- API response time
- Database query performance
- Memory usage
- CPU utilization
- Error rates

### Logging
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Audit logs: Database audit_events table

## Support

For deployment support:
- Email: novyrax04@gmail.com
- Documentation: https://novyrax.vercel.app/docs
- Issues: GitHub Issues

---

*Deployment Guide for Metrology V2 v2.0.0*
*Edition: PRODUCTION*
*© 2026 NovyraX. All rights reserved.*
