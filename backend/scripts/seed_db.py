"""Database seeding script - creates initial admin user and sample data."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.models.user import User
from app.models.organization import Organization
from app.models.control import Control


async def seed_database():
    """Seed the database with initial data."""
    print("🌱 Seeding database...")
    
    async with async_session_maker() as session:
        # Create admin user
        admin = User(
            email='admin@example.com',
            hashed_password=get_password_hash('admin123'),
            full_name='Admin User',
            role='admin',
            is_active=True
        )
        session.add(admin)
        
        # Create sample organization
        org = Organization(
            name='Demo Organization',
            industry='Technology',
            compliance_frameworks=['ISO27001', 'SOC2', 'GDPR'],
            contact_email='compliance@demo.com',
            is_active=True
        )
        session.add(org)
        
        # Create sample controls
        controls_data = [
            {
                'control_id': 'AWS-IAM-001',
                'title': 'MFA Required',
                'description': 'MFA must be enabled',
                'category': 'IAM',
                'severity': 'critical',
                'frameworks': {'ISO27001': ['A.9.2.1'], 'SOC2': ['CC6.1']},
                'provider': 'aws',
                'can_auto_remediate': False
            },
            {
                'control_id': 'AWS-S3-001',
                'title': 'Block Public Access',
                'description': 'S3 buckets must block public access',
                'category': 'Storage',
                'severity': 'critical',
                'frameworks': {'ISO27001': ['A.13.1.3'], 'GDPR': ['Art.32']},
                'provider': 'aws',
                'can_auto_remediate': True,
                'remediation_risk': 'high'
            },
        ]
        
        for ctrl_data in controls_data:
            control = Control(**ctrl_data)
            session.add(control)
        
        await session.commit()
        print("✅ Database seeded successfully!")
        print("\n📋 Created:")
        print("  - Admin user: admin@example.com / admin123")
        print("  - Sample organization")
        print(f"  - {len(controls_data)} controls")


if __name__ == '__main__':
    asyncio.run(seed_database())
