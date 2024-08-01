class Filter:

    def __init__(self, sub_id: str=None):
        self._subscription_id = sub_id

    @property
    def subscription_id(self) -> str:
        return self._subscription_id

    @subscription_id.setter
    def subscription_id(self, val: str):
        self._subscription_id = val
