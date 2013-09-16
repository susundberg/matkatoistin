
from google.appengine.ext import db


#####################################################################
#
#####################################################################
class TableUserInfo(db.Model):
   username               = db.StringProperty()
   heiaheia_api_oa_token  = db.StringProperty()
   heiaheia_api_oa_secret = db.StringProperty()
   last_sport             = db.StringProperty()

class TableTempUserInfo(db.Model):
   username               = db.StringProperty()
   heiaheia_api_oa_token  = db.StringProperty()
   heiaheia_api_oa_secret = db.StringProperty()

class TableSportInfo(db.Model):
   name       = db.StringProperty()    # sport name
   id         = db.IntegerProperty()   # sport id
   param_list = db.StringProperty()    # ; separated string of parameters
   url_icon   = db.StringProperty() 

class TableSportInfoString(db.Model):
   all_sports = db.TextProperty()

