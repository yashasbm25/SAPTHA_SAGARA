
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from schemas import MarineQueryRequest, APIResponse

router = APIRouter(prefix="/marine", tags=["Marine Intelligence"])


@router.post("/query", response_model=APIResponse)
async def marine_query(request: MarineQueryRequest):
    try:
        # Import lazily so agent dependencies are loaded only when needed.

        from agent import run_agent

        result = await run_in_threadpool(run_agent, request.query)

        return APIResponse(
            success=True,
            message="Marine query processed.",
            data=result,
        )

    except Exception as exc:
        # Log the full exception on the server; avoid exposing secrets.
        print(f"Marine query failed: {type(exc).__name__}: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Unable to process the marine query. Check backend logs.",
        )
