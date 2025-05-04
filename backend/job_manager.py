import threading
import uuid
from typing import Dict, List, Optional

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, dict] = {}
        self.lock = threading.Lock()

    def add_job(self, filename: str, language: str, model: str) -> str:
        job_id = str(uuid.uuid4())
        with self.lock:
            self.jobs[job_id] = {
                'id': job_id,
                'filename': filename,
                'language': language,
                'model': model,
                'progress': 0,
                'status': '대기',
                'log': '',
            }
        return job_id

    def get_jobs(self) -> List[dict]:
        with self.lock:
            return list(self.jobs.values())

    def get_job(self, job_id: str) -> Optional[dict]:
        with self.lock:
            return self.jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(kwargs)

    def delete_job(self, job_id: str):
        with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]

    def set_status(self, job_id: str, status: str):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = status

    def set_progress(self, job_id: str, progress: int):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['progress'] = progress

    def append_log(self, job_id: str, log_line: str):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['log'] += log_line + '\n'

job_manager = JobManager() 