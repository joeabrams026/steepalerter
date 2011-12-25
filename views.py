from google.appengine.api import users
from google.appengine.ext.webapp import template
from models import *

from models import Deal
from google.appengine.ext import webapp
from google.appengine.api.prospective_search import *
import string
import os

class EditAlerts(webapp.RequestHandler):
    """Edit or create alerts"""

    def get(self):
        alert = Alert.by_user(users.get_current_user())

        if alert is not None:
            histories = History.by_alert(alert)
        else:
            alert = Alert()
            histories = None

        if histories is None:
            histories = []

        template_values = {
            'keywords': alert.keywords,
            'histories': histories
        }

        path = os.path.join(os.path.dirname(__file__), 'templates/edit_alerts.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        user = users.get_current_user()
        alert = Alert.by_user(user)
        if not alert:
            alert = Alert()
            alert.user = user

        keywords = self.request.get('keywords')
        alert.keywords = keywords

        rgKeywords = map(lambda x: x.lower(), keywords.split())
        query = string.join(rgKeywords, sep=' OR ')
        alert.put()

        subscribe(Deal, query, str(alert.key()))
        self.redirect('/edit_alerts')


class MatchResponseHandler(webapp.RequestHandler):
    """MatchResponseHandler receives match results from TaskQueue."""

    def post(self):
        # document from match request, either a python dict or db.Model
        # if result_return_document = true in Match call
        #doc = prospective_search.get_document(self.request)

        # topic from match request
        topic = self.request.get('topic')
        # Key specified in match call.
        key = self.request.get_all('key')[0]
        deal = db.get(key)

        # Number of total matching subscriptions from match request
        # which generated this result event.
        results_count = self.request.get_all('results_count')
        # Index of 1st subscription in this match result batch.
        # 0 <= result_offset < results_count.
        results_offset = self.request.get_all('results_offset')
        # List of subscription ids that matched for match.
        sub_ids = self.request.get_all('id')
        alerts = db.get(sub_ids)
        for alert in alerts:
            if alert is None:
                continue

            hist = History()
            hist.deal = deal
            hist.alert = alert
            hist.put()
            if not hist.emailed:
                hist.send_email()


class Check(webapp.RequestHandler):
    """ Fetches Rss feed and submits a new Match query"""

    def get(self):
        deal = Deal.parse()
        last_deal = Deal.all().order("-published").get()
        ### last_deal = None ### for testing

        # Only add this deal and call match if it's new!
        if last_deal is None or last_deal.title != deal.title or self.request.GET.has_key('force'):
            deal.put()
            match(deal, result_key=str(deal.key()))
            print ("new deal.  match submitted")
            print (deal.alltext)
        else:
            print ("existing deal")


class ClearAllSubs(webapp.RequestHandler):
    """ Clear all subs b/c I'm getting orphans for some reason """

    def get(self):
        pass