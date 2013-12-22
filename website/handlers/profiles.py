
import os
from datetime import datetime
import re
import urllib
import webapp2 as webapp

from google.appengine.api import users
from google.appengine.api import memcache

import handlers
import ctrl.profile
import model.profile


class BasePage(handlers.BaseHandler):
  def render(self, tmplName, args):
    if not args:
      args = {}

    super(BasePage, self).render(tmplName, args)


class ProfilePage(BasePage):
  def get(self):
    if not self._isLoggedIn():
      return

    data = {}
    data['empires'] = ctrl.profile.getEmpiresForUser(self.user.email())

    self.render("profile/profile_edit.html", data)

  def post(self):
    if not self._isLoggedIn():
      return

    realm_name = None
    empire = None
    display_name = None
    linked_empire = self.request.POST.get("linked_empire")
    if linked_empire:
      empires = ctrl.profile.getEmpiresForUser(self.user.email())
      realm_name, empire_id = linked_empire.split(':')
      empire_id = int(empire_id)

      empire = None
      for empire_realm_name, this_empire in empires.items():
        if empire_realm_name == realm_name and int(this_empire["key"]) == empire_id:
          empire = this_empire
          display_name = empire["display_name"]
      if not empire:
        # actually an error
        realm_name = None
    else:
      display_name = self.request.POST.get("display_name")
    ctrl.profile.saveProfile(self.user.user_id(), realm_name, display_name, empire)

    self.redirect("/profile")


class EmpireAutocompletePage(BasePage):
  """This page is used by the "autocomplete" feature for selecting an empire."""
  def get(self):
    query = self.request.get("q")
    empires = ctrl.profile.getEmpiresByName(query.lower().strip())

    self.render("profile/empire_autocomplete.txt", {"empires": empires})


class EmpireAssociatePage(BasePage):
  """This page is used to add an associate between an empire in the game and a profile."""
  def get(self, cookie):
    """If we have a cookie, we'll look up the association request and, well, honour it!"""
    
  def post(self):
    empire_id = self.request.POST.get("empire_id")
    realm_name, empire_id = empire_id.split(":")
    empire_id = int(empire_id)

    self.response.content_type = "text/plain"
    err = ctrl.profile.initiateEmpireAssociateRequest(self.user, self.profile, realm_name, empire_id)
    if err:
      self.response.write("ERR:"+err)
    else:
      self.response.write("SUCCESS")


app = webapp.WSGIApplication([("/profile/?", ProfilePage),
                              ("/profile/empire-autocomplete", EmpireAutocompletePage),
                              ("/profile/empire-associate/?(.*)", EmpireAssociatePage)],
                             debug=os.environ["SERVER_SOFTWARE"].startswith("Development"))
