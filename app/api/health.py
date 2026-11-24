from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health", summary="检查服务进程状态")
async def health() -> dict[str, str]:
    """返回服务进程的存活状态。

    Returns:
        当前 API 进程的存活标记。
    """
    return {"status": "ok"}
