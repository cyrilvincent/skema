class ServiceError(Exception):

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        print(f"ServiceError: {message}")


class ServiceWarning(Exception):

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        print(f"ServiceWarning: {message}")


class ServiceEmptyWarning(ServiceWarning):

    def __init__(self, message: str):
        super().__init__(message)

