#!/usr/bin/env python3
# Copyright (C) 2025 OETIKER+PARTNER AG - License: GNU General Public License v2

"""
Ruleset configuration for ISAM alarm special agent.
Provides GUI configuration form for the collector URL.
"""

from cmk.rulesets.v1 import Title, Help
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    String,
    validators,
)
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


def _formspec():
    return Dictionary(
        title=Title("OPOSS ISAM Alarm Collector"),
        help_text=Help("Configure the ISAM alarm collector URL. "
                       "The agent will fetch alarm data from {collector_url}/{host_ip}."),
        elements={
            "collector": DictElement(
                parameter_form=String(
                    title=Title("Collector URL"),
                    help_text=Help("Base URL of the ISAM alarm collector service "
                                   "(e.g. https://collector.example.com:8443/isam)"),
                    custom_validate=[validators.LengthInRange(min_value=1)],
                ),
                required=True,
            ),
        },
    )


# CRITICAL: Variable name must be: rule_spec_special_agent_{name}
# Name must match special_agent_{name} in server_side_calls
rule_spec_special_agent_oposs_isam_alarm = SpecialAgent(
    name="oposs_isam_alarm",
    title=Title("OPOSS ISAM Alarm Collector"),
    topic=Topic.GENERAL,
    parameter_form=_formspec,
)
