class ContextManager:
    """
    A thread-safe singleton that holds runtime context of the last actions.
    No persistent storage, no history.json integration, no timestamps.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextManager, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.last_application = None
        self.last_website = None
        self.last_url = None
        self.last_file = None
        self.last_folder = None
        self.last_action = None
        self.last_action_payload = None
