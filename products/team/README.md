# Team / Laboratory Fleet Edition
=================================

Welcome to the **Team / Laboratory Fleet Edition** of the Metrology Workstation. 
This edition is designed for large-scale laboratories with multiple operational bays, 
requiring strict procedural synchronization, peer review, and batch processing.

## 🌟 Exclusive Features (vs. Professional Edition)

While the Professional edition is built for a single advanced workstation, the Team Edition provides:

1. **Fleet Synchronization Protocol**: Cryptographically secures and syncs procedures across up to 5 bays.
2. **Bay Status Monitor**: Real-time dashboard for OOT (Out-of-Tolerance) detection and drift warnings.
3. **4-Eyes Principle Peer Review**: Strict hash-chained peer review preventing self-approvals.
4. **Batch Calibration Pipeline**: High-throughput automated batch processing with checkpoint recovery.
5. **Procedure Distributor**: Secure, signed distribution of approved calibration procedures.
6. **Advanced Procedures**: Includes high-end CMM, Force, and Pressure calibration procedures not in Pro.

## 🏗️ Architecture

```text
+-------------------------------------------------------------+
|                     SHARED VAULT                            |
|  [Procedures]  [Manifests]  [Audit Logs]  [Peer Reviews]    |
+------------------------------+------------------------------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
+------v-------+        +------v-------+        +------v-------+
|    BAY 01    |        |    BAY 02    |        |    BAY 03    |
| (Dimensional)|        | (Electrical) |        | (Temp/Press) |
+--------------+        +--------------+        +--------------+
| Local Vault  |        | Local Vault  |        | Local Vault  |
| Sync Agent   |        | Sync Agent   |        | Sync Agent   |
| Batch Runner |        | Batch Runner |        | Batch Runner |
+--------------+        +--------------+        +--------------+
```

## 🚀 Deployment Guide

To deploy the Fleet Edition across your laboratory bays:

1. Ensure all target workstations are on the same domain or network share.
2. Edit `deployment/bay_config.json` to map your bays and instrument families.
3. Open a PowerShell console as Administrator.
4. Run the deployment script:
   ```powershell
   .\deployment\deploy_team_bays.ps1
   ```
5. Verify the `SharedVault` and local `Vault` directories are created.

## 🔄 Running Fleet Sync

To synchronize a bay with the shared vault:

```bash
python fleet_sync/shared_vault_sync.py --operator "OP-123" --mode "bidirectional"
```

## 🏭 Running the Batch Pipeline

For high-throughput jobs, use the batch pipeline:

```bash
python batch_pipeline/run_batch_calibration.py --queue batch_pipeline/job_queue_example.json
```
A batch summary report will be generated in the output directory.

## 👀 Peer Review (4-Eyes Principle)

The Team Edition enforces strict peer review.
Run the demo to see how self-review is blocked and hashes are chained:

```bash
python peer_review/peer_review_demo.py
```

## 📁 File Descriptions

*   `fleet_sync/shared_vault_sync.py`: Syncs and verifies procedures.
*   `fleet_sync/bay_status_monitor.py`: Dashboard for bay health.
*   `fleet_sync/procedure_distributor.py`: Distributes and signs procedures.
*   `batch_pipeline/run_batch_calibration.py`: High-throughput processing engine.
*   `batch_pipeline/job_queue_example.json`: Example job queue.
*   `batch_pipeline/batch_report_example.txt`: Example batch report.
*   `peer_review/peer_review_workflow.py`: The 4-eyes principle enforcement engine.
*   `peer_review/peer_review_demo.py`: Interactive demo of the review system.
*   `peer_review/pending_reviews_schema.sql`: Database schema for reviews.
*   `deployment/deploy_team_bays.ps1`: Automated deployment script.
*   `deployment/bay_config.json`: Configuration for all fleet bays.
*   `procedures/PROC_CMM_RENISHAW_QUALIFICATION.json`: Exclusive CMM procedure.
*   `procedures/PROC_FORCE_GAUGE_0_100N.json`: Exclusive Force gauge procedure.
*   `procedures/PROC_PRESSURE_GAUGE_0_10BAR.json`: Exclusive Pressure gauge procedure.

\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n