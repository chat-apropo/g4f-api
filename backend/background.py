import asyncio

from g4f import ProviderType
from g4f.client import AsyncClient
from g4f.stubs import ChatCompletion

from backend.dependencies import base_working_providers_map, provider_and_models
from backend.errors import CustomValidationError

lock = asyncio.Lock()


async def ai_respond(messages: list[dict], model: str, provider: ProviderType) -> str:
    """Generate a response from the AI."""
    client = AsyncClient()
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=messages, model=model, provider=provider, stream=False
    )
    choices = chat_completion.choices
    if len(choices) == 0:
        raise CustomValidationError(
            "No response from the provider", error={"messages": messages}
        )

    return choices[0].message.content


async def test_provider(
    provider: ProviderType, queue: asyncio.Queue, semaphore: asyncio.Semaphore
) -> bool:
    """Sends hi to a provider and check if there is response or error."""
    print(f"Testing provider {provider.__name__}")
    async with semaphore:
        try:
            messages = [{"role": "user", "content": "hi"}]
            if hasattr(provider, "supported_models"):
                model = list(provider.supported_models)[0]
            elif hasattr(provider, "default_model"):
                model = provider.default_model
            elif provider.__name__ in provider_and_models.all_working_providers_map:
                model = list(
                    provider_and_models.all_working_providers_map[
                        provider.__name__
                    ].supported_models
                )[0]
            else:
                model = "gpt-4"
            async with asyncio.timeout(5):
                text = await ai_respond(messages, model, provider=provider)
            result = bool(text) and isinstance(text, str)
        except ValueError:
            result = False
        except asyncio.TimeoutError:
            result = False
        except Exception:
            result = False

        await queue.put((provider, result))
    return result


async def update_working_providers():
    if lock.locked():
        return

    async with lock:
        now_working_providers = set()
        queue = asyncio.Queue()
        providers = list(base_working_providers_map.values())

        async def producer():
            semaphore = asyncio.Semaphore(8)
            await asyncio.gather(
                *[test_provider(provider, queue, semaphore) for provider in providers]
            )
            await queue.join()
            await queue.put((None, None))

        async def consumer():
            async with asyncio.timeout(5 * 60):
                while True:
                    provider, result = await queue.get()
                    if provider is None and result is None:
                        break
                    name = provider.__name__
                    if result:
                        now_working_providers.add(name)
                    queue.task_done()

        await asyncio.gather(producer(), consumer())

        print(
            f"Finished testing providers. Updating working providers to {len(now_working_providers)}"
        )
        provider_and_models.update_model_providers(
            {
                provider_name: base_working_providers_map[provider_name]
                for provider_name in now_working_providers
            }
        )
