from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend import app
from backend.dependencies import chat_completion, provider_and_models

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
            COMPLETION_PATH,
            params={"model": "Kjf0ajL0gjlskb0K"},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 422

        # Invalid provider
        response = client.post(
            COMPLETION_PATH,
            params={"provider": "xkdjak3jal"},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 422

        model = list(
            provider_and_models.all_working_providers_map[
                provider_and_models.all_working_provider_names[0]
            ].supported_models
        )[0]
        provider = provider_and_models.all_working_provider_names[0]

        # Valid model and provider given together
        response = client.post(
            COMPLETION_PATH,
            params={
                "model": model,
                "provider": provider,
            },
            json={
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "completion": "response",
            "model": model,
            "provider": provider,
        }

        # Both model and provider missing
        response = client.post(
            COMPLETION_PATH, json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert response.status_code == 200
        assert response.json()["model"]
        assert response.json()["provider"]

        # Valid request
        response = client.post(
            COMPLETION_PATH,
            params={"model": provider_and_models.all_model_names[0]},
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        assert response.json()["completion"] == "response"


@pytest.mark.parametrize("model", sorted(provider_and_models.all_model_names))
def test_all_models(client: TestClient, model: str) -> None:
    response = client.post(
        COMPLETION_PATH,
        params={"model": model},
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
    assert response.json()["completion"] == "response"


@pytest.mark.parametrize(
    "provider", sorted(provider_and_models.all_working_provider_names)
)
def test_all_providers(client: TestClient, provider: str) -> None:
    response = client.post(
        COMPLETION_PATH,
        params={"provider": provider},
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
    assert response.json()["completion"] == "response"


@pytest.mark.parametrize("model", sorted(provider_and_models.all_model_names))
@pytest.mark.parametrize(
    "provider", sorted(provider_and_models.all_working_provider_names)
)
def test_all_provider_model_combination(
    client: TestClient, model: str, provider: str
) -> None:
    model_supported = (
        model
        in provider_and_models.all_working_providers_map[provider].supported_models
    )
    response = client.post(
        COMPLETION_PATH,
        params={"provider": provider, "model": model},
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    if model_supported:
        assert response.status_code == 200
        assert response.json()["completion"] == "response"
    else:
        assert response.status_code == 422
