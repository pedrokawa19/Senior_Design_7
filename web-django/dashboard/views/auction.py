"""Authenticated Auction workflow. Forms validate input; services process tables."""
import base64
import copy
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from ..auction_forms import AuctionFilterForm, AuctionUploadForm
from ..services import auction as service, auction_storage as storage

logger = logging.getLogger(__name__)
SESSION_STATE = 'auction_state'


def initial_state(token):
    return {'token': token, 'filters': dict(service.DEFAULT_FILTERS), 'show_excluded': False,
            'pages': {'eligible': 1, 'excluded': 1},
            'sorts': {kind: {'column': None, 'direction': ''} for kind in ('eligible', 'excluded')}}


def clear_upload(request):
    state = request.session.pop(SESSION_STATE, None)
    if state:
        storage.remove(state['token'], request.user.pk, request.session.session_key)


def _snapshot(request, state):
    return storage.load(state['token'], request.user.pk, request.session.session_key)


def _select_sheet(snapshot, token, sheet):
    # Clear old results before parsing a replacement worksheet.
    snapshot['sheet'] = None
    snapshot['table'] = None
    storage.save(token, snapshot)
    table = service.read_table(snapshot['name'], base64.b64decode(snapshot['content']), sheet)
    snapshot.update(sheet=sheet, table=table)
    storage.save(token, snapshot)


def _form_error(form):
    return ' '.join(str(error) for errors in form.errors.values() for error in errors)


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def page(request):
    error = None
    state = copy.deepcopy(request.session.get(SESSION_STATE))
    snapshot = None
    try:
        if request.method == 'POST' and request.POST.get('action') == 'upload':
            clear_upload(request)
            state = None
            form = AuctionUploadForm(request.POST, request.FILES)
            if not form.is_valid():
                raise service.AuctionError(_form_error(form))
            uploaded = form.cleaned_data['file']
            content = uploaded.read(service.MAX_FILE_BYTES + 1)
            sheets = service.inspect_upload(uploaded.name, content)
            if not request.session.session_key:
                request.session.create()
            token, snapshot = storage.create(request.user.pk, request.session.session_key, uploaded.name, content, sheets)
            state = initial_state(token)
            request.session[SESSION_STATE] = state
            if len(sheets) <= 1:
                _select_sheet(snapshot, token, sheets[0] if sheets else None)
            return redirect('auction')
        if state:
            snapshot = _snapshot(request, state)
        if request.method == 'POST':
            if not state or request.POST.get('token') != state['token']:
                raise service.AuctionError('This upload has changed or expired. Reload the page and try again.')
            action = request.POST.get('action')
            if action == 'sheet':
                state = initial_state(state['token'])
                request.session[SESSION_STATE] = state
                _select_sheet(snapshot, state['token'], request.POST.get('sheet'))
            else:
                if snapshot['table'] is None:
                    raise service.AuctionError('Select a valid worksheet first.')
                if action == 'filter':
                    form = AuctionFilterForm(request.POST)
                    if not form.is_valid():
                        raise service.AuctionError(_form_error(form))
                    state['filters'] = {key: str(value) for key, value in form.cleaned_data.items()}
                    state['pages'] = {'eligible': 1, 'excluded': 1}
                elif action in ('show', 'hide'):
                    state['show_excluded'] = action == 'show'
                elif action in ('paginate', 'sort'):
                    kind = request.POST.get('table')
                    if kind not in ('eligible', 'excluded'):
                        raise service.AuctionError('Choose a valid results table.')
                    if action == 'paginate':
                        try:
                            page_number = int(request.POST.get('page') or request.POST.get('page_number', ''))
                        except ValueError as exception:
                            raise service.AuctionError('Enter a valid page number.') from exception
                        groups = service.partition(snapshot['table'], state['filters'])
                        pages = max(1, (len(groups[kind]) + service.PAGE_SIZE - 1) // service.PAGE_SIZE)
                        if not 1 <= page_number <= pages:
                            raise service.AuctionError(f'Enter a page number between 1 and {pages}.')
                        state['pages'][kind] = page_number
                    else:
                        try:
                            column = int(request.POST.get('column', ''))
                        except ValueError as exception:
                            raise service.AuctionError('Choose a valid column.') from exception
                        if not 0 <= column < len(snapshot['table']['columns']):
                            raise service.AuctionError('Choose a valid column.')
                        order = state['sorts'][kind]
                        if order['column'] != column:
                            order.update(column=column, direction='asc')
                        elif order['direction'] == 'asc':
                            order['direction'] = 'desc'
                        else:
                            order.update(column=None, direction='')
                        state['pages'][kind] = 1
                else:
                    raise service.AuctionError('Choose a valid Auction action.')
            request.session[SESSION_STATE] = state
            return redirect('auction')
    except storage.UploadExpired as exception:
        request.session.pop(SESSION_STATE, None)
        state = snapshot = None
        error = str(exception)
    except service.AuctionError as exception:
        error = str(exception)
    except OSError:
        logger.warning('Temporary Auction storage unavailable for user id %s', request.user.pk)
        error = 'Temporary upload storage is unavailable. Please try again.'

    context = {'active_tab': 'auction', 'upload_form': AuctionUploadForm(), 'error': error,
               'snapshot': snapshot, 'state': state}
    if snapshot and snapshot['table'] is not None:
        table = snapshot['table']
        groups = service.partition(table, state['filters'])
        context['eligible'] = service.page_table(table['columns'], groups['eligible'], state, 'eligible')
        context['excluded'] = service.page_table(table['columns'], groups['excluded'], state, 'excluded')
        context['eligible_filter'] = AuctionFilterForm(initial=state['filters'], auto_id='eligible_%s')
        context['excluded_filter'] = AuctionFilterForm(initial=state['filters'], auto_id='excluded_%s')
    return render(request, 'auction.html', context, status=400 if error else 200)


@login_required
@never_cache
@require_GET
def download(request):
    state = request.session.get(SESSION_STATE)
    try:
        if not state:
            raise service.AuctionError('Upload an auction list first.')
        snapshot = _snapshot(request, state)
        if snapshot['table'] is None:
            raise service.AuctionError('Select a worksheet before downloading.')
        groups = service.partition(snapshot['table'], state['filters'])
        content = service.export_workbook(snapshot['table'], groups, state['sorts'])
    except service.AuctionError as exception:
        return HttpResponse(str(exception), status=400, content_type='text/plain')
    response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="auction-results.xlsx"'
    return response
