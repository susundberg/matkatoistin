from google.appengine.api import users

import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2
import json

import common
import datatables
import api_heiaheia
import re


###################################################################################################
# This is our main landing page
###################################################################################################
class HelloPage(webapp2.RequestHandler):
   def get(self):
      template_values = { }
      
      user = common.get_loginuser( self.response, self.request.get("machine") )
      if user == None:
         return 
      
      if self.request.get("justdidlogin"):
         if self.check_for_datatable( user  )== None:
            return
         
      template_values = common.get_template_base( self.request.get("machine") )
      
      if self.request.get("page") == "commit":
         
         template_page = 'html/index_commit.html'
         all_params  = self.request.arguments()
         post_params = {}
         
         
         sport_name = self.request.get('param_sport')
         sport_entry = datatables.TableSportInfo.all().filter("name =", sport_name ).get()

         if sport_entry == None:
            common.show_error_message( self.response, "Cannot find sport named '%s'" % sport_name)
            return
         
         post_params['param_sport_id'] = "%d" % sport_entry.id
         
         for param in all_params:
            if param.startswith("param_"):
               post_params[param] = self.request.get(param)  
               
         (client, usertable ) = common.get_oauth_client( user.user_id(),  )
      
         if client == None:
           common.show_error_message( self.response, usertable )
           return 
        
         if 'param_f_comment' not in post_params:
           post_params['param_comment'] = ""
         else:
           post_params['param_comment'] = post_params['param_f_comment']
           del post_params['param_f_comment']
           
         all_dates = post_params["param_dates"].split(",")
         for date in all_dates:
             if len( date ) < 4 : 
                common.show_error_message( self.response, "Something is wrong with date '%s'" % date)
                return
             post_params['param_date'] = date
             print "Upload for " + date
             ret = api_heiaheia.upload_new_entry( client, post_params )
             if ret != None:
               common.show_error_message( self.response, "Error while uploading: " + ret )
               return 
            
         template_values['commit_ok'] = 1       
         last_post_params = {}
         for key in post_params :
            keynew = key.replace("param_","")
            keynew = keynew.replace("f_","")
            last_post_params[keynew] = post_params[key]
            
            
         usertable.last_sport = json.dumps( last_post_params );
         usertable.put()
         
         
         
      elif self.request.get("page") == "details":
         template_page = 'html/index_details.html'
         dates=self.request.get("dates") 
         sport=self.request.get("sport")
         
         template_values['param_dates']=dates
         template_values['param_sport']=sport
         
         if dates == "" or sport == "":
            common.show_error_message( self.response, "Invalid URL!" )
            return 
         
         usertable = self.check_for_datatable( user )
         
         if usertable == None:
            common.show_error_message( self.response, "Internal error, cannot get usertable at details!" )
            return
         

          
         sport_entry = datatables.TableSportInfo.all().filter('name =', sport ).get()
         
         if sport_entry == None:
            common.show_error_message( self.response, "Cannot find sport '%s'!" % sport )
            return 
         
         last_param_values = {}
         if usertable.last_sport != None:
            last_values = json.loads( usertable.last_sport )
            if "sport_id" in last_values :
               if int(last_values["sport_id"]) == sport_entry.id:
                  last_param_values = last_values
         
         template_values['sport_params_compulsory'] = [ "hours", "minutes" ]
         
         for param_comp in template_values['sport_params_compulsory'] :
            if param_comp not in last_param_values:
               last_param_values[param_comp] = ""
         
         param_list=["comment"]  
         explain_hash = {}
         for param in sport_entry.param_list.split(";"):
            
            if param == "":
              continue
            
            param_new = re.sub( r"[^\w_]","_",param);
            explain_hash[param_new]=param.lower()
            param_list.append(param_new)
            if param_new not in last_param_values:
              last_param_values[param_new] = ""
              
         template_values['last_param_values'] = last_param_values
         template_values['sport_params']      = param_list
         template_values['sport_params_text'] = explain_hash   
         template_values['sport_entry']       = sport_entry
         
      else:
         template_page = 'html/index.html'
         full_list = self.get_sport_list()
         
         if full_list == None:
            return
         
         template_values['sport_list'] = full_list
         
      common.write_responce( self.response,  template_page, template_values)

      

   # Check that we have properply added user in database
   def check_for_datatable(self, user ):
      userinfo = common.get_userinfo( user.user_id() )
      
      if userinfo != None:
         return userinfo
      
      # We did not have proper user created, we need to show oauth page
      to_redirect = '/oauthme'
      
      if self.request.get("machine"):
         to_redirect = to_redirect + "?machine=1"
      print "USERINFO REDIRECT: " + to_redirect
      self.redirect(to_redirect)
      return None
   
   def get_sport_list( self ):
      entry = datatables.TableSportInfoString.all().get()
      if entry == None or entry.all_sports == None:
         common.show_error_message( self.response, "Cannot get full sport list for some reason!" )
         return None
      
      full_list = entry.all_sports.split(";")
      full_string = "[\""
      full_string += ( "\",\"".join(full_list) )
      full_string += ( "\"]" );
      
      
      
      return full_string

###################################################################################################
# This is request for getting for OAUTH tokens for current user
###################################################################################################
   
class ListPage(webapp2.RequestHandler):
   def get(self):
      template_values = { }
      
      user = common.get_loginuser( self.response, self.request.get("machine") )
      if user == None:
         return 
      

         
      template_values = common.get_template_base( self.request.get("machine") )
   
      entry = datatables.TableSportInfoString.all().get()

      if entry == None:
         common.show_error_message( self.response, "Cannot get full sport list for some reason!" )
         return None
      
      items = entry.all_sports.split(";")
      items.sort()
      template_values['sport_list'] = items
      template_page = 'html/index_list.html'
      common.write_responce( self.response,  template_page, template_values)
###################################################################################################
# This is request for getting for OAUTH tokens for current user
###################################################################################################
   
class AboutPage(webapp2.RequestHandler):
   def get(self):
      template_values = { }
         
      template_values = common.get_template_base( self.request.get("machine") )
      template_page   = 'html/index_about.html'
      
      common.write_responce( self.response,  template_page, template_values)
      
      
###################################################################################################
# This is request for getting for OAUTH tokens for current user
###################################################################################################
class OauthPage(webapp2.RequestHandler):
   # First step is to show page with 'please click to auth' with proper oauth linke
   def get(self):
      is_machine = self.request.get("machine")
      
      user = common.get_loginuser( self.response, is_machine  )
      if user == None:
         return 
      
      template_values = common.get_template_base( is_machine  )
     
     
      if self.request.get("auth_done") != "yes":
         values = {} 
         if is_machine :
            values['url_callback'] = self.request.host_url
         else:   
            values['url_callback'] = self.request.uri + "?auth_done=yes"
         
         print "SET CALLBACK: " + values['url_callback']
         
         if api_heiaheia.generate_oauth_link( values ) == False:
            common.show_error_message( self.response, "Error while get oauth link: %s " % values["message"] )
         
         
         # make sure there are no old temporary auths
         query       = datatables.TableTempUserInfo.all().filter("username =",user.user_id())
         oldinfos    = query.fetch(16)
         for oldinfo in oldinfos:
            print "Remove entry : " + oldinfo.heiaheia_api_oa_token 
            oldinfo.delete () 
         
         tmpuserinfo                        = datatables.TableTempUserInfo()
         tmpuserinfo.username               = user.user_id()
         tmpuserinfo.heiaheia_api_oa_token  = values["oauth_token"]
         tmpuserinfo.heiaheia_api_oa_secret = values["oauth_token_secret"]
         tmpuserinfo.put()
         template_values['oauth_link']      = values["oauth_link"]
         
      else:
         query       = datatables.TableTempUserInfo.all().filter("username =",user.user_id())
         tmpuserinfo = query.get()
         
         if tmpuserinfo == None:
            common.show_error_message( self.response, "Error while aquiring temp oauth tokens!" )
            return 

         tokens = {}
         tokens['oauth_token']        = tmpuserinfo.heiaheia_api_oa_token
         tokens['oauth_token_secret'] = tmpuserinfo.heiaheia_api_oa_secret
         tokens['oauth_verifier']     = self.request.get("oauth_verifier")
         
         if tokens['oauth_verifier'] == "":
            common.show_error_message( self.response, "Error while aquiring verifier token!" )
            return
            
         # Change the temporary token to access token
         if api_heiaheia.get_oauth_tokens(tokens) == False:
            common.show_error_message( self.response, "Error while aquiring oauth tokens: %s " % tokens["message"] )
            return 
         
         # We have oauth done ok, now we can add proper user
         userinfo = datatables.TableUserInfo()
         userinfo.username = user.user_id()
         
         # Note: These are updated!
         userinfo.heiaheia_api_oa_token  = tokens["oauth_token"]
         userinfo.heiaheia_api_oa_secret = tokens["oauth_token_secret"]
         userinfo.last_sport = None
         
         userinfo.put()
         tmpuserinfo.delete()
         template_values["oauth_success"] = "yes"
      
      
      # All done
      template_page = 'html/oauth.html'
      common.write_responce( self.response,  template_page , template_values)
     
   

###################################################################################################
# Main redirection
###################################################################################################
application = webapp2.WSGIApplication([
    ('/', HelloPage),
    ('/sport_list', ListPage),
    ('/about', AboutPage),
    ('/oauthme', OauthPage)
    ], debug=True)

