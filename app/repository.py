from collections.abc import Iterable

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.models import CheckResult, Target
from app.schemas import TargetCreate, TargetUpdate
from app.services.monitoring import CheckOutcome, TargetSnapshot


class Repository:
    """Small data-access layer. API and scheduler do not work with SQL directly."""

    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def create_target(self, payload: TargetCreate) -> Target:
        with self.session_factory() as session:
            target = Target(
                name=payload.name,
                kind=payload.kind.value,
                url=str(payload.url) if payload.url else None,
                host=payload.host,
                port=payload.port,
                enabled=payload.enabled,
                interval_seconds=payload.interval_seconds,
                timeout_seconds=payload.timeout_seconds,
            )
            session.add(target)
            session.commit()
            return session.scalar(
                select(Target)
                .options(selectinload(Target.checks))
                .where(Target.id == target.id)
            )

    def get_target(self, target_id: int, with_checks: bool = False) -> Target | None:
        with self.session_factory() as session:
            statement = select(Target).where(Target.id == target_id)
            if with_checks:
                statement = statement.options(selectinload(Target.checks))
            return session.scalar(statement)

    def list_targets(self) -> list[Target]:
        with self.session_factory() as session:
            statement = select(Target).options(selectinload(Target.checks)).order_by(Target.id.desc())
            return list(session.scalars(statement).all())

    def list_enabled_snapshots(self) -> list[TargetSnapshot]:
        with self.session_factory() as session:
            targets = session.scalars(select(Target).where(Target.enabled.is_(True))).all()
            return [self.to_snapshot(target) for target in targets]

    def update_target(self, target_id: int, payload: TargetUpdate) -> Target | None:
        with self.session_factory() as session:
            target = session.get(Target, target_id)
            if target is None:
                return None
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(target, field, value)
            session.commit()
            return session.scalar(
                select(Target)
                .options(selectinload(Target.checks))
                .where(Target.id == target.id)
            )

    def delete_target(self, target_id: int) -> bool:
        with self.session_factory() as session:
            target = session.get(Target, target_id)
            if target is None:
                return False
            session.delete(target)
            session.commit()
            return True

    def record_check(self, target_id: int, outcome: CheckOutcome) -> CheckResult:
        with self.session_factory() as session:
            result = CheckResult(
                target_id=target_id,
                status=outcome.status,
                latency_ms=outcome.latency_ms,
                status_code=outcome.status_code,
                error=outcome.error,
            )
            session.add(result)
            session.commit()
            session.refresh(result)
            return result

    def get_history(self, target_id: int, limit: int = 50) -> list[CheckResult]:
        with self.session_factory() as session:
            statement = (
                select(CheckResult)
                .where(CheckResult.target_id == target_id)
                .order_by(desc(CheckResult.checked_at))
                .limit(limit)
            )
            return list(session.scalars(statement).all())

    def dashboard(self) -> dict[str, int]:
        targets = self.list_targets()
        last_checks = [self.last_check(target.checks) for target in targets]
        return {
            "total": len(targets),
            "enabled": sum(target.enabled for target in targets),
            "up": sum(check is not None and check.status for check in last_checks),
            "down": sum(check is not None and not check.status for check in last_checks),
            "never_checked": sum(check is None for check in last_checks),
        }

    @staticmethod
    def last_check(checks: Iterable[CheckResult]) -> CheckResult | None:
        return max(checks, key=lambda item: item.checked_at, default=None)

    @staticmethod
    def to_snapshot(target: Target) -> TargetSnapshot:
        return TargetSnapshot(
            id=target.id,
            kind=target.kind,
            url=target.url,
            host=target.host,
            port=target.port,
            timeout_seconds=target.timeout_seconds,
            interval_seconds=target.interval_seconds,
        )

