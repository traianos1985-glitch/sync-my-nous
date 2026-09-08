import time

from executor.deep_code_analyst import analyze_failure, analyze_latest_diagnosis_deep
from executor.patch_generator import generate_patch_from_analysis, patch_generator_status, list_patch_proposals, approve_patch_proposal, reject_patch_proposal


def run_self_healing_analysis(problem=None):
    if problem is None:
        analysis = analyze_latest_diagnosis_deep()
    else:
        analysis = analyze_failure(problem)

    patch = generate_patch_from_analysis(analysis.get("report", analysis))

    return {
        "ok": True,
        "analysis": analysis,
        "patch_proposal": patch,
        "time": time.time(),
    }


def self_healing_status():
    return {
        "time": time.time(),
        "patch_generator": patch_generator_status(),
        "recent_patch_proposals": list_patch_proposals(10),
    }
