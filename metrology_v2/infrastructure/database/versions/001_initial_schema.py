"""Initial schema creation for Metrology V2

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-19 21:28:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema for Metrology V2."""
    
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('accreditation_number', sa.String(100)),
        sa.Column('accreditation_body', sa.String(255)),
        sa.Column('address', sa.Text),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('settings', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('mfa_secret', sa.String(255)),
        sa.Column('mfa_enabled', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('failed_login_attempts', sa.Integer, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('address', sa.Text),
        sa.Column('department', sa.String(255)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create user_permissions table
    op.create_table(
        'user_permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('permission_id', sa.String(36), sa.ForeignKey('permissions.id'), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('granted_by_id', sa.String(36), sa.ForeignKey('users.id')),
    )
    
    # Create instruments table
    op.create_table(
        'instruments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('custodian_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('asset_number', sa.String(50), unique=True, nullable=False),
        sa.Column('serial_number', sa.String(100), unique=True, nullable=False),
        sa.Column('manufacturer', sa.String(255), nullable=False),
        sa.Column('model', sa.String(255), nullable=False),
        sa.Column('instrument_type', sa.String(100), nullable=False),
        sa.Column('range_min', sa.Float),
        sa.Column('range_max', sa.Float),
        sa.Column('range_unit', sa.String(20)),
        sa.Column('resolution', sa.Float),
        sa.Column('resolution_unit', sa.String(20)),
        sa.Column('accuracy', sa.Float),
        sa.Column('accuracy_unit', sa.String(20)),
        sa.Column('calibration_interval_months', sa.Integer, server_default='12'),
        sa.Column('last_calibration_date', sa.DateTime(timezone=True)),
        sa.Column('next_calibration_date', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('purchase_date', sa.DateTime(timezone=True)),
        sa.Column('purchase_cost', sa.Numeric(10, 2)),
        sa.Column('retirement_date', sa.DateTime(timezone=True)),
        sa.Column('description', sa.Text),
        sa.Column('specifications', sa.JSON),
        sa.Column('photo_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by_id', sa.String(36), sa.ForeignKey('users.id')),
    )
    
    # Create indexes for instruments
    op.create_index('idx_instrument_asset_number', 'instruments', ['asset_number'])
    op.create_index('idx_instrument_serial_number', 'instruments', ['serial_number'])
    op.create_index('idx_instrument_status', 'instruments', ['status'])
    op.create_index('idx_instrument_next_calibration', 'instruments', ['next_calibration_date'])
    
    # Create instrument_lifecycle_events table
    op.create_table(
        'instrument_lifecycle_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('previous_status', sa.String(20)),
        sa.Column('new_status', sa.String(20)),
        sa.Column('previous_location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('new_location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('previous_custodian_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('new_custodian_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('reason', sa.Text),
        sa.Column('performed_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('metadata', sa.JSON),
    )
    
    # Create calibration_procedures table
    op.create_table(
        'calibration_procedures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('procedure_code', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('instrument_type', sa.String(100)),
        sa.Column('steps', sa.JSON),
        sa.Column('requirements', sa.JSON),
        sa.Column('approval_status', sa.String(20), server_default='DRAFT'),
        sa.Column('approved_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create calibration_records table
    op.create_table(
        'calibration_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id'), nullable=False),
        sa.Column('procedure_id', sa.String(36), sa.ForeignKey('calibration_procedures.id')),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('performed_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('reviewed_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('approved_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('scheduled_date', sa.DateTime(timezone=True)),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('environmental_condition_id', sa.String(36), sa.ForeignKey('environmental_conditions.id')),
        sa.Column('calibration_method', sa.String(100)),
        sa.Column('overall_result', sa.String(20)),
        sa.Column('uncertainty_budget_id', sa.String(36), sa.ForeignKey('uncertainty_budgets.id')),
        sa.Column('certificate_id', sa.String(36), sa.ForeignKey('certificates.id')),
        sa.Column('notes', sa.Text),
        sa.Column('deviation_notes', sa.Text),
        sa.Column('corrective_actions', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create indexes for calibration_records
    op.create_index('idx_calibration_instrument', 'calibration_records', ['instrument_id'])
    op.create_index('idx_calibration_status', 'calibration_records', ['status'])
    op.create_index('idx_calibration_date', 'calibration_records', ['scheduled_date'])
    
    # Create environmental_conditions table
    op.create_table(
        'environmental_conditions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('temperature_celsius', sa.Float, nullable=False),
        sa.Column('temperature_tolerance', sa.Float),
        sa.Column('humidity_percent', sa.Float),
        sa.Column('humidity_tolerance', sa.Float),
        sa.Column('atmospheric_pressure_hpa', sa.Float),
        sa.Column('notes', sa.Text),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('recorded_by_id', sa.String(36), sa.ForeignKey('users.id')),
    )
    
    # Create measurements table
    op.create_table(
        'measurements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('calibration_record_id', sa.String(36), sa.ForeignKey('calibration_records.id'), nullable=False),
        sa.Column('nominal_value', sa.Float, nullable=False),
        sa.Column('measured_value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('error', sa.Float, nullable=False),
        sa.Column('uncertainty', sa.Float),
        sa.Column('tolerance_lower', sa.Float, nullable=False),
        sa.Column('tolerance_upper', sa.Float, nullable=False),
        sa.Column('result', sa.String(20), nullable=False),
        sa.Column('operator_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('measurement_sequence', sa.Integer),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('repeat_number', sa.Integer),
        sa.Column('standard_used_id', sa.String(36), sa.ForeignKey('reference_standards.id')),
        sa.Column('notes', sa.Text),
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('previous_version_id', sa.String(36), sa.ForeignKey('measurements.id')),
        sa.Column('correction_reason', sa.Text),
        sa.Column('corrected_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('corrected_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Add constraint for measurements
    op.create_check_constraint('check_tolerance_order', 'measurements', 'tolerance_lower < tolerance_upper')
    
    # Create indexes for measurements
    op.create_index('idx_measurement_calibration', 'measurements', ['calibration_record_id'])
    op.create_index('idx_measurement_timestamp', 'measurements', ['timestamp'])
    
    # Create calibration_standards table
    op.create_table(
        'calibration_standards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('calibration_record_id', sa.String(36), sa.ForeignKey('calibration_records.id'), nullable=False),
        sa.Column('standard_id', sa.String(36), sa.ForeignKey('reference_standards.id'), nullable=False),
        sa.Column('usage_notes', sa.Text),
    )
    
    # Create reference_standards table
    op.create_table(
        'reference_standards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('asset_number', sa.String(50), unique=True, nullable=False),
        sa.Column('serial_number', sa.String(100), unique=True, nullable=False),
        sa.Column('standard_type', sa.String(100), nullable=False),
        sa.Column('accuracy', sa.Float),
        sa.Column('accuracy_unit', sa.String(20)),
        sa.Column('traceability_number', sa.String(100), nullable=False),
        sa.Column('traceability_chain', sa.JSON),
        sa.Column('calibration_date', sa.DateTime(timezone=True)),
        sa.Column('expiry_date', sa.DateTime(timezone=True)),
        sa.Column('certificate_id', sa.String(36), sa.ForeignKey('certificates.id')),
        sa.Column('status', sa.String(20), server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create uncertainty_budgets table
    op.create_table(
        'uncertainty_budgets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('calibration_record_id', sa.String(36), sa.ForeignKey('calibration_records.id')),
        sa.Column('combined_standard_uncertainty', sa.Float, nullable=False),
        sa.Column('effective_degrees_of_freedom', sa.Float),
        sa.Column('coverage_factor_k', sa.Float, nullable=False),
        sa.Column('expanded_uncertainty', sa.Float, nullable=False),
        sa.Column('confidence_level', sa.Float, server_default='0.95'),
        sa.Column('components', sa.JSON),
        sa.Column('calculation_method', sa.String(50), server_default='GUM'),
        sa.Column('calculation_timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('calculated_by_id', sa.String(36), sa.ForeignKey('users.id')),
    )
    
    # Create certificates table
    op.create_table(
        'certificates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('calibration_record_id', sa.String(36), sa.ForeignKey('calibration_records.id')),
        sa.Column('certificate_number', sa.String(50), unique=True, nullable=False),
        sa.Column('template_id', sa.String(36)),
        sa.Column('language', sa.String(10), server_default='en'),
        sa.Column('status', sa.String(20), server_default='DRAFT'),
        sa.Column('draft_created_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('technical_review_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('approved_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('issue_date', sa.DateTime(timezone=True)),
        sa.Column('valid_until', sa.DateTime(timezone=True)),
        sa.Column('customer_name', sa.String(255)),
        sa.Column('customer_address', sa.Text),
        sa.Column('purchase_order', sa.String(100)),
        sa.Column('digital_signature', sa.Text),
        sa.Column('signature_algorithm', sa.String(50)),
        sa.Column('signed_at', sa.DateTime(timezone=True)),
        sa.Column('signed_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('verification_hash', sa.String(64)),
        sa.Column('verification_qr_url', sa.String(500)),
        sa.Column('revocation_reason', sa.Text),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('revoked_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('pdf_path', sa.String(500)),
        sa.Column('pdf_size_bytes', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create indexes for certificates
    op.create_index('idx_certificate_number', 'certificates', ['certificate_number'])
    op.create_index('idx_certificate_status', 'certificates', ['status'])
    op.create_index('idx_certificate_verification', 'certificates', ['verification_hash'])
    
    # Create deviation_records table
    op.create_table(
        'deviation_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('calibration_record_id', sa.String(36), sa.ForeignKey('calibration_records.id')),
        sa.Column('deviation_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('root_cause', sa.Text),
        sa.Column('immediate_action', sa.Text),
        sa.Column('status', sa.String(20), server_default='OPEN'),
        sa.Column('reported_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('assigned_to_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create corrective_actions table
    op.create_table(
        'corrective_actions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('deviation_id', sa.String(36), sa.ForeignKey('deviation_records.id')),
        sa.Column('action_description', sa.Text, nullable=False),
        sa.Column('responsible_person_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('target_date', sa.DateTime(timezone=True)),
        sa.Column('completion_date', sa.DateTime(timezone=True)),
        sa.Column('effectiveness_verification', sa.Text),
        sa.Column('status', sa.String(20), server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create maintenance_records table
    op.create_table(
        'maintenance_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id'), nullable=False),
        sa.Column('maintenance_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True)),
        sa.Column('performed_date', sa.DateTime(timezone=True)),
        sa.Column('technician_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('status', sa.String(20), server_default='SCHEDULED'),
        sa.Column('cost', sa.Numeric(10, 2)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create audit_events table (immutable ledger)
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_id', sa.String(64), unique=True, nullable=False),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('actor_type', sa.String(20)),
        sa.Column('actor_ip_address', sa.String(50)),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('before_state', sa.JSON),
        sa.Column('after_state', sa.JSON),
        sa.Column('reason', sa.Text),
        sa.Column('application_version', sa.String(20)),
        sa.Column('correlation_id', sa.String(64)),
        sa.Column('request_id', sa.String(64)),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for audit_events
    op.create_index('idx_audit_actor', 'audit_events', ['actor_id'])
    op.create_index('idx_audit_entity', 'audit_events', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_timestamp', 'audit_events', ['timestamp'])
    op.create_index('idx_audit_organization', 'audit_events', ['organization_id'])
    op.create_index('idx_audit_event_id', 'audit_events', ['event_id'])
    
    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255)),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_size_bytes', sa.Integer),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('storage_type', sa.String(20), server_default='local'),
        sa.Column('checksum', sa.String(64)),
        sa.Column('uploaded_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('status', sa.String(20), server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop all tables in reverse order of creation."""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('attachments')
    op.drop_table('audit_events')
    op.drop_table('maintenance_records')
    op.drop_table('corrective_actions')
    op.drop_table('deviation_records')
    op.drop_table('certificates')
    op.drop_table('uncertainty_budgets')
    op.drop_table('reference_standards')
    op.drop_table('calibration_standards')
    op.drop_table('measurements')
    op.drop_table('environmental_conditions')
    op.drop_table('calibration_records')
    op.drop_table('calibration_procedures')
    op.drop_table('instrument_lifecycle_events')
    op.drop_table('instruments')
    op.drop_table('user_permissions')
    op.drop_table('permissions')
    op.drop_table('locations')
    op.drop_table('users')
    op.drop_table('organizations')