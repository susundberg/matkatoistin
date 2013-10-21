import urlparse
import oauth2 as oauth
import urllib
import sys
import json
import os


import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import taskqueue

import api_heiaheia
import common
import datatables


#######################################################################################
#
#######################################################################################
class AdminPage(webapp2.RequestHandler):
   
   queue_user = "__QUEUE"
   
   def handle_queue_logic_next( self, current_task ):
      #print "NEXT LOGIC CALLED WITH TASK: %s " % current_task
      
      if current_task == None:
         taskqueue.add( url="/admin?action=sport_list&page=0&queue=1", method="GET" )
      elif current_task == "sport_list":
         taskqueue.add( url="/admin?action=sport_string&queue=1", method="GET" )
      elif current_task == "sport_string":
         taskqueue.add( url="/admin?action=sport_info&queue=1", method="GET" )
      elif current_task == "sport_info":   
         return
      else:
         raise Exception("Queue logic asked, but bad task defined '%s'" % current_task )
      
   #######################################################################################
   # 
   #######################################################################################
   def get(self):
      
      self.handle_admin_user()

      template_values = {};
      
      if self.request.get('action') == "sport_list":
         template_values['message'] = self.update_sport_list( AdminPage.queue_user) ;
      elif self.request.get('action') == "sport_info":
         template_values['message'] = self.update_sport_info( AdminPage.queue_user  );
      elif self.request.get('action') == "sport_string":
         template_values['message'] = self.update_sport_list_string( );
      elif self.request.get('action') == "queue":   
         template_values['message'] = "QUEUE STARTED"
         self.handle_queue_logic_next( current_task=None )
      else:
         template_values['message'] = "No action selected";

      if self.request.get('show'):       
         query    = datatables.TableSportInfo.all().order('name')
         
         sport_cursor = memcache.get('sport_cursor')
         
         if sport_cursor and self.request.get("cursor"):
            query.with_cursor(start_cursor=sport_cursor)   
         
         current_offset = self.get_current_offset(  )
         
         template_values['sport_list']     = query.fetch( 10 )
         template_values['sport_list_len'] = len( template_values['sport_list']     )
                  
         sport_cursor = query.cursor()
         memcache.set('sport_cursor', sport_cursor)
         
      common.write_responce( self.response,  "html/admin.html", template_values)
      return 
   
   #######################################################################################
   # 
   #######################################################################################

   def update_sport_list_string( self ):
       # Construct string containing all sports separated with ';'
       query = db.Query(datatables.TableSportInfo, projection=('name',))
       entry_list = query.fetch(limit=None)
       full_string_list = []
       for entry in entry_list:
          full_string_list.append( entry.name )
          
       full_string = ";".join( full_string_list )
      
       query = datatables.TableSportInfoString.all()
       entry = query.get()
       
       if entry == None:
          entry = datatables.TableSportInfoString( all_sports=full_string )
       else :
          entry.all_sports = full_string 
       
       entry.put()
       memcache.set('full_string', full_string )
       
       if self.request.get("queue"):
          self.handle_queue_logic_next("sport_string")
          
       return "All sports added as string ok. Now we know %d sports " % len(full_string_list )
    
          
   
   #######################################################################################
   # The actual implementation for fetching the list
   #######################################################################################
   def update_sport_list(self, username):
      (client, message ) = common.get_oauth_client( username )
      
      if ( client == None ):
         return message
      
      current_page = int(self.request.get("page"))
      
      retmessage = "So for good, oauth ready\n"
      sport_name_hash = api_heiaheia.download_sport_list( client,  current_page )
      
      if sport_name_hash == None:
         retmessage = retmessage + "Call to 'download_sport_list' failed!\n"
         return retmessage
      
      sport_hash={}
      
      for sport_name in sport_name_hash:
         sport_id = int( sport_name_hash[sport_name])
         query    = datatables.TableSportInfo.all().filter("id =", sport_id  );
         entry    = query.get()
         
         if entry == None:
            entry = datatables.TableSportInfo( id = sport_id, name = sport_name, param_list = "" )
         else:
            entry.name       = sport_name
            entry.param_list =  ""
         
         entry.put()
         retmessage = retmessage + "Sport " + sport_name + " ok \n"
      
      
      if self.request.get("queue"):
         if len(sport_name_hash) > 0 :
            taskqueue.add( url="/admin?action=sport_list&page=%d&queue=1" % (current_page + 1), method="GET" )
         else:
            self.handle_queue_logic_next("sport_list")
      return retmessage    
   
   #######################################################################################
   # The actual implementation for fetching the list
   #######################################################################################
   def update_sport_info(self, username ):
      
      (client, message ) = common.get_oauth_client( username )
      
      if client == None:
         return message
      
      retmessage = "Oauth ok\n"
      
      query = datatables.TableSportInfo.all().order('name');
      
      
      if self.request.get("sport_id"):
         try:
            query.filter("id =" , int( sport_id ) )
            sport_entry_list = query.fetch(1)
         except ValueError:
            retmessage=retmessage + "Invalid sport_id!\n"
            return retmessage
      elif self.request.get("info_cursor"):
          query.with_cursor(start_cursor=self.request.get("info_cursor"))
          sport_entry_list = query.fetch( 32 );
      else:
          sport_entry_list = query.fetch( 32 );
          
      retmessage = retmessage + "Start process\n"
      
      for sport_entry in sport_entry_list:
         param_hash = api_heiaheia.update_sports_for( client, sport_entry.name , sport_entry.id )
         retmessage = retmessage + "Processing %s ... " % sport_entry.name 
         if param_hash == None:
            retmessage = retmessage + "ERROR\n"
            return retmessage;
         
         param_list = param_hash['param']
         param_list_str = ";".join( param_list )
         
         retmessage = retmessage + "OK: '" + param_list_str + "' \n"
         
         sport_entry.url_icon   = param_hash['icon']
         sport_entry.param_list = param_list_str
         
         sport_entry.put()
      
      if self.request.get("queue"):
         loop = 0
         if self.request.get("loop"):
            loop = int( self.request.get("loop") ) + 1
            
         if len(sport_entry_list) > 0:
            taskqueue.add( url="/admin?action=sport_info&info_cursor=%s&loop=%d&queue=1" % (query.cursor(),loop), method="GET" )
         else:
            self.handle_queue_logic_next( "sport_info" )
            
      return retmessage



   #######################################################################################
   # 
   #######################################################################################
   def handle_admin_user( self,  ):
      user = users.get_current_user()
      
      if user == None:
         return
      
      if users.is_current_user_admin() == False:
         error_message = "Sorry, you dont have admin rights"
         common.show_error_message( self.response, error_message );
         return 
      
      userinfo = common.get_userinfo( user.user_id() )
      
      if userinfo == None:
         error_message = "Sorry, i cannot find you!"
         common.show_error_message( self.response, error_message );
         return 
      
      # This is admin user, make oauth tokens for queue
      userinfo_queue = common.get_userinfo(AdminPage.queue_user )
      if userinfo_queue == None:
         userinfo_queue = datatables.TableUserInfo()
         
      userinfo_queue.username = AdminPage.queue_user
      userinfo_queue.heiaheia_api_oa_token  = userinfo.heiaheia_api_oa_token
      userinfo_queue.heiaheia_api_oa_secret = userinfo.heiaheia_api_oa_secret
      userinfo_queue.last_sport = None
      userinfo_queue.put()
      




###################################################################################################
# Main redirection
###################################################################################################
application = webapp2.WSGIApplication([
    ('/admin', AdminPage ),
    ], debug=True)
