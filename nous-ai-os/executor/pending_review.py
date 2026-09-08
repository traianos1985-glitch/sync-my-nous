import time


def pending_review_status():
    items = []



    try:
        from executor.upgrade_planner import list_upgrade_plans
        for p in list_upgrade_plans():
            if p.get("status") == "pending":
                items.append({
                    "type": "upgrade_plan",
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "risk": "strategic",
                    "created": p.get("created"),
                    "source": "Upgrade Planner",
                    "action_tab": "upgrades",
                    "data": p,
                })
    except Exception as e:
        items.append({"type": "error", "title": "Upgrade planner error", "error": str(e)})

    try:
        from executor.patch_generator import list_patch_proposals
        for p in list_patch_proposals():
            if p.get("status") == "pending":
                items.append({
                    "type": "patch_proposal",
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "risk": p.get("risk"),
                    "created": p.get("created"),
                    "source": "Patch Generator",
                    "action_tab": "selfheal",
                    "data": p,
                })
    except Exception as e:
        items.append({"type": "error", "title": "Patch proposals error", "error": str(e)})

    try:
        from executor.autonomous_repair import list_repair_proposals
        for p in list_repair_proposals():
            if p.get("status") == "pending":
                items.append({
                    "type": "repair_proposal",
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "risk": p.get("risk"),
                    "created": p.get("created"),
                    "source": "Autonomous Repair",
                    "action_tab": "repair",
                    "data": p,
                })
    except Exception as e:
        items.append({"type": "error", "title": "Repair proposals error", "error": str(e)})

    try:
        from executor.mission_planner import list_mission_proposals
        for p in list_mission_proposals():
            if p.get("status") == "pending":
                items.append({
                    "type": "mission_proposal",
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "risk": p.get("risk"),
                    "created": p.get("created"),
                    "source": "Mission Planner",
                    "action_tab": "planner",
                    "data": p,
                })
    except Exception as e:
        items.append({"type": "error", "title": "Mission proposals error", "error": str(e)})

    try:
        from executor.mission_system import pending_approvals
        approvals = pending_approvals()
        for a in approvals.get("approvals", []):
            items.append({
                "type": "mission_task_approval",
                "id": str(a.get("mission_id")) + ":" + str(a.get("task_id")),
                "title": a.get("task_title"),
                "risk": "approval_required",
                "created": a.get("created"),
                "source": "Mission Approvals",
                "action_tab": "approvals",
                "data": a,
            })
    except Exception as e:
        items.append({"type": "error", "title": "Mission approvals error", "error": str(e)})

    try:
        from executor.executive_intelligence import executive_intelligence_status
        st = executive_intelligence_status()
        n = st.get("next_best_action", {})
        if n and n.get("type") not in [None, "idle"]:
            items.append({
                "type": "executive_recommendation",
                "id": n.get("type") + ":" + n.get("action", ""),
                "title": n.get("title"),
                "risk": "recommendation",
                "created": st.get("time"),
                "source": "Executive Intelligence",
                "action_tab": "intelligence",
                "data": n,
            })
    except Exception as e:
        items.append({"type": "error", "title": "Executive recommendation error", "error": str(e)})

    items = sorted(items, key=lambda x: float(x.get("created") or 0), reverse=True)

    return {
        "time": time.time(),
        "total": len(items),
        "items": items,
        "counts": {
            "repair_proposals": len([x for x in items if x.get("type") == "repair_proposal"]),
            "patch_proposals": len([x for x in items if x.get("type") == "patch_proposal"]),
            "upgrade_plans": len([x for x in items if x.get("type") == "upgrade_plan"]),
            "mission_proposals": len([x for x in items if x.get("type") == "mission_proposal"]),
            "mission_task_approvals": len([x for x in items if x.get("type") == "mission_task_approval"]),
            "executive_recommendations": len([x for x in items if x.get("type") == "executive_recommendation"]),
        }
    }
