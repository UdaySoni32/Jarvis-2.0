"""Phase 3.5 regression checks for API route compatibility."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGINS_ROUTE = ROOT / "src" / "api" / "routes" / "plugins.py"
WEBSOCKET_ROUTE = ROOT / "src" / "api" / "routes" / "websocket.py"


def test_plugin_static_routes_before_dynamic_route():
    content = PLUGINS_ROUTE.read_text(encoding="utf-8")
    assert content.index('@plugins_router.get("/categories"') < content.index('@plugins_router.get("/{plugin_name}"')
    assert content.index('@plugins_router.get("/stats"') < content.index('@plugins_router.get("/{plugin_name}"')


def test_plugin_execution_uses_core_tool_executor():
    content = PLUGINS_ROUTE.read_text(encoding="utf-8")
    assert "from ...core.tools.executor import tool_executor" in content
    assert "from ...plugins.executor import PluginExecutor" not in content
    assert 'execution_params = {"action": execution_request.action, **execution_request.parameters}' in content


def test_websocket_has_connection_limit_and_model_scoping():
    content = WEBSOCKET_ROUTE.read_text(encoding="utf-8")
    assert "settings.websocket_max_connections" in content
    assert 'model_kwargs = {"model": chat_data.model} if chat_data.model else {}' in content
    assert "llm_manager.set_model(chat_data.model)" not in content
    assert '"online_users": len(manager.get_online_users())' in content
