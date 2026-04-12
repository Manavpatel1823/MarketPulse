import asyncio
from typing import Any, Callable, Coroutine


class AgentPool:
    def __init__(self, batch_size: int = 5):
        self.semaphore = asyncio.Semaphore(batch_size)

    async def execute_batch(
        self, tasks: list[Callable[[], Coroutine[Any, Any, Any]]]
    ) -> list[Any]:
        async def limited(task: Callable[[], Coroutine]) -> Any:
            async with self.semaphore:
                return await task()

        return await asyncio.gather(*[limited(t) for t in tasks])
