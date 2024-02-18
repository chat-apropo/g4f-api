from unittest.mock import Mock

import pytest
from backend import app
from backend.dependencies import all_models, all_working_providers, chat_completion
from fastapi.testclient import TestClient

COMPLETION_PATH = "/api/completions"


def test_api_validation():
    chat = Mock()
    chat.create.return_value = "response"
    app.dependency_overrides[chat_completion] = lambda: chat

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

        # Invalid model
        response = client.post(
            COMPLETION_PATH, params={"model": "Kjf0ajL0gjlskb0K"}, json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert response.status_code == 422

        # Invalid provider
        response = client.post(
            COMPLETION_PATH,
            params={"provider": "xkdjak3jal"},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 422

        # Valid model and provider given together
        response = client.post(
            COMPLETION_PATH,
            params={
                "model": all_models[0],
                "provider": all_working_providers[0],
            },
            json={
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code == 422

        # Both model and provider missing
        response = client.post(COMPLETION_PATH, json={"messages": [{"role": "user", "content": "Hello"}]})
        assert response.status_code == 422

        # Valid request
        response = client.post(
            COMPLETION_PATH,
            params={"model": all_models[0]},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        assert response.json() == {"completion": "response"}


@pytest.mark.parametrize("model", all_models)
@pytest.mark.parametrize("provider", all_working_providers)
def test_all_provider_model_combination(model, provider):
    chat = Mock()
    chat.create.return_value = "response"
    app.dependency_overrides[chat_completion] = lambda: chat

    with TestClient(app) as client:
        response = client.post(
            COMPLETION_PATH,
            params={"model": model},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        assert response.json() == {"completion": "response"}

        response = client.post(
            COMPLETION_PATH,
            params={"provider": provider},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        assert response.json() == {"completion": "response"}
