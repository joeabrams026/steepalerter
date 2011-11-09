from google.appengine.ext import db
from datetime import datetime
from xml.dom import minidom
from google.appengine.api import mail
import urllib

class Alert(db.Model):
    keywords = db.StringListProperty ()
    user =  db.UserProperty ()

    @staticmethod
    def by_user(user):
        return Alert.all().filter('user = ', user).get()

    @staticmethod
    def by_sub_id(sub_id):
        return Alert.all().filter('user.pk = ', sub_id).get()

class Deal(db.Model):
    title = db.StringProperty()
    description = db.TextProperty()
    published = db.DateTimeProperty()

    @staticmethod
    def parse():
        URL = "http://rss.steepandcheap.com/docs/steepcheap/rss.xml"

        dom = minidom.parse(urllib.urlopen(URL))
        deal = Deal()
        node = dom.getElementsByTagName("item")[0]
        deal.title = node.getElementsByTagName("title")[0].firstChild.data + " toots"
        deal.description = node.getElementsByTagName("description")[0].firstChild.data
        deal.link = node.getElementsByTagName("link")[0].firstChild.data

        published = node.getElementsByTagName("pubDate")[0].firstChild.data
        deal.published = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S MDT")
        deal.priceCurrent = node.getElementsByTagName("sac:priceCurrent")[0].firstChild.data
        deal.priceRegular = node.getElementsByTagName("sac:priceRegular")[0].firstChild.data
        deal.price = node.getElementsByTagName("sac:price")[0].firstChild.data
        deal.tinyImage = node.getElementsByTagName("sac:tinyImage")[0].firstChild.data
        deal.image = node.getElementsByTagName("sac:image")[0].firstChild.data
        deal.thumbnail = node.getElementsByTagName("sac:thumbnail")[0].firstChild.data
        deal.detailimage = node.getElementsByTagName("sac:detailimage")[0].firstChild.data
        deal.availability = node.getElementsByTagName("sac:availability")[0].firstChild.data
        return deal


class History(db.Model):
    alert =  db.ReferenceProperty (Alert)
    deal = db.ReferenceProperty (Deal)
    emailed = db.BooleanProperty (default = False)

    @staticmethod
    def by_alert(alert):
        return History.all().filter('alert = ', alert)

    from google.appengine.api import mail

    def send_email (self):
        mail.send_mail(sender="Steep Alerts <todo@gmail.com>",
                      to=self.alert.user.email(),
                      subject="Steep Alert: " + self.deal.title,
                      body=self.deal.description)
        self.emailed = True
        self.put()