"""Tests for the special agent, its server-side call and its rule form.

Naming chain: rule_spec_special_agent_oposs_isam_alarm (rulesets) ->
special_agent_oposs_isam_alarm (server_side_calls) ->
libexec/agent_oposs_isam_alarm (the script Checkmk runs).
"""

import importlib.util
import pathlib
import subprocess
import sys
import types
from importlib.machinery import SourceFileLoader

import pytest
import requests
from cmk.server_side_calls.v1 import HostConfig, IPv4Config, SpecialAgentCommand

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "local/lib/python3/cmk_addons/plugins/oposs_isam_alarm"
AGENT = PLUGIN / "libexec/agent_oposs_isam_alarm"

# What the collector answers for one ISAM (see test_check.py)
BODY = (
    "<<<isam_alarm_status:sep(0)>>>\n"
    '{"info":"No active alarms","service":"Equip[1]/shub-loc[8]","status":0}\n'
)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def agent(monkeypatch):
    # cmk.utils is part of the Checkmk monolith, not of the API packages
    calls = []
    password_store = types.ModuleType("cmk.utils.password_store")
    password_store.replace_passwords = lambda: calls.append("replace_passwords")
    monkeypatch.setitem(sys.modules, "cmk.utils", types.ModuleType("cmk.utils"))
    monkeypatch.setitem(sys.modules, "cmk.utils.password_store", password_store)
    loader = SourceFileLoader("agent_oposs_isam_alarm", str(AGENT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.calls = calls
    return module


class _Response:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


def test_agent_passes_the_collector_answer_through(agent, monkeypatch, capsys):
    seen = {}

    def get(url, **kwargs):
        seen.update(url=url, **kwargs)
        return _Response(BODY)

    monkeypatch.setattr(agent.requests, "get", get)
    assert agent.main(["https://collector.example.com:8443/isam/10.1.2.3"]) == 0
    assert capsys.readouterr().out == BODY
    assert seen == {"url": "https://collector.example.com:8443/isam/10.1.2.3", "timeout": 30}
    assert agent.calls == ["replace_passwords"]


def test_agent_fails_on_http_error(agent, monkeypatch, capsys):
    # The collector answers 404 "Not Found" for a path without an address
    monkeypatch.setattr(agent.requests, "get", lambda url, **kw: _Response("Not Found", 404))
    with pytest.raises(requests.HTTPError):
        agent.main(["https://collector.example.com:8443/isam/"])
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("args", [[], ["a", "b"]])
def test_agent_usage(agent, monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["agent_oposs_isam_alarm", *args])
    monkeypatch.setattr(agent.requests, "get", lambda *a, **k: pytest.fail("must not fetch"))
    assert agent.main() == 1
    assert "Usage: agent_oposs_isam_alarm URL" in capsys.readouterr().err


def test_agent_empty_argv_is_not_replaced_by_sys_argv(agent, monkeypatch, capsys):
    # An explicit empty argument list is a usage error, even when the
    # process itself was started with a URL
    monkeypatch.setattr(sys, "argv", ["agent_oposs_isam_alarm", "https://collector.example.com:8443/isam/10.1.2.3"])
    monkeypatch.setattr(agent.requests, "get", lambda *a, **k: pytest.fail("must not fetch"))
    assert agent.main([]) == 1
    assert "Usage: agent_oposs_isam_alarm URL" in capsys.readouterr().err


def test_agent_is_executable_in_git():
    # Checkmk runs the special agent as a program
    mode = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-s", str(AGENT.relative_to(ROOT))],
                          capture_output=True, text=True, check=True).stdout.split()[0]
    assert mode == "100755"


@pytest.fixture(scope="module")
def ssc():
    return _load(PLUGIN / "server_side_calls/isam_alarm.py", "test_oposs_isam_alarm_ssc")


def _host(address):
    return HostConfig(name="isam-olt-01", ipv4_config=IPv4Config(address=address))


def test_command_appends_the_host_address(ssc):
    # Checkmk calls the config with the rule's value and the host
    config = ssc.special_agent_oposs_isam_alarm
    assert list(config({"collector": "https://collector.example.com:8443/isam"}, _host("10.1.2.3"))) == [
        SpecialAgentCommand(command_arguments=["https://collector.example.com:8443/isam/10.1.2.3"]),
    ]


def test_parameter_parser_needs_a_collector(ssc):
    with pytest.raises(ValueError):
        list(ssc.special_agent_oposs_isam_alarm({}, _host("10.1.2.3")))


def test_names_line_up(ssc):
    rulesets = _load(PLUGIN / "rulesets/isam_alarm.py", "test_oposs_isam_alarm_rulesets")
    rule = rulesets.rule_spec_special_agent_oposs_isam_alarm
    assert rule.name == ssc.special_agent_oposs_isam_alarm.name == "oposs_isam_alarm"
    assert AGENT.name == "agent_" + rule.name


def test_rule_form_has_a_required_collector_url():
    from cmk.rulesets.v1.form_specs import String, validators

    rulesets = _load(PLUGIN / "rulesets/isam_alarm.py", "test_oposs_isam_alarm_rulesets")
    form = rulesets.rule_spec_special_agent_oposs_isam_alarm.parameter_form()
    assert set(form.elements) == {"collector"}
    element = form.elements["collector"]
    assert element.required
    assert isinstance(element.parameter_form, String)
    assert any(isinstance(v, validators.LengthInRange) for v in element.parameter_form.custom_validate)
