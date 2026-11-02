
import traceback

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from schemas import RouteRequest, APIResponse

router = APIRouter(prefix="/route", tags=["Route Planning"])


@router.post("/plan", response_model=APIResponse)
async def plan_route(request: RouteRequest):
    try:
        from agent import run_route_planning

        result = await run_in_threadpool(
            run_route_planning,
            request.origin,
            request.destination,
        )

        if result is None:
            raise RuntimeError(
                "run_route_planning() returned None. "
                "Update it to return the route result."
            )

        return APIResponse(
            success=True,
            message="Route analysis completed.",
            data=result,
        )

    except Exception as exc:
        print(f"\nRoute planning failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="Unable to plan the route. Check backend logs.",
        ) from exc
