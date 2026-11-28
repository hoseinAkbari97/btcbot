from sqlalchemy.ext.asyncio import AsyncSession
from test_backtest_api import seed_candles
from test_experiment_pipeline import client_for, submit

from app.repositories.backtest import BacktestRepository
from app.repositories.evaluation import EvaluationReportRepository
from app.repositories.experiment import ExperimentRepository
from app.repositories.provenance import RunManifestRepository
from app.services.provenance.verification import verify_report


async def _completed_records(db_session: AsyncSession):
    async with client_for(db_session) as client:
        response = await submit(client)
    assert response.status_code == 201, response.text
    body = response.json()

    experiment = await ExperimentRepository(db_session).get(body["id"])
    run = await BacktestRepository(db_session).get_run_without_trades(
        body["backtest_run_id"]
    )
    report = await EvaluationReportRepository(db_session).get(body["evaluation_report_id"])
    manifest = await RunManifestRepository(db_session).get_for_run(run.id)
    assert experiment is not None and run is not None and report is not None
    return run, report, manifest


async def test_generated_report_verifies_against_its_run_and_manifest(db_session) -> None:
    await seed_candles(db_session)
    run, report, manifest = await _completed_records(db_session)

    result = verify_report(report, run, manifest)

    assert result.status == "verified", result.detail
    assert result.run_id == run.id
    assert result.report_version == "3g.0"
    assert result.evaluation_method_version == "3d.1"
    assert result.manifest_fingerprint is not None
    assert result.stored_digest_matches is True
    assert result.config_fingerprint_matches is True
    assert result.input_fingerprint_matches is True
    assert result.trade_ledger_fingerprint is not None
    assert len(result.canonical_digest or "") == 64


async def test_report_without_a_manifest_is_partial_not_verified(db_session) -> None:
    await seed_candles(db_session)
    run, report, _ = await _completed_records(db_session)

    result = verify_report(report, run, None)

    assert result.status == "partial"
    assert "no immutable manifest" in result.detail
    assert result.stored_digest_matches is True


async def test_tampered_report_content_is_changed(db_session) -> None:
    await seed_candles(db_session)
    run, report, manifest = await _completed_records(db_session)
    report.report["performance"] = {"net_pnl": "999999"}

    result = verify_report(report, run, manifest)

    assert result.status == "changed"
    assert "report_digest" in result.failed_checks


async def test_changed_stored_run_identity_is_changed(db_session) -> None:
    await seed_candles(db_session)
    run, report, manifest = await _completed_records(db_session)
    report.report["provenance"]["run"]["cost_model"]["fee_rate"] = "0.002"

    result = verify_report(report, run, manifest)

    assert result.status == "changed"
    assert "run_identity" in result.failed_checks
    assert "input_fingerprint" in result.failed_checks


async def test_record_method_version_mismatch_is_changed(db_session) -> None:
    await seed_candles(db_session)
    run, report, manifest = await _completed_records(db_session)
    report.method_version = "other"

    result = verify_report(report, run, manifest)

    assert result.status == "changed"
    assert "method_version_record" in result.failed_checks


async def test_unreadable_report_is_corrupted(db_session) -> None:
    await seed_candles(db_session)
    run, report, manifest = await _completed_records(db_session)
    report.report = {}

    result = verify_report(report, run, manifest)

    assert result.status == "corrupted"
    assert result.failed_checks == ("report_structure",)
