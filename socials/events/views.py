from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_datetime
from .models import Event
from .forms import EventForm

@login_required
def calendar_page(request):
    # main calendar UI
    return render(request, "events/calendar.html")

@login_required
def events_feed(request):
    """
    FullCalendar will call this with ?start=ISO&end=ISO.
    Return JSON list of events the user is allowed to see.
    """
    start = request.GET.get("start")
    end = request.GET.get("end")
    if not start or not end:
        return HttpResponseBadRequest("start/end required")

    # visibility rules: show public, friends, and user’s own private events
    qs = Event.objects.filter(start__lte=end, end__gte=start).select_related("created_by")

    user = request.user
    allowed = []
    for ev in qs:
        if ev.visibility == "public":
            allowed.append(ev)
        elif ev.visibility == "private" and ev.created_by_id == user.id:
            allowed.append(ev)
        elif ev.visibility == "friends":
            # TODO: plug in your real “friends” logic.
            # For now, treat friends == public for demo or restrict to creator.
            allowed.append(ev)  # or `if is_friend(user, ev.created_by): allowed.append(ev)`
    data = [{
        "id": ev.id,
        "title": ev.title,
        "start": ev.start.isoformat(),
        "end": ev.end.isoformat(),
        "extendedProps": {
            "description": ev.description,
            "location": ev.location,
            "visibility": ev.visibility,
            "isOwner": ev.created_by_id == user.id,
        }
    } for ev in allowed]
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["POST"])
def create_event(request):
    # Accept JSON from FullCalendar quick-create OR form-encoded from modal
    payload = request.POST or request.body
    data = {}
    if request.content_type == "application/json":
        import json
        data = json.loads(payload)
    else:
        data = request.POST

    # handle ISO strings when coming from calendar drag
    start = data.get("start")
    end = data.get("end")
    if start and end and "T" in start:
        data = data.copy()
        data["start"] = parse_datetime(start)
        data["end"] = parse_datetime(end)

    form = EventForm(data)
    if form.is_valid():
        ev = form.save(commit=False)
        ev.created_by = request.user
        ev.save()
        return JsonResponse({"ok": True, "id": ev.id})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@login_required
@require_http_methods(["PATCH", "POST"])
def update_event(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    if ev.created_by_id != request.user.id:
        return HttpResponseForbidden("not yours")

    import json
    if request.content_type == "application/json":
        data = json.loads(request.body)
    else:
        data = request.POST

    # allow drag-resize updates
    for key in ("start", "end"):
        if key in data and isinstance(data[key], str) and "T" in data[key]:
            data[key] = parse_datetime(data[key])

    form = EventForm(data, instance=ev, partial=True)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@login_required
@require_http_methods(["DELETE", "POST"])
def delete_event(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    if ev.created_by_id != request.user.id:
        return HttpResponseForbidden("not yours")
    ev.delete()
    return JsonResponse({"ok": True})
