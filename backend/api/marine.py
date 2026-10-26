
import traceback

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from schemas import MarineQueryRequest, APIResponse

router = APIRouter(prefix="/marine", tags=["Marine Intelligence"])


@router.post("/query", response_model=APIResponse)
async def marine_query(request: MarineQueryRequest):
    try:
        # agent.py is located in agents/exp/.
        from agent import run_agent

        result = await run_in_threadpool(run_agent, request.query)

        if result is None:
            raise RuntimeError(
                "run_agent() returned None. "
                "Update run_agent() to return its final response."
            )

        return APIResponse(
            success=True,
            message="Marine query processed successfully.",
            data=result,
        )

    except Exception as exc:
        print(f"\nMarine query failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="Unable to process the marine query. Check backend logs.",
        ) from exc
