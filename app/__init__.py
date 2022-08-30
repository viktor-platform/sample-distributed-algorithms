from viktor import InitialEntity

from .distributed_algorithms.controller import Controller as MyFolder
from .hirschberg.controller import Controller as MyEntityType

initial_entities = [InitialEntity("MyFolder", name="Distributed Algorithms")]
