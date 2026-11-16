import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-factoryshield-tests")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://factoryshield:factoryshield@localhost:5432/factoryshield_test")
