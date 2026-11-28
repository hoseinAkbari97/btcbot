from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from test_backtest_api import seed_candles
from test_experiment_pipeline import client_for, submit

from app.repositories.evaluation import EvaluationReportRepository
from app.repositories.experiment import ExperimentRepository


async def _completed_experiment_id(db_session: AsyncSession) -> str:
    await seed_candles(db_session)
    async with client_for(db_session) as client:
        response = await submit(client)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _verification(client, experiment_id: str):
    return await client.get(f"/api/v1/experiments/{experiment_id}/verification")


async def test_completed_experiment_verifies_through_the_api(db_session) -> None:
    experiment_id = await _completed_experiment_id(db_session)

    async with client_for(db_session) as client:
        response = await _verification(client, experiment_id)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["experiment_id"] == experiment_id
    assert body["status"] == "verified"
    assert body["identification"] == "fully_identified"
    assert body["manifest"]["available"] is True
    assert body["manifest"]["fingerprint_matches"] is True
    assert body["manifest"]["link_matches"] is True
    assert body["dataset"]["status"] == "verified"
    assert body["dataset"]["expected_candle_count"] == body["dataset"]["observed_candle_count"]
    assert body["report"]["status"] == "verified"
    assert body["report"]["stored_digest_matches"] is True
    assert any("does not rerun" in item for item in body["limitations"])


async def test_unknown_experiment_is_not_found(db_session) -> None:
    async with client_for(db_session) as client:
        response = await _verification(client, "missing-experiment")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


async def test_experiment_without_linked_artifacts_is_unavailable(db_session) -> None:
    async with client_for(db_session) as client:
        rejected = await submit(client, strategy="random", parameters={"not_a_param": 1})
    assert rejected.status_code == 422, rejected.text
    experiment_id = rejected.json()["detail"]["experiment_id"]

    async with client_for(db_session) as client:
        response = await _verification(client, experiment_id)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "unavailable"
    assert body["identification"] == "not_reproducible"
    assert body["manifest"]["available"] is False
    assert body["dataset"]["status"] == "unavailable"
    assert body["report"] is None


async def test_historical_run_without_manifest_is_partial(db_session) -> None:
    experiment_id = await _completed_experiment_id(db_session)
    await db_session.execute(
        text("DELETE FROM run_manifests WHERE experiment_id = :id"), {"id": experiment_id}
    )
    await db_session.commit()

    async with client_for(db_session) as client:
        response = await _verification(client, experiment_id)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "partial"
    assert body["identification"] == "not_reproducible"
    assert body["manifest"]["available"] is False
    assert body["dataset"]["status"] == "unavailable"
    assert body["report"]["status"] == "partial"
    assert "no immutable manifest" in body["report"]["detail"]


async def test_changed_candles_are_reported_without_rerunning(db_session) -> None:
    experiment_id = await _completed_experiment_id(db_session)
    await db_session.execute(text("UPDATE candles SET close = '9999'"))
    await db_session.commit()

    async with client_for(db_session) as client:
        response = await _verification(client, experiment_id)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "changed"
    assert body["dataset"]["status"] == "changed"
    assert body["dataset"]["observed_fingerprint"] != body["dataset"]["expected_fingerprint"]
    assert body["report"]["status"] == "verified"


async def test_corrupted_stored_report_is_reported(db_session) -> None:
    experiment_id = await _completed_experiment_id(db_session)
    experiment = await ExperimentRepository(db_session).get(experiment_id)
    assert experiment is not None
    report = await EvaluationReportRepository(db_session).get(experiment.evaluation_report_id)
    assert report is not None
    report.report = {}
    await db_session.commit()

    async with client_for(db_session) as client:
        response = await _verification(client, experiment_id)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "corrupted"
    assert body["identification"] == "not_reproducible"
    assert body["report"]["status"] == "corrupted"
    assert body["report"]["failed_checks"] == ["report_structure"]


async def test_broken_artifact_link_is_a_conflict(db_session) -> None:
    experiment_id = await _completed_experiment_id(db_session)
    experiment = await ExperimentRepository(db_session).get(experiment_id)
    assert experiment is not None
    experiment.backtest_run_id = "missing-run"
    await db_session.commit()

    async with client_for(db_session) as client:
        response = await _verification(client, experiment_id)

    assert response.status_code == 409
    assert "missing" in response.json()["detail"]
