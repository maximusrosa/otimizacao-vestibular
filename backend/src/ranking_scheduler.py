"""Processo dedicado que agenda a sincronizacao diaria dos rankings."""

import os
import time
from zoneinfo import ZoneInfo

from .sync_rankings import configured_years, sync_rankings


def is_enabled() -> bool:
    return os.environ.get("RANKING_SYNC_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def schedule_time() -> tuple[int, int]:
    value = os.environ.get("RANKING_SYNC_TIME", "05:00")
    try:
        hour, minute = (int(part) for part in value.split(":"))
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError
        return hour, minute
    except ValueError as error:
        raise RuntimeError("RANKING_SYNC_TIME deve usar o formato HH:MM.") from error


def run_scheduled_sync():
    sync_rankings(configured_years(), resume=True)


def main():
    if not is_enabled():
        print("Sincronização diária desabilitada por RANKING_SYNC_ENABLED=false.")
        while True:
            time.sleep(3600)

    hour, minute = schedule_time()
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    timezone = ZoneInfo(os.environ.get("TZ", "America/Sao_Paulo"))
    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(
        run_scheduled_sync,
        CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="daily-ranking-sync",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    print(f"Sincronização diária ativa às {hour:02d}:{minute:02d} ({timezone}).")
    scheduler.start()


if __name__ == "__main__":
    main()
