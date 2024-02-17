from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from backend import app
from backend.dependencies import chat_completion, all_models, all_working_providers


def test_api_validation():
    chat = Mock()
    chat.create.return_value = "response"
    app.dependency_overrides[chat_completion] = lambda: chat

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

        # Invalid model
        response = client.post(
            "/", params={"model": "gpt-scheisse"}, json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert response.status_code == 422

        # Invalid provider
        response = client.post(
            "/", params={"provider": "xkdjak3jal"}, json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert response.status_code == 422

        # Valid model and provider given together
        response = client.post(
            "/",
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
        response = client.post("/", json={"messages": [{"role": "user", "content": "Hello"}]})
        assert response.status_code == 422

        # Valid request
        response = client.post(
            "/",
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
            "/",
            params={"model": model},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        assert response.json() == {"completion": "response"}

        response = client.post(
            "/",
            params={"provider": provider},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        assert response.json() == {"completion": "response"}
