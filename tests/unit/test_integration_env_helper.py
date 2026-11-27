import importlib.util
from pathlib import Path
import json
import pytest

path = Path(__file__).resolve().parents[2] / "deployment/clients/integration-env.py"
spec = importlib.util.spec_from_file_location("integration_env", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_dotenv_and_preserve_unrelated_lines():
    assert module.dotenv_value('OTHER=ok\nexport MCP_BOX_API_KEY="synthetic-key" # note\n', "MCP_BOX_API_KEY") == "synthetic-key"
    assert module.replace_entry("# keep\nOTHER=value\nPAI_BOX_MCP_TOKEN=old\n", "PAI_BOX_MCP_TOKEN", "new") == "# keep\nOTHER=value\nPAI_BOX_MCP_TOKEN=new\n"
    with pytest.raises(ValueError):
        module.replace_entry("A=1\nA=2\n", "A", "new")
    with pytest.raises(ValueError):
        module.dotenv_value("A=one\nA=two\n", "A")

def test_optional_beeper_expiry(tmp_path):
    directory = tmp_path / ".hermes-pi/mcp-tokens"
    directory.mkdir(parents=True)
    file = directory / "beeper.json"
    file.write_text(json.dumps({"access_token":"synthetic-token", "expires_at":9999}))
    assert module.read_token(tmp_path, "beeper", 1000) == "synthetic-token"
    with pytest.raises(ValueError):
        module.read_token(tmp_path, "beeper", 9999)
    file.write_text(json.dumps({"access_token":"synthetic-token"}))
    with pytest.raises(ValueError):
        module.read_token(tmp_path, "beeper", 1000)
