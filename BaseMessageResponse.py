from fuzzywuzzy import fuzz

class BaseMessageResponse:
    def __init__(self):
        pass

    def invoke(self, msg) -> bool:
        raise NotImplementedError

    def execute(self, msg) -> bool:
        raise NotImplementedError


class Zoe(BaseMessageResponse):
    def invoke(self, msg) -> bool:
        raise NotImplementedError

    def execute(self, msg) -> bool:
        raise NotImplementedError


class Ezreal(BaseMessageResponse):
    def invoke(self, msg) -> bool:
        raise NotImplementedError

    def execute(self, msg) -> bool:
        raise NotImplementedError


class Lux(BaseMessageResponse):
    def invoke(self, msg) -> bool:
        raise NotImplementedError

    def execute(self, msg) -> bool:
        raise NotImplementedError


class Mooncake(BaseMessageResponse):
    def invoke(self, msg) -> bool:
        raise NotImplementedError

    def execute(self, msg) -> bool:
        raise NotImplementedError


class Xinqui(BaseMessageResponse):
    def invoke(self, msg) -> bool:
        return

    def execute(self, msg) -> bool:
        raise NotImplementedError


RESPONSES = [Zoe(), Ezreal, Lux, Mooncake, Xinqui]
