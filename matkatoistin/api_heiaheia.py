   
import urlparse
from urllib import urlencode
import oauth2 as oauth
import xml.dom.minidom
import json

from api_keys import api_keys

request_token_url = 'http://www.heiaheia.com/oauth/request_token'
access_token_url = 'http://www.heiaheia.com/oauth/access_token'
authorize_url = 'http://www.heiaheia.com/oauth/authorize'


##########################################################################################################
# This is from example: https://github.com/simplegeo/python-oauth2
##########################################################################################################
def generate_oauth_link( return_dict ):

   consumer = oauth.Consumer(api_keys.consumer_key, api_keys.consumer_secret)
   client = oauth.Client(consumer)

   # Step 1: Get a request token. This is a temporary token that is used for 
   # having the user authorize an access token and to sign the request to obtain 
   # said access token.

   request_token_url_red = request_token_url + "?" + urlencode( { 'oauth_callback' : return_dict['url_callback'] } )
   resp, content = client.request(request_token_url_red , "GET")
   
   if resp['status'] != '200':
      return_dict['message'] =  "Invalid oauth response %s." % resp['status']
      return False
   
   request_token = dict(urlparse.parse_qsl(content))

   # Step 2: Redirect to the provider. Since this is a CLI script we do not 
   # redirect. In a web application you would redirect the user to the URL
   # below.

   oauth_link = authorize_url + "?" + urlencode( { 'oauth_token'    : request_token['oauth_token'] } )
   
   return_dict['oauth_link']         = oauth_link
   return_dict['oauth_token']        = request_token['oauth_token']
   return_dict['oauth_token_secret'] = request_token['oauth_token_secret']
   
   return True


def get_oauth_tokens( conf ):
   # Step 3: Once the consumer has redirected the user back to the oauth_callback
   # URL you can request the access token the user has approved. You use the 
   # request token to sign this request. After this is done you throw away the
   # request token and use the access token returned. You should store this 
   # access token somewhere safe, like a database, for future use.
   print "Request Token (try2):"
   print "    - oauth_token        = %s" % conf['oauth_token']
   print "    - oauth_token_secret = %s" % conf['oauth_token_secret']
   print "    - oauth_verify       = %s" % conf['oauth_verifier']
   
   token = oauth.Token( conf['oauth_token'], conf['oauth_token_secret'])
   token.set_verifier( conf['oauth_verifier'])
   
   consumer = oauth.Consumer(api_keys.consumer_key, api_keys.consumer_secret)
   client = oauth.Client(consumer, token)
   resp, content = client.request(access_token_url, "POST")
   

   print json.dumps( resp )
   print json.dumps( content )

   access_token = dict(urlparse.parse_qsl(content))
   
   print json.dumps( access_token )
   
   if access_token.has_key( 'oauth_token' ) and access_token.has_key('oauth_token_secret'):
      print "Access Token aquired"
   else:
      print "Something went wrong with the authorization!";
      conf["message"] = "Something went wrong with the authorization!"
      return False;
      
   conf["oauth_token"]        = access_token['oauth_token'];
   conf["oauth_token_secret"] = access_token['oauth_token_secret'];
   
   return True;


def get_client( heiaheia_api_oa_token, heiaheia_api_oa_secret ):
   consumer = oauth.Consumer(key=api_keys.consumer_key, secret=api_keys.consumer_secret)
   access_token = oauth.Token(key=heiaheia_api_oa_token, secret=heiaheia_api_oa_secret )
   client = oauth.Client(consumer, access_token)
   return client



##########################################################################################################
#
##########################################################################################################
def upload_new_entry( client, sport_info ):
  full_url = 'http://www.heiaheia.com/api/v1/training_logs/';
  
  post_data = {
       'sport_id'                  : sport_info['param_sport_id'],
       'training_log[date]'        : sport_info['param_date'],
       'training_log[duration_h]'  : sport_info['param_hours'],
       'training_log[duration_m]'  : sport_info['param_minutes'],
       'training_log[comment]'     : sport_info['param_comment']
       }
  
  
  sport_param_loop=0
  for key in sport_info:
     if key.startswith("param_f_"):
        param_name=key.replace("param_f_","")
        post_data[ "training_log[sport_params][%d][name]" % sport_param_loop ]  = param_name
        post_data[ "training_log[sport_params][%d][value]" % sport_param_loop ] = sport_info[key]
        sport_param_loop += 1
  
  # Check that we have no zero lengths fields
  clean_post_data = dict( (k, v ) for k, v in post_data.iteritems() if v )
       
  print "Uploading ... : %s " % clean_post_data 
  
  resp, content = client.request(full_url, "POST", urlencode( post_data ) );
  #
  if resp['status'] != '200' :
      return " Error responce: " + resp['status'] + "\n ----------- ERROR: GOT CONTENT --------------\n" + content
     
  return None;          

##########################################################################################################
#
##########################################################################################################
def update_sports_for( client, sport_name, sport_id  ):
  
  full_url = "http://www.heiaheia.com/api/v1/sports/%d" % sport_id;
  
  resp, content = client.request(full_url , "GET" )
  
  if resp['status'] != '200' :
     print " Error responce: " + resp['status'] ;
     print "----------- ERROR: GOT CONTENT --------------"
     print content
     return None

  dom = xml.dom.minidom.parseString(content)
  
  nodes = dom.getElementsByTagName("sport-param");
  parameters=[]
  
  for node in nodes:
     parameters.append( node.getElementsByTagName("name")[0].firstChild.nodeValue )
  
  icon = dom.getElementsByTagName("icon")[0].firstChild.nodeValue
  
  return { 'param' : parameters, 'icon' : icon }
  

##########################################################################################################
#
##########################################################################################################
def download_sport_list( client, page_loop ):

      sport_hash = {}

      full_url = "http://www.heiaheia.com/api/v1/sports?page=%s" % page_loop

      resp, content = client.request(full_url , "GET" )

      if resp['status'] != '200' :
         print " Error responce: " + resp['status'] ;
         print "----------- ERROR: GOT CONTENT --------------"
         print content
         return None
         
      # print "Fetched page %s" % page_loop
      
      dom = xml.dom.minidom.parseString(content)
      
      if ( dom == None ):
         print "Error while parsing"
         return None
      
      sport_nodes =  dom.getElementsByTagName("sport");
      
      for node in sport_nodes:
         sport_name   = node.getElementsByTagName("name")[0].firstChild.nodeValue
         sport_name   = sport_name.replace("'"," ");
         sport_id     = node.getElementsByTagName("id")[0].firstChild.nodeValue
         sport_hash[ sport_name ] = sport_id 
         

      return sport_hash;
