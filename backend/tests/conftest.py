"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.session import Base
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def sample_organization():
    """Sample organization data for testing."""
    return {
        "name": "Test Organization",
        "industry": "Technology",
        "compliance_frameworks": ["ISO27001", "SOC2"],
        "contact_email": "compliance@test.com"
    }


@pytest.fixture
def sample_cloud_account():
    """Sample cloud account data for testing."""
    return {
        "organization_id": 1,
        "name": "Test AWS Account",
        "provider": "aws",
        "account_id": "123456789012",
        "region": "us-east-1",
        "credentials": {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole"
        }
    }


@pytest.fixture
def sample_control():
    """Sample control data for testing."""
    return {
        "control_id": "TEST-001",
        "title": "Test Control",
        "description": "Test control description",
        "category": "Testing",
        "severity": "high",
        "frameworks": {"ISO27001": ["A.1.1"]},
        "provider": "aws",
        "can_auto_remediate": True,
        "remediation_risk": "low"
    }
