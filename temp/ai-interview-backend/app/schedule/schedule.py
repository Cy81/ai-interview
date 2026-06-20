import logging
import asyncio
import os
import tempfile
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

logger = logging.getLogger(__name__)

scheduler = None


def async_task_wrapper(async_func):
    """包装异步函数，使其可以在调度器中运行"""
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_func(*args, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error running async task: {e}", exc_info=True)
            raise
    return wrapper


def setup_scheduler(app: FastAPI = None):
    """初始化定时任务调度器"""
    global scheduler

    if not app:
        logger.error("FastAPI app instance is required for scheduler setup")
        return

    lock_file_path = os.path.join(tempfile.gettempdir(), "framework_scheduler.lock")
    logger.info(f"Lock file path: {lock_file_path}")

    try:
        if os.path.exists(lock_file_path):
            try:
                with open(lock_file_path, "r") as f:
                    pid = f.read().strip()
                try:
                    os.kill(int(pid), 0)
                    logger.info(f"Scheduler lock exists. Process {pid} is running the scheduler.")
                    scheduler_enabled = False
                except ProcessLookupError:
                    logger.warning(f"Process {pid} in lock file is not running. Removing stale lock file.")
                    os.remove(lock_file_path)
                    with open(lock_file_path, "w") as f:
                        f.write(str(os.getpid()))
                    scheduler_enabled = True
            except Exception as e:
                logger.warning(f"Could not read scheduler lock file: {e}. Creating new lock.")
                os.remove(lock_file_path)
                with open(lock_file_path, "w") as f:
                    f.write(str(os.getpid()))
                scheduler_enabled = True
        else:
            with open(lock_file_path, "w") as f:
                f.write(str(os.getpid()))
            scheduler_enabled = True
    except Exception as e:
        logger.error(f"Error handling scheduler lock: {e}")
        scheduler_enabled = False

    if not scheduler_enabled:
        logger.info("Scheduler disabled for this worker process")
        return

    try:
        scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='UTC'
        )

        # 在此添加定时任务
        # scheduler.add_job(
        #     async_task_wrapper(your_task),
        #     'interval', seconds=60, id='your_task', replace_existing=True
        # )

        scheduler.start()
        logger.info("定时任务已注册并成功启动")
    except Exception as e:
        logger.error(f"Failed to setup scheduler: {e}", exc_info=True)


def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    logger.info("Shutting down scheduler")
    try:
        if scheduler:
            scheduler.shutdown()
            logger.info("定时任务调度器已成功关闭")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")
