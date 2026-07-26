"""Before/after repair comparison with evidence-consistency safeguards."""

WEIGHT = {"Minor": 1, "Moderate": 2, "Severe": 3, "Critical": 4}
MINIMUM_EVIDENCE_SIMILARITY = 0.35


def compare_inspections(
    before_defects,
    before_summary,
    after_defects,
    after_summary,
    evidence_similarity=None,
):
    before_risk = sum(WEIGHT[item["severity"]] for item in before_defects)
    after_risk = sum(WEIGHT[item["severity"]] for item in after_defects)
    change = after_summary["road_health_index"] - before_summary["road_health_index"]

    if evidence_similarity is not None and evidence_similarity < MINIMUM_EVIDENCE_SIMILARITY:
        status = "Evidence mismatch / manual review"
        explanation = (
            "The before-and-after views do not appear similar enough for an automated repair decision. "
            "Upload evidence from the same road location and a comparable camera angle."
        )
    elif after_risk == 0:
        status = "Repair likely completed"
        explanation = "No visible defects were detected after repair. Field inspection should confirm engineering quality."
    elif after_risk < before_risk or change >= 10:
        status = "Partial repair / manual review"
        explanation = "The visual risk profile improved, but visible defects remain. Manual verification is recommended."
    else:
        status = "Repair not verified"
        explanation = "The post-repair image shows similar or higher visible damage. Confirm that the same road location and camera view were used."

    return {
        "status": status,
        "explanation": explanation,
        "health_change": change,
        "before_risk": before_risk,
        "after_risk": after_risk,
        "evidence_similarity": evidence_similarity,
        "comparison_confidence": (
            "Available" if evidence_similarity is not None else "Legacy evidence - visual match unavailable"
        ),
    }
