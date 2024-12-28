from managers.models.publications_creater import PublicationsCreater
from managers.models.publications_scheduler import PublicationsScheduler


class AppManager:
    def __init__(self) -> None:
        self.publications_creater = PublicationsCreater
        self.publications_scheduler = PublicationsScheduler
