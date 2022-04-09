from typing import Dict


# TODO: Use shared_types paradigm.  Sooner would be great!
Html = str
Policy = str
Url = str
# TODO: What is this?  Ms since epoch?
Time = int
Row = Dict[str, str]


class BcException(Exception):
    pass
