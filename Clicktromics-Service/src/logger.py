import logging

class Logger:
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls._initialize_logger()
        return cls._logger
    
    @classmethod
    def _initialize_logger(cls):
        """Initialize the logger with a standard configuration."""
        cls._logger = logging.getLogger(__name__)
        cls._logger.setLevel(logging.DEBUG) 

        file_handler = logging.FileHandler('app.log','w')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        cls._logger.addHandler(file_handler)
