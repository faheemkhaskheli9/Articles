import pytest

from sql_guard import sample_db


@pytest.fixture(scope="session")
def db(tmp_path_factory):
    return sample_db.build(tmp_path_factory.mktemp("db") / "shop.db")
