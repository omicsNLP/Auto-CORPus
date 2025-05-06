from .node import BioCNode


class BioCRelation:
    def __init__(
        self,
        id: str | None = None,
        infons: dict[str, str] | None = None,
        nodes: list[BioCNode] | None = None,
    ):
        self.id = id or ""
        self.infons = infons or {}
        self.nodes = nodes or []
