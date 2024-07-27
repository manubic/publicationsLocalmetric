from models.publicationsCreater import PublicationsCreater
from models.publicationsScheduler import PublicationsScheduler



class AppManager:
    def __init__(self) -> None:
        self.PublicationsCreater = PublicationsCreater
        self.PublicationsScheduler = PublicationsScheduler