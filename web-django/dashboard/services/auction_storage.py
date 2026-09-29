"""Private, temporary upload snapshots bound to one user and Django session.

Only an opaque token and small display preferences are stored in the session.
Uploads follow the login session; stale files are removed on the user's next login.
"""
import base64
import json
import os
import re
import secrets
import tempfile
from importlib import import_module
from pathlib import Path

from django.conf import settings
from django.utils.crypto import salted_hmac

from .auction import AuctionError


class UploadExpired(AuctionError):
    pass


def _directory():
    directory = Path(settings.AUCTION_UPLOAD_DIR)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory


def _owner(user_id, session_key):
    return salted_hmac('auction-owner', f'{user_id}:{session_key}', algorithm='sha256').hexdigest()


def _path(token):
    if not re.fullmatch(r'[0-9a-f]{64}', token or ''):
        raise UploadExpired('Your auction upload is no longer available. Upload it again.')
    return _directory() / f'{token}.json'


def _write(token, snapshot):
    directory = _directory()
    descriptor, temporary = tempfile.mkstemp(dir=directory, suffix='.tmp')
    try:
        with os.fdopen(descriptor, 'w') as file:
            json.dump(snapshot, file, allow_nan=False)
        os.replace(temporary, _path(token))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def create(user_id, session_key, name, content, sheets):
    token = secrets.token_hex(32)
    snapshot = {'owner': _owner(user_id, session_key), 'account': _owner(user_id, 'account'),
                'session_key': session_key,
                'name': name, 'content': base64.b64encode(content).decode('ascii'),
                'sheets': sheets, 'sheet': None, 'table': None}
    _write(token, snapshot)
    return token, snapshot


def load(token, user_id, session_key):
    path = _path(token)
    try:
        snapshot = json.loads(path.read_text())
    except (FileNotFoundError, ValueError) as error:
        raise UploadExpired('Your auction upload expired. Upload it again.') from error
    if snapshot['owner'] != _owner(user_id, session_key):
        raise UploadExpired('This upload is not available in your session. Upload your own file.')
    return snapshot


def save(token, snapshot):
    _write(token, snapshot)


def remove(token, user_id, session_key):
    try:
        load(token, user_id, session_key)
    except UploadExpired:
        return
    _path(token).unlink(missing_ok=True)


def cleanup_after_login(user_id):
    """Remove this user's files from inactive sessions after authentication.

    Another browser may still have a valid session, so preserve those uploads.
    Django's session backend decides whether a session has expired or logged out.
    """
    session_store = import_module(settings.SESSION_ENGINE).SessionStore
    account = _owner(user_id, 'account')
    removed = 0
    for path in _directory().glob('*.json'):
        try:
            snapshot = json.loads(path.read_text())
            if snapshot.get('account') != account:
                continue
            session = session_store(session_key=snapshot['session_key']).load()
            if str(session.get('_auth_user_id', '')) != str(user_id):
                path.unlink(missing_ok=True)
                removed += 1
        except FileNotFoundError:
            pass
    return removed
