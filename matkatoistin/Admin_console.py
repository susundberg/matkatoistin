import urlparse
import oauth2 as oauth
import urllib
import sys
import json
import os


import jinja2
import webapp2
from google.appengine.api import users

import api_heiaheia
import common
import datatables

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

#######################################################################################
#
#######################################################################################
class Admin_console(webapp2.RequestHandler):
    
   def get_current_offset( self ):
      try:
         current_offset = int(self.request.get("offset"))
      except ValueError:
         current_offset = 0
         
      return current_offset
         
   #######################################################################################
   # Get method to check that we have full access
   #######################################################################################
   def get(self):
      user = users.get_current_user()
      if user:
            if users.is_current_user_admin() == False:
               error_message = "Sorry, you dont have admin rights"
               common.show_error_message( self.response, error_message );
               return 
      else:
         common.show_error_message( self.response, 
                                    "Sorry, you have to login first", "Click here to login with google account", 
                                    users.create_login_url(self.request.uri) );
         return 
      
      template_values = {};
      if self.request.get('action') == "sport_list":
         template_values['message'] = self.update_sport_list( user.user_id() ) ;
      elif self.request.get('action') == "sport_info":
         template_values['message'] = self.update_sport_list_info( user.user_id() , self.request.get('sport_id') );
      elif self.request.get('action') == "sport_string":
         template_values['message'] = self.update_sport_list_string( );
      else:
         template_values['message'] = "No action selected";
      
      query    = datatables.TableSportInfo.all().order('name')
      
      current_offset = self.get_current_offset(  )

         
      template_values['sport_list']     = query.fetch( 100, current_offset )
      template_values['sport_list_len'] = len( template_values['sport_list']     )
      template_values['offset'] = current_offset ;
      
      # Ok we have user and the user is admin
      template = JINJA_ENVIRONMENT.get_template('html/admin.html')
      self.response.write(template.render(template_values))
      return 
   
   def update_sport_list_string( self ):
      
       # Construct string containing all sports separated with ';'
       query = datatables.TableSportInfo.all()
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
       return "All sports added as string ok. Now we know %d sports " % len(full_string_list )
    
          
   
   #######################################################################################
   # The actual implementation for fetching the list
   #######################################################################################
   def update_sport_list(self, username):
      (client, message ) = common.get_oauth_client( username )
      
      if ( client == None ):
         return message
      
      retmessage = "So for good, oauth ready\n"
      sport_name_hash = api_heiaheia.download_sport_list( client )
      
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
         
      return retmessage    
         
   #######################################################################################
   # The actual implementation for fetching the list
   #######################################################################################
   def update_sport_list_info(self, username, sport_id):
      
      (client, message ) = common.get_oauth_client( username )
      
      if client == None:
         return message
      
      retmessage = "Oauth ok\n"
      
      query = datatables.TableSportInfo.all().order('name');
      
      
      if sport_id != "":
         try:
            query.filter("id =" , int( sport_id ) )
            sport_entry_list = query.fetch(1)
         except ValueError:
            retmessage=retmessage + "Invalid sport_id!\n"
            return retmessage
      else :
          current_offset = self.get_current_offset(  )
          sport_entry_list = query.fetch( 100, offset=current_offset );
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
      return retmessage
