import datetime

from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy

from home.views import get_twitter
from .models import Battle
from . import spellCheck


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        form.instance.user = self.request.user
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
            }
            return JsonResponse(data)
        else:
            return response


class BattleList(ListView):
    model = Battle


class BattleCreate(CreateView):
    model = Battle
    fields = ['battle_name', 'hashtag1', 'hashtag2', 'started_at', 'ended_at']
    success_url = reverse_lazy('battle:battle_list')

    def form_valid(self, form):

        context = battle(self.request)

        form.instance.hashtag1_typos = context["query1_typos"]
        form.instance.hashtag2_typos = context["query2_typos"]
        form.instance.winner = context["winner"]
        form.instance.status = context["status"]
        form.instance.user = self.request.user

        return super(BattleCreate, self).form_valid(form)


class BattleDetailView(DetailView):
    model = Battle
    template_name = "battle/battle_detail.html"


class BattleUpdate(UpdateView):
    model = Battle
    fields = ['battle_name', 'hashtag1', 'hashtag2', 'started_at', 'ended_at']
    success_url = reverse_lazy('battle:battle_list')

    def form_valid(self, form):

        context = battle(self.request)

        form.instance.hashtag1_typos = context["query1_typos"]
        form.instance.hashtag2_typos = context["query2_typos"]
        form.instance.winner = context["winner"]
        form.instance.status = context["status"]
        form.instance.user = self.request.user

        return super(BattleUpdate, self).form_valid(form)


class BattleDelete(AjaxableResponseMixin, DeleteView):
    model = Battle
    success_url = reverse_lazy('battle:battle_list')


@login_required
def battle(request):

    hashtag1 = request.POST.get("hashtag1", None)
    hashtag2 = request.POST.get("hashtag2", None)
    started_at = request.POST.get("started_at", None)
    ended_at = request.POST.get("ended_at", None)

    api = get_twitter(request.user)

    statuses1 = []
    statuses2 = []

    status1_ended_at = datetime.datetime.strptime(ended_at, "%Y-%m-%d").date() + datetime.timedelta(days=1)
    status1_ended_at = status1_ended_at.strftime("%Y-%m-%d")

    status2_ended_at = datetime.datetime.strptime(ended_at, "%Y-%m-%d").date() + datetime.timedelta(days=1)
    status2_ended_at = status2_ended_at.strftime("%Y-%m-%d")

    today = datetime.datetime.today()
    today = today.strftime("%Y-%m-%d")

    query1_typos = None
    query2_typos = None
    winner = None
    status = "Inactive"

    # get a query of tweets by hashtags and start date/end date
    while hashtag1 and len(hashtag1) > 1 and hashtag2 and len(hashtag2) > 1 and started_at and ended_at  and started_at < today:
        new_statuses1 = api.GetSearch(term=hashtag1, count=100, until=status1_ended_at, result_type='recent')
        new_statuses2 = api.GetSearch(term=hashtag2, count=100, until=status2_ended_at, result_type='recent')

        # out of statuses: done
        if len(new_statuses1) == 0 or len(new_statuses2) == 0:
            break

        statuses1 = statuses1 + new_statuses1
        statuses2 = statuses2 + new_statuses2

        # get the created_at of the oldest tweet in a response query1
        status1_date_string = new_statuses1[len(new_statuses1) - 1].created_at
        dt1 = status1_date_string.split(" ")
        status1_ended_at = datetime.datetime.strptime(dt1[5] + "-" + dt1[1] + "-" + dt1[2], "%Y-%b-%d").date()
        status1_ended_at = status1_ended_at.strftime("%Y-%m-%d")

        # get the created_at of the oldest tweet in a response query2
        status2_date_string = new_statuses2[len(new_statuses2) - 1].created_at
        dt2 = status2_date_string.split(" ")
        status2_ended_at = datetime.datetime.strptime(dt2[5] + "-" + dt2[1] + "-" + dt2[2], "%Y-%b-%d").date()
        status2_ended_at = status2_ended_at.strftime("%Y-%m-%d")

        # reached started_at: done
        if started_at >= status1_ended_at or started_at >= status2_ended_at:
            break

    # calculate the number of typos if a query of tweets is not empty
    if len(statuses1) > 0 and len(statuses2) > 0:
        query1_typos = spellCheck.preprocess(statuses1)
        query2_typos = spellCheck.preprocess(statuses2)

    # compare the number of typos between two queries of tweets
    if query1_typos or query2_typos:
        if query2_typos < query1_typos:
            winner = hashtag2
        else:
            winner = hashtag1

    # estimate the status of battle
    if len(statuses1) != 0 and len(statuses2) != 0:
        status = "Active"

    context = {
        'request': request,
        'statuses1': statuses1,
        'query1_typos': query1_typos,
        'statuses2': statuses2,
        'query2_typos': query2_typos,
        'winner': winner,
        'status': status
    }

    return context
