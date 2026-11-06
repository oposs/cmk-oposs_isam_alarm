"""Tests for the ISAM alarm check plugin, fed with collector output.

The section comes from the isam-alarm-collector daemon
(lib/IsamAlarmCollector/Server/CheckMk.pm). It answers
`GET {collector}/{ip}` with `<<<isam_alarm_status:sep(0)>>>` and then one
compact JSON object per configured alarm, keys sorted (Mojo::JSON):
`service` is "<Type>[<type id>]/<CliName>[<number id>]", `status` is 2
for an active alarm and 0 otherwise, and `info` is "No active alarms" or a
multi-line description of the alarm. With sep(0), Checkmk hands each line
to the parse function as a one-element list.
"""

import importlib.util
import json
import pathlib
import re
import sys

import pytest
from cmk.agent_based.v2 import Result, Service, State

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = ROOT / "local/lib/python3/cmk_addons/plugins/oposs_isam_alarm/agent_based/oposs_isam_alarm.py"

QUIET = "Equip[1]/shub-loc[8]"
ACTIVE = "OLT General[45]/olt-gen-deact-hightca[20]"

# The info text the collector builds for an active alarm (the INFO_END
# heredoc plus one line per active instance)
ACTIVE_INFO = (
    "Deactivated ONU amount has crossed the high threshold. [2026-11-05 14:12:09]\n"
    "Category: Equ\n"
    "Severity: Crit\n"
    "Service Affecting: N\n"
    "Description: Deactivated ONU amount has crossed the high threshold.\n"
    "Repair: Check the reason that the ONUs under the PON are deactivated.\n"
    "\n"
    "2026-11-05 14:12:09 - Idx1:4352/Idx2:0 \n"
)

# Collector lines, exactly as Mojo::JSON encodes them
COLLECTOR_LINES = [
    '{"info":"No active alarms","service":"Equip[1]/shub-loc[8]","status":0}',
    '{"info":' + json.dumps(ACTIVE_INFO) + ',"service":"OLT General[45]/olt-gen-deact-hightca[20]","status":2}',
    '{"info":"No active alarms","service":"Ethernet Ring[235]/ethernet-ring-pthfwst[1]","status":0}',
]
STRING_TABLE = [[line] for line in COLLECTOR_LINES]


@pytest.fixture(scope="module")
def check():
    name = "test_oposs_isam_alarm_check"
    spec = importlib.util.spec_from_file_location(name, CHECK)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def section(check):
    return check.parse_info(STRING_TABLE)


def test_parse_keys_by_service(section):
    assert list(section) == [
        "Equip[1]/shub-loc[8]",
        "OLT General[45]/olt-gen-deact-hightca[20]",
        "Ethernet Ring[235]/ethernet-ring-pthfwst[1]",
    ]


def test_discovery_one_service_per_alarm(check, section):
    assert list(check.discover_alarms(section)) == [Service(item=item) for item in section]


def test_discovery_of_empty_section(check):
    assert list(check.discover_alarms(check.parse_info([]))) == []


def test_quiet_alarm_is_ok(check, section):
    (result,) = check.check_alarms(QUIET, section)
    assert result.state == State.OK
    # OK keeps the summary empty and shows the text in the details only
    assert result.summary == ""
    assert result.details == "No active alarms"


def test_active_alarm_is_crit_with_full_info(check, section):
    (result,) = check.check_alarms(ACTIVE, section)
    assert result.state == State.CRIT
    assert result.details == ACTIVE_INFO
    assert "\n" not in result.summary
    assert result.summary.startswith("Deactivated ONU amount has crossed the high threshold. [2026-11-05 14:12:09]")
    assert "Severity: Crit" in result.summary


@pytest.mark.parametrize("status, state", [
    (0, State.OK),
    (1, State.WARN),
    (2, State.CRIT),
    (3, State.UNKNOWN),
])
def test_status_maps_to_state(check, status, state):
    line = json.dumps({"info": "something", "service": "Equip[1]/shub-loc[8]", "status": status})
    (result,) = check.check_alarms("Equip[1]/shub-loc[8]", check.parse_info([[line]]))
    assert result == Result(state=state, notice="something")


def test_vanished_item_yields_nothing(check, section):
    # Checkmk then reports the service as UNKNOWN, "Item not found"
    assert list(check.check_alarms("Equip[1]/timing-reference[6]", section)) == []


def test_service_name_and_section(check):
    plugin = check.check_plugin_oposs_isam_alarm
    assert plugin.service_name == "ISAM Alarm State - %s"
    assert list(plugin.sections) == ["isam_alarm_status"]
    assert check.agent_section_isam_alarm_status.name == "isam_alarm_status"


def test_no_metrics(check, section):
    for item in section:
        assert all(isinstance(r, Result) for r in check.check_alarms(item, section))


@pytest.mark.parametrize("bad", [
    "<html><body>Bad Gateway</body></html>",
    '{"info":"No active alarms","service":"Equip[1]/shub-l',
    '{"info":"No active alarms","service":"Equip[1]/shub-loc[8]","status":4}',
    '{"service":"Equip[1]/shub-loc[8]","status":0}',
])
def test_bad_line_does_not_take_the_other_alarms_down(check, bad):
    section = check.parse_info([[COLLECTOR_LINES[1]], [bad]])
    (result,) = check.check_alarms(ACTIVE, section)
    assert result.state == State.CRIT


@pytest.mark.parametrize("bad", [
    "<html><body>Bad Gateway</body></html>",
    '{"info":"No active alarms","service":"Equip[1]/shub-l',
    '{"service":"Equip[1]/shub-loc[8]","status":0}',
    '{"info":"","service":"Equip[1]/shub-loc[8]","status":0}',
    '{"info":"No active alarms","status":0}',
    '["Equip[1]/shub-loc[8]",0]',
])
def test_unreadable_line_is_skipped(check, bad):
    assert check.parse_info([[bad]]) == {}


@pytest.mark.parametrize("status", [4, -1, "2", None, True, [1], {}])
def test_unknown_status_is_unknown(check, status):
    line = json.dumps({"info": "No active alarms", "service": QUIET, "status": status})
    (result,) = check.check_alarms(QUIET, check.parse_info([[line]]))
    assert result.state == State.UNKNOWN
    assert result.summary == f"Collector sent unknown alarm status {status!r}"
    assert result.details == "No active alarms"


def test_check_carries_the_released_version():
    # The publish check fails on main when a version file disagrees with
    # the newest released CHANGES.md heading.
    released = re.search(r"^## (\d+\.\d+\.\d+)", (ROOT / "CHANGES.md").read_text(),
                         flags=re.MULTILINE).group(1)
    assert re.search(rf'^__version__ = "{re.escape(released)}"$', CHECK.read_text(), flags=re.MULTILINE)


def test_release_writes_version_into_check(tmp_path):
    """Apply the version_files entry of .github/repo-infra.json to the check
    module, as Create release PR does (a multiline regex, first match)"""
    config = json.loads((ROOT / ".github/repo-infra.json").read_text())
    (spec,) = [f for f in config["version_files"] if (ROOT / f["path"]) == CHECK]
    stamped = re.sub(spec["pattern"], spec["replacement"].replace("$VERSION", "9.8.7"),
                     CHECK.read_text(), count=1, flags=re.MULTILINE)
    assert re.search(spec["verify"].replace("$VERSION", re.escape("9.8.7")), stamped, flags=re.MULTILINE)
    copy = tmp_path / "stamped_check.py"
    copy.write_text(stamped)
    module_spec = importlib.util.spec_from_file_location("stamped_check", copy)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    assert module.__version__ == "9.8.7"
