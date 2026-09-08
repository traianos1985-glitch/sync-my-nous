from flask import Blueprint, request
from executor.agent_v2 import run
from executor.plugin_registry import list_plugins

ui = Blueprint("ui", __name__)

@ui.route("/run", methods=["POST"])
def run_route():
    data = request.json
    return run(data.get("goal",""))

@ui.route("/plugins")
def plugins():
    return {"plugins": list_plugins()}
