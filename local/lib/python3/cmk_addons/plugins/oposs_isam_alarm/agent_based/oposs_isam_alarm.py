#!/usr/bin/env python3
# Copyright (C) 2025 OETIKER+PARTNER AG - License: GNU General Public License v2

"""
Check plugin for ISAM alarm status monitoring.
Parses JSON alarm data from collector, discovers per-service alarms,
and reports their state.
"""

import json

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
)

STATE_MAP = {
    0: State.OK,
    1: State.WARN,
    2: State.CRIT,
    3: State.UNKNOWN,
}


def parse_info(string_table):
    """Parse JSON lines into a dict mapping service name -> Result."""
    parsed = {}
    for line in string_table:
        j = json.loads(line[0])
        s = j["service"]
        parsed[s] = Result(
            state=STATE_MAP[j["status"]],
            notice=j["info"],
        )
    return parsed


def discover_alarms(section) -> DiscoveryResult:
    for name in section:
        yield Service(item=name)


def check_alarms(item, section) -> CheckResult:
    if item in section:
        yield section[item]


# Section name stays "isam_alarm_status" for collector compatibility
agent_section_isam_alarm_status = AgentSection(
    name="isam_alarm_status",
    parse_function=parse_info,
)

check_plugin_oposs_isam_alarm = CheckPlugin(
    name="oposs_isam_alarm",
    sections=["isam_alarm_status"],
    service_name="ISAM Alarm State - %s",
    discovery_function=discover_alarms,
    check_function=check_alarms,
)
