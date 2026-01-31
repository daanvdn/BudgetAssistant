import logging
from logging import Logger


class LoggerFactory:
    _handler_configured = False
    _console_handler: logging.Handler | None = None

    @classmethod
    def _get_console_handler(cls) -> logging.Handler:
        if cls._console_handler is None:
            cls._console_handler = logging.StreamHandler()
            cls._console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            cls._console_handler.setFormatter(formatter)
        return cls._console_handler

    @classmethod
    def _configure_logger(cls, logger: logging.Logger) -> logging.Logger:
        logger.setLevel(logging.INFO)
        handler = cls._get_console_handler()
        if handler not in logger.handlers:
            logger.addHandler(handler)
        logger.propagate = False  # Prevent duplicate logs from parent loggers
        return logger

    @classmethod
    def for_class(cls, clazz: type) -> "Logger":
        logger_name = f"{clazz.__module__}.{clazz.__name__}"
        logger = logging.getLogger(logger_name)
        return cls._configure_logger(logger)

    @classmethod
    def for_caller(cls):
        import inspect

        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            if caller_frame is not None:
                module = inspect.getmodule(caller_frame)
                if module is not None:
                    logger_name = module.__name__
                else:
                    logger_name = "__main__"
            else:
                logger_name = "__main__"
        else:
            logger_name = "__main__"

        logger = logging.getLogger(logger_name)
        return cls._configure_logger(logger)


class Bla:
    def __init__(self):
        self.logger = LoggerFactory.for_class(self.__class__)
        self.logger.info("Bla instance created")


if __name__ == "__main__":
    logger = LoggerFactory.for_caller()
    logger.info("This is a test log message.")
    bla = Bla()
