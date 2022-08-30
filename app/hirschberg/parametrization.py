import json
from pathlib import Path

from viktor.parametrization import NumberField
from viktor.parametrization import Parametrization
from viktor.parametrization import Text

with open(Path(__file__).parent / "lib" / "descriptions.json") as f:
    DESC = json.load(f)


class AppParametrization(Parametrization):
    title = Text(DESC["title"])
    election = Text(DESC["election"])
    subtitle = Text(DESC["subtitle"])
    explanation = Text(DESC["explanation"])
    number_of_nodes = NumberField("Number of nodes", default=3, min=3, max=99, step=2)
