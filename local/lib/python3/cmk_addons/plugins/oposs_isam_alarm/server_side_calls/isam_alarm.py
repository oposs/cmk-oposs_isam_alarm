# Copyright (C) 2025 OETIKER+PARTNER AG - License: GNU General Public License v2

"""
Server-side calls configuration for ISAM alarm special agent.
Converts GUI ruleset parameters into command-line arguments.
"""

from collections.abc import Iterator

from cmk.server_side_calls.v1 import (
    HostConfig,
    SpecialAgentCommand,
    SpecialAgentConfig,
)
from pydantic import BaseModel


class Params(BaseModel):
    collector: str
    verify_tls: bool = True


def commands_function(
    params: Params,
    host_config: HostConfig,
) -> Iterator[SpecialAgentCommand]:
    ip = host_config.primary_ip_config.address
    # Without the option the command line stays as it always was
    flags = [] if params.verify_tls else ["--no-verify-tls"]
    yield SpecialAgentCommand(command_arguments=[
        *flags,
        f"{params.collector}/{ip}",
    ])


# CRITICAL: Must be named special_agent_<name>
# Name must match: libexec/agent_<name>
special_agent_oposs_isam_alarm = SpecialAgentConfig(
    name="oposs_isam_alarm",
    parameter_parser=Params.model_validate,
    commands_function=commands_function,
)
