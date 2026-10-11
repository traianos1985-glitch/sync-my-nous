from pathlib import Path

from executor.app_contract_audit import audit_app_builder_contract_sources, audit_repository_app_builder_contract


def ui_source(action_path='/remote/app-builder/test'):
    return '''
  appbuilder: {
    endpoints: [
      { label: "App Builder", path: "/remote/app-builder/status" },
      { label: "Builds", path: "/remote/app-builder/list" },
    ],
    actions: [
      { label: "Test", path: "''' + action_path + '''" },
    ],
  },
  scheduler: {
    endpoints: [],
  },
'''


def test_matching_contract_passes():
    report = audit_app_builder_contract_sources(ui_source(), '''
@app.route("/remote/app-builder/status")
def status():
    pass
@app.route("/remote/app-builder/list")
def builds():
    pass
@app.route("/remote/app-builder/test", methods=["POST"])
def test():
    pass
''')
    assert report["ok"] is True
    assert report["ui_entry_count"] == 3
    assert report["findings"] == []


def test_missing_route_is_reported():
    report = audit_app_builder_contract_sources(ui_source("/remote/app-builder/missing"), '''
@app.route("/remote/app-builder/status")
def status():
    pass
@app.route("/remote/app-builder/list")
def builds():
    pass
''')
    assert report["ok"] is False
    assert any(x["code"] == "ui_route_missing_in_backend" for x in report["findings"])


def test_method_mismatch_is_reported():
    report = audit_app_builder_contract_sources(ui_source(), '''
@app.route("/remote/app-builder/status")
def status():
    pass
@app.route("/remote/app-builder/list")
def builds():
    pass
@app.route("/remote/app-builder/test", methods=["GET"])
def test():
    pass
''')
    assert report["ok"] is False
    assert any(x["code"] == "ui_method_not_supported" for x in report["findings"])


def test_current_repository_contract_passes():
    root = Path(__file__).resolve().parents[2]
    report = audit_repository_app_builder_contract(root)
    assert report["status"] == "passed", report
    assert report["ui_entry_count"] >= 7


def test_missing_source_is_reported_as_unavailable(tmp_path):
    report = audit_repository_app_builder_contract(tmp_path)
    assert report["ok"] is False
    assert report["status"] == "unavailable"
