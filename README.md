# ISAM Alarm Status Checkmk Plugin

Checkmk special agent plugin for monitoring ISAM alarm status via a collector web service.

## Features

- Fetches alarm data from a configurable collector URL
- Discovers individual alarm services automatically
- Reports per-service alarm state (OK/WARN/CRIT/UNKNOWN)

## Components

| File | Purpose |
|------|---------|
| `agent_based/oposs_isam_alarm.py` | Check plugin (parse, discover, check) |
| `libexec/agent_oposs_isam_alarm` | Special agent script (HTTP GET) |
| `server_side_calls/isam_alarm.py` | Server-side call connector |
| `rulesets/isam_alarm.py` | WATO ruleset (collector URL config) |

## Installation

### MKP Package (recommended)

Download the latest `.mkp` file from the
[Releases](https://github.com/oposs/cmk-oposs_isam_alarm/releases) page and
install it:

```bash
mkp install oposs_isam_alarm-<version>.mkp
```

### Manual Installation

Copy the plugin files into your Checkmk site:

```
local/lib/python3/cmk_addons/plugins/oposs_isam_alarm/
├── agent_based/
│   └── oposs_isam_alarm.py
├── libexec/
│   └── agent_oposs_isam_alarm
├── server_side_calls/
│   └── isam_alarm.py
└── rulesets/
    └── isam_alarm.py
```

## Configuration

1. In WATO, navigate to **Setup > Agents > Other integrations > OPOSS ISAM Alarm Collector**
2. Set the **Collector URL** (e.g., `https://collector.example.com:8443/isam`)
3. The agent builds the final URL as `{collector_url}/{host_ip}`

## License

MIT - OETIKER+PARTNER AG
