import threading
import uuid
from typing import Dict, List, Optional
import time

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, dict] = {}
        self.lock = threading.Lock()
        self.jobid_to_clientid: Dict[str, str] = {}
        self.jobid_to_filepath: Dict[str, str] = {}

    def add_job(self, filename: str, language: str, model: str, client_id: str = None, file_path: str = None) -> str:
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
                'client_id': client_id,
                'file_path': file_path,
                'completed_at': None
            }
            if client_id:
                self.jobid_to_clientid[job_id] = client_id
            if file_path:
                self.jobid_to_filepath[job_id] = file_path
        return job_id

    def get_jobs(self) -> List[dict]:
        now = time.time()
        expired = []
        with self.lock:
            for job_id, job in list(self.jobs.items()):
                if job.get('completed_at') and now - job['completed_at'] > 259200:
                    expired.append(job_id)
            # 3일 경과된 job 자동 삭제
            for job_id in expired:
                del self.jobs[job_id]
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
                if status in ['완료', 'skipped', '오류', '취소', '중단됨']:
                    self.jobs[job_id]['completed_at'] = time.time()

    def set_progress(self, job_id: str, progress: int):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['progress'] = progress

    def append_log(self, job_id: str, log_line: str):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['log'] += log_line + '\n'

    def get_client_id(self, job_id: str) -> str:
        return self.jobid_to_clientid.get(job_id)

    def get_file_path(self, job_id: str) -> str:
        return self.jobid_to_filepath.get(job_id)

job_manager = JobManager() 