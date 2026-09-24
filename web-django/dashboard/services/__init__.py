"""Where the work happens: calculations, queries, and outside data sources.

Nothing here knows about HTTP. Each function takes plain arguments and returns
plain Python values, so it can be tested and reused independently of the views.

- ``connections``   : reads and writes the signed-in user's saved MySQL settings
- ``database``      : opens and checks connections to the client's MySQL server
- ``profitability`` : profit-per-class calculation over ``items_clean``
- ``market``        : index price history and growth from Yahoo Finance
"""
