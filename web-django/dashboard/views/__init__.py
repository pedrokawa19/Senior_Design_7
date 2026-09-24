"""Request handling.

Each module here turns an HTTP request into a response: check permissions,
validate input, call a service, and render. Calculations and external data
access belong in ``dashboard.services``.

- ``auth``  : sign up, log in, log out
- ``pages`` : HTML pages rendered from templates
- ``api``   : JSON endpoints called by the dashboard's JavaScript
"""
