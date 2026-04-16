import asyncio
from typing import Any, Callable, Coroutine


class AgentPool:
    def __init__(self, batch_size: int = 5):
        self.semaphore = asyncio.Semaphore(batch_size)

    async def execute_batch(
        self, tasks: list[Callable[[], Coroutine[Any, Any, Any]]]
    ) -> list[Any]:
        """Run tasks under a concurrency semaphore.

        Uses `return_exceptions=True` so that one failure (e.g. rate-limit
        exhaustion after full retry) doesn't abort the batch and waste the
        tokens already spent on successful calls. Failed tasks return their
        exception object — callers that care should filter or log.
        """
        async def limited(task: Callable[[], Coroutine]) -> Any:
            async with self.semaphore:
                try:
                    return await task()
                except Exception as e:
                    print(f"  [batch-task-failed] {type(e).__name__}: {e}")
                    return e

        return await asyncio.gather(*[limited(t) for t in tasks], return_exceptions=False)
