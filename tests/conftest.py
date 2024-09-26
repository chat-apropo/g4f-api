from typing import Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend import app
from backend.dependencies import chat_completion


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    chat = Mock()
    chat.create.return_value = "response"
    app.dependency_overrides[chat_completion] = lambda: chat

    with TestClient(app) as client:
        yield client
