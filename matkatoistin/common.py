
import jinja2
import webapp2
import os

from google.appengine.api import users

import datatables
import api_heiaheia
import json

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


def write_responce( response,  template_page, template_values):
   if 'machine' in template_values and template_values['machine']:
      print "ITS MACHINE!"
      template_values['page'] = template_page
      response.write( json.dumps( template_values ) )
   else:
      template = JINJA_ENVIRONMENT.get_template(template_page)
      response.write(template.render(template_values))
   
   
def get_template_base( machine = None ):
   ret = {}
   user = users.get_current_user()
   
   if user == None:
      return ret
   
   ret['user_id']    = user.user_id()
   ret['user_name']  = user.nickname()
   ret['url_logout'] = users.create_logout_url('/')
   
   if machine:
      ret['machine']    = "true"
   return ret;


def get_loginuser( response, machine = None ):
   user = users.get_current_user()
   
   if user == None:
      template_values = {};
      template_values ['login_url'] = users.create_login_url("?justdidlogin=1")
      if machine:
         template_values['machine'] = "true"
         
      template_page = 'html/loginpage.html'
      
      write_responce( response, template_page , template_values )
      return None
   
   return user


def get_userinfo( username ):
   query    = datatables.TableUserInfo.all().filter("username =",username)
   userinfo = query.get()
   return userinfo;


def get_oauth_client( username ):      
   userinfo = get_userinfo( username )
   
   if userinfo == None:
      return (None, "You need to make proper OAUTH to HeiaHeia first.")
   
   if userinfo.heiaheia_api_oa_token == None or userinfo.heiaheia_api_oa_secret == None:
      return (None, "Internal error, OAUTH tokens corrupted, contact admin.")
   
   client = api_heiaheia.get_client( userinfo.heiaheia_api_oa_token, userinfo.heiaheia_api_oa_secret )
   return (client, userinfo)




def show_error_message( response, message, link_info = None, link = None ):
   if link_info == None or link == None:
      link_info = "Click here to return mainpage"
      link = "/"
   
   values = get_template_base (  );
   
   template = JINJA_ENVIRONMENT.get_template('html/error.html')
   
   values['message']   = message
   values['link_info'] = link_info
   values['link']      = link 
   
   response.set_status( code=400, message=message ) 
   response.write(template.render(values))
   return False;
   
   
      
   
   


      