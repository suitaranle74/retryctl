"""Command-line entry point for retryctl."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, REMAINDER

from retryctl.alerts import AlertConfig, AlertManager
from retryctl.backoff import BackoffConfig, ExponentialBackoff
from retryctl.runner import Runner, RunnerConfig


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="retryctl",
        description="Retry a CLI command with exponential backoff and alerting.",
    )
    parser.add_argument("command", nargs=REMAINDER, help="Command to execute")
    parser.add_argument("-n", "--attempts", type=int, default=3, help="Max attempts")
    parser.add_argument("--base-delay", type=float, default=1.0, help="Initial delay (s)")
    parser.add_argument("--max-delay", type=float, default=60.0, help="Max delay (s)")
    parser.add_argument("--multiplier", type=float, default=2.0, help="Backoff multiplier")
    parser.add_argument("--jitter", action="store_true", help="Add random jitter to delay")
    parser.add_argument(
        "--on-failure-cmd",
        default=None,
        help="Shell command to run on final failure ({cmd}, {attempts}, {exit_code})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.error("No command specified.")

    backoff_cfg = BackoffConfig(
        base_delay=args.base_delay,
        max_delay=args.max_delay,
        multiplier=args.multiplier,
        jitter=args.jitter,
    )
    runner_cfg = RunnerConfig(max_attempts=args.attempts)
    alert_cfg = AlertConfig(on_failure_cmd=args.on_failure_cmd)

    backoff = ExponentialBackoff(backoff_cfg)
    alert_mgr = AlertManager(alert_cfg)
    runner = Runner(runner_cfg, backoff, alert_mgr)

    result = runner.run(args.command)
    return result.last.exit_code if result.last else 1


if __name__ == "__main__":
    sys.exit(main())
