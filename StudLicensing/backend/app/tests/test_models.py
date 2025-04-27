import pytest
import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from logger import logger



@pytest.fixture(scope="function")
def test_db():
    # Setup in-memory test DB
    engine = create_engine("postgresql://YOUR_POSTGRESQL_USER:YOUR_POSTGRESQL_PASSWORD@localhost:5432/StudLicensing")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    logger.info("Tests run complete-----------------------------------------------------------------")