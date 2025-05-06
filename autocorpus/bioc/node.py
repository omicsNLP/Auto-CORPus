class BioCNode:
    def __init__(self, refid: str, role: str | None = None):
        self.refid = refid
        self.role = role or ""
