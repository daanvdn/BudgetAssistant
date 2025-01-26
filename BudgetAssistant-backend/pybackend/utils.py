from collections import defaultdict
from typing import TypeVar, Generic, List, Dict

K = TypeVar('K')
V = TypeVar('V')

class ListMultiMap(Generic[K, V]):
    def __init__(self):
        self._map: Dict[K, List[V]] = defaultdict(list)

    def put(self, key: K, value: V) -> None:
        self._map[key].append(value)

    def get(self, key: K) -> List[V]:
        return self._map[key]

    def remove(self, key: K, value: V) -> bool:
        if key in self._map and value in self._map[key]:
            self._map[key].remove(value)
            if not self._map[key]:
                del self._map[key]
            return True
        return False

    def keys(self) -> List[K]:
        return list(self._map.keys())

    def values(self) -> List[List[V]]:
        return list(self._map.values())

    def items(self) -> List[tuple]:
        return list(self._map.items())

    def __str__(self) -> str:
        return str(dict(self._map))