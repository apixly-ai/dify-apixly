import math
import time

from apixly_media.client import MediaError
from tools import base


class QueryTaskTool(base.MediaTool):
    def execute(self, client, parameters):
        try:
            wait = float(parameters.get("wait_seconds") or 0)
        except (TypeError, ValueError) as exc:
            raise MediaError("Wait seconds must be a number from 0 to 15.") from exc
        if not math.isfinite(wait) or not 0 <= wait <= 15:
            raise MediaError("Wait seconds must be from 0 to 15.")
        if wait:
            time.sleep(wait)
        return client.query_task(parameters.get("kind"), parameters.get("task_id"))
