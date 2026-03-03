# cmk-oposs_isam_alarm

Checkmk special agent plugin for ISAM alarm status monitoring.
Migrated from oegig-plugins to Checkmk 2.3.x v2 API.

## Components

- `local/lib/python3/cmk_addons/plugins/oposs_isam_alarm/agent_based/oposs_isam_alarm.py` -- check plugin (parse JSON, discover services, check alarm state)
- `local/lib/python3/cmk_addons/plugins/oposs_isam_alarm/libexec/agent_oposs_isam_alarm` -- special agent script (HTTP GET from collector)
- `local/lib/python3/cmk_addons/plugins/oposs_isam_alarm/server_side_calls/isam_alarm.py` -- server-side call connector (builds URL)
- `local/lib/python3/cmk_addons/plugins/oposs_isam_alarm/rulesets/isam_alarm.py` -- WATO ruleset (collector URL field)
- `.mkp-builder.ini` -- MKP packaging config
- `.github/workflows/release.yml` -- automated release workflow

## Architecture

- Special agent: simple HTTP GET proxy -- fetches raw response from `{collector}/{ip}` and writes to stdout
- Section name: `isam_alarm_status` (kept for backward compatibility with collector service)
- Check plugin uses `sections=["isam_alarm_status"]` to reference the unchanged section name
- Each JSON line from collector has `service`, `status` (0-3), and `info` fields
- Discovery yields one Service per JSON line; check yields the pre-built Result

## Naming Chain

```
rule_spec_special_agent_oposs_isam_alarm  (rulesets)
  -> special_agent_oposs_isam_alarm       (server_side_calls)
    -> libexec/agent_oposs_isam_alarm     (special agent script)
```
