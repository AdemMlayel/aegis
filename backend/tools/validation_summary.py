from __future__ import annotations

from typing import Any

from backend.graph.state import (
    AutomationBlock,
    CoveragePlan,
    RequirementAnalysis,
    TestCase,
    ValidationSummary,
)
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="ValidationSummaryTool",
    isolation="in_process",
    description=(
        "Builds deterministic validation quality, traceability, and risk metrics "
        "from Robot validation results."
    ),
)
class ValidationSummaryTool(BaseTool):
    def invoke(self, **kwargs: Any) -> ValidationSummary:
        automation = kwargs.get("automation")
        test_cases = kwargs.get("test_cases")
        coverage_plan = kwargs.get("coverage_plan")
        requirement_analysis = kwargs.get("requirement_analysis")
        retry_count = kwargs.get("retry_count", 0)
        max_retries = kwargs.get("max_retries", 0)

        if not isinstance(automation, dict) or not all(
            isinstance(block, AutomationBlock) for block in automation.values()
        ):
            raise TypeError(
                "ValidationSummaryTool requires dict[str, AutomationBlock]"
            )
        if not isinstance(test_cases, list) or not all(
            isinstance(test_case, TestCase) for test_case in test_cases
        ):
            raise TypeError("ValidationSummaryTool requires list[TestCase]")
        if coverage_plan is not None and not isinstance(coverage_plan, CoveragePlan):
            raise TypeError("coverage_plan must be CoveragePlan or None")
        if (
            requirement_analysis is not None
            and not isinstance(requirement_analysis, RequirementAnalysis)
        ):
            raise TypeError(
                "requirement_analysis must be RequirementAnalysis or None"
            )
        if not isinstance(retry_count, int) or not isinstance(max_retries, int):
            raise TypeError("retry counts must be integers")

        return build_validation_summary(
            automation=automation,
            test_cases=test_cases,
            coverage_plan=coverage_plan,
            requirement_analysis=requirement_analysis,
            retry_count=retry_count,
            max_retries=max_retries,
        )


def build_validation_summary(
    *,
    automation: dict[str, AutomationBlock],
    test_cases: list[TestCase],
    coverage_plan: CoveragePlan | None,
    requirement_analysis: RequirementAnalysis | None,
    retry_count: int,
    max_retries: int,
) -> ValidationSummary:
    total_artifacts = len(automation)
    passed_artifacts = sum(
        1
        for block in automation.values()
        if (
            block.validation.artifact_exists
            and block.data_reference_check_passed
            and block.validation.dry_run_passed is True
        )
    )
    failed_artifacts = total_artifacts - passed_artifacts
    data_passed = sum(
        1 for block in automation.values() if block.data_reference_check_passed
    )
    total_attempts = sum(
        block.validation.validation_attempts for block in automation.values()
    )

    test_cases_by_id = {test_case.id: test_case for test_case in test_cases}
    missing_requirements: list[str] = []
    coverage_matrix = coverage_plan.coverage_matrix if coverage_plan else {}
    for requirement, mapped_test_ids in coverage_matrix.items():
        requirement_ref = requirement.split(maxsplit=1)[0]
        traceable = any(
            test_case_id in automation
            and test_case_id in test_cases_by_id
            and requirement_ref
            in test_cases_by_id[test_case_id].requirement_refs
            for test_case_id in mapped_test_ids
        )
        if not traceable:
            missing_requirements.append(requirement)

    requirement_total = len(coverage_matrix)
    requirement_coverage_percent = _percent(
        requirement_total - len(missing_requirements),
        requirement_total,
        empty_default=100 if test_cases else 0,
    )
    artifact_pass_percent = _percent(
        passed_artifacts,
        total_artifacts,
    )
    data_reference_percent = _percent(
        data_passed,
        total_artifacts,
    )
    missing_fields = (
        requirement_analysis.missing_fields if requirement_analysis else []
    )
    requirement_completeness_percent = max(0, 100 - (len(missing_fields) * 20))
    quality_score = round(
        (requirement_coverage_percent * 0.35)
        + (artifact_pass_percent * 0.40)
        + (data_reference_percent * 0.15)
        + (requirement_completeness_percent * 0.10)
    )

    fallback_count = sum(
        1
        for block in automation.values()
        if block.validation.dry_run_skipped_reason is not None
    )
    validator_mode = _validator_mode(
        total_artifacts=total_artifacts,
        fallback_count=fallback_count,
    )
    risk_areas = [
        *(
            [f"{len(missing_requirements)} planned requirement(s) lack traceability."]
            if missing_requirements
            else []
        ),
        *(
            [f"{failed_artifacts} automation artifact(s) failed validation."]
            if failed_artifacts
            else []
        ),
        *(
            [f"{total_artifacts - data_passed} artifact(s) lack resolved test data."]
            if data_passed < total_artifacts
            else []
        ),
        *(f"Requirement gap: {field}" for field in missing_fields),
        *(
            [
                "Robot Framework CLI was unavailable; local structural "
                "validation was used."
            ]
            if fallback_count
            else []
        ),
    ]
    if failed_artifacts or missing_requirements:
        status = "failed"
    elif risk_areas:
        status = "warning"
    else:
        status = "passed"

    return ValidationSummary(
        status=status,
        total_artifacts=total_artifacts,
        passed_artifacts=passed_artifacts,
        failed_artifacts=failed_artifacts,
        requirement_coverage_percent=requirement_coverage_percent,
        artifact_pass_percent=artifact_pass_percent,
        data_reference_percent=data_reference_percent,
        requirement_completeness_percent=requirement_completeness_percent,
        quality_score=quality_score,
        missing_requirements=missing_requirements,
        risk_areas=risk_areas,
        validator_mode=validator_mode,
        total_attempts=total_attempts,
        retry_count=retry_count,
        max_retries=max_retries,
    )


def _percent(numerator: int, denominator: int, *, empty_default: int = 0) -> int:
    if denominator == 0:
        return empty_default
    return round((numerator / denominator) * 100)


def _validator_mode(*, total_artifacts: int, fallback_count: int) -> str:
    if total_artifacts == 0:
        return "not_run"
    if fallback_count == total_artifacts:
        return "local_structural"
    if fallback_count:
        return "mixed"
    return "robot_dry_run"
