from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.repository import Repository
from app.schemas import (
    CheckResponse,
    DashboardResponse,
    HealthResponse,
    TargetCreate,
    TargetResponse,
    TargetUpdate,
)
from app.services.monitoring import check_target

router = APIRouter(prefix="/api")


def get_repository(request: Request) -> Repository:
    return request.app.state.repository


def require_write_access(request: Request) -> None:
    expected_key = request.app.state.settings.api_key
    if expected_key and request.headers.get("X-API-Key") != expected_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный API-ключ")


def serialize_target(target, repository: Repository) -> TargetResponse:
    last = repository.last_check(target.checks)
    return TargetResponse(
        id=target.id,
        name=target.name,
        kind=target.kind,
        url=target.url,
        host=target.host,
        port=target.port,
        enabled=target.enabled,
        interval_seconds=target.interval_seconds,
        timeout_seconds=target.timeout_seconds,
        created_at=target.created_at,
        updated_at=target.updated_at,
        last_check=CheckResponse.model_validate(last) if last else None,
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        monitoring_enabled=settings.monitoring_enabled,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(repository: Repository = Depends(get_repository)):
    return repository.dashboard()


@router.get("/targets", response_model=list[TargetResponse])
def list_targets(repository: Repository = Depends(get_repository)):
    targets = repository.list_targets()
    return [serialize_target(target, repository) for target in targets]


@router.post(
    "/targets",
    response_model=TargetResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write_access)],
)
def create_target(payload: TargetCreate, repository: Repository = Depends(get_repository)):
    target = repository.create_target(payload)
    return serialize_target(target, repository)


@router.patch(
    "/targets/{target_id}",
    response_model=TargetResponse,
    dependencies=[Depends(require_write_access)],
)
def update_target(
    target_id: int,
    payload: TargetUpdate,
    repository: Repository = Depends(get_repository),
):
    target = repository.update_target(target_id, payload)
    if target is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return serialize_target(target, repository)


@router.delete(
    "/targets/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_write_access)],
)
def delete_target(target_id: int, repository: Repository = Depends(get_repository)):
    if not repository.delete_target(target_id):
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/targets/{target_id}/check",
    response_model=CheckResponse,
    dependencies=[Depends(require_write_access)],
)
async def run_check(target_id: int, repository: Repository = Depends(get_repository)):
    target = repository.get_target(target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    outcome = await check_target(repository.to_snapshot(target))
    return repository.record_check(target_id, outcome)


@router.get("/targets/{target_id}/history", response_model=list[CheckResponse])
def target_history(
    target_id: int,
    limit: int = 50,
    repository: Repository = Depends(get_repository),
):
    if repository.get_target(target_id) is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    safe_limit = min(max(limit, 1), 200)
    return repository.get_history(target_id, safe_limit)

