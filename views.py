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

        if alert is None:
            alert = Alert()

        histories = History.by_alert(alert)
        if histories is None:
            histories = []

        template_values = {
            'keywords': string.join(alert.keywords),
            'histories' : histories
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
        alert.keywords = keywords.strip().split()
        alert.put()
        subscribe(Deal, keywords, str(alert.key()))
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
        for sub_id in sub_ids:
            hist = History()
            hist.deal = deal
            hist.alert = db.get(sub_id)
            hist.put()
            hist.send_email()


class Check(webapp.RequestHandler):
    """ Fetches Rss feed and submits a new Match query"""
    def get(self):
        deal = Deal.parse()
        last_deal = Deal.all().order("-published").get()

        # Only add this deal and call match if it's new!
        if last_deal == None or last_deal.title == deal.title:
            deal.put()
            match(deal, result_key=str(deal.key()))
            print ("new deal.  match submitted")
        else:
            print ("existing deal")