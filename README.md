# retryctl

A configurable retry wrapper for CLI commands with exponential backoff and alerting hooks.

---

## Installation

```bash
pip install retryctl
```

Or install from source:

```bash
git clone https://github.com/yourname/retryctl.git && cd retryctl && pip install .
```

---

## Usage

Wrap any CLI command with automatic retries and exponential backoff:

```bash
retryctl --retries 5 --backoff 2 --timeout 30 -- curl https://example.com/api
```

**Common options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--retries` | `3` | Maximum number of retry attempts |
| `--backoff` | `1.5` | Exponential backoff multiplier |
| `--timeout` | `60` | Per-attempt timeout in seconds |
| `--on-failure` | `None` | Shell command to run as an alert hook on final failure |

**Example with an alerting hook:**

```bash
retryctl --retries 3 --backoff 2 \
  --on-failure "curl -X POST https://hooks.slack.com/... -d '{\"text\":\"Command failed\"}'" \
  -- ./deploy.sh production
```

**Use in a script:**

```bash
retryctl --retries 4 --backoff 1.5 -- python sync_data.py
```

---

## Configuration

You can place default settings in a `.retryctl.toml` file in your project root:

```toml
[defaults]
retries = 3
backoff = 2.0
timeout = 60
```

---

## License

This project is licensed under the [MIT License](LICENSE).