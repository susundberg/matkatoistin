import requests
import json
import time
import inspect
import string
import random
import sys
import datetime


def print_usage():
   print "USAGE: ./python test_server <host to test> "

def PrintTestOk():
  callerframerecord = inspect.stack()[1] 
  frame = callerframerecord[0]
  info = inspect.getframeinfo(frame)
  print "Test:" + str( info.filename ) + ":" + str( info.lineno ) + " OK!"
  
  
def PrintFrame():
  callerframerecord = inspect.stack()[1]    # 0 represents this line
                                            # 1 represents line at caller
  frame = callerframerecord[0]
  info = inspect.getframeinfo(frame)
  print "FILE:" + str( info.filename ) + ":" + str( info.lineno )
  # print "FUNC:"info.function                       # __FUNCTION__ -> Main
 
def PrintRequest(r):
   print "-------------HEADERS------------------"
   print "STATUS CODE %d " % r.status_code
   print r.headers
   print "-------------CONTENT------------------"
   print r.text
   print "-------------COOKIE ------------------"
   print r.cookies
   
   
class TestScript:
 def __init__(self, host):
      self.host_base = host
      self.cookies   = None
   
 def read_config(self, settings_file):
   compulsory_settings = ["oauth_key", "oauth_secret" ]

   try:
      fid = open(settings_file,"r") 
      settings = json.loads( fid.read() )
   except IOError:
      template = {}
      for key in compulsory_settings:
         template[key] = "COMPULSORY SETTING"
      open(settings_file,"w").write(json.dumps(template))
      print "\n Error! Configuration file missing, wrote template. Bye!\n"
      exit(1)
      
   errors = 0


   for key in compulsory_settings:
      if key not in settings :
         print "Key '%s' is missing from settings file!"
         errors += 1
         settings[key] = "MISSING"
         
   if errors > 0:
      open(settings_file,"w").write(json.dumps)
      print "\n ERRORS on config. Writing template config file all bail out!\n"
      exit(1)
      
 def get_json( self ):
    try:
       ret = json.loads( self.last_request.text )
    except:
       print "Error! JSON loading failed"
       self.error_exit()
    return ret
 
 def get_request( self, url ):
   self.last_request_address = self.host_base + url 

   if self.cookies:
      self.last_request = requests.get( self.last_request_address  , cookies=self.cookies )
   else:
      self.last_request = requests.get( self.last_request_address  )
      
   if ( self.last_request .status_code != requests.codes.ok ):
      self.error_exit()
      
   return self.last_request 

 def error_exit(self):
    print "ERROR! Request failed on url '%s'\n" % self.last_request_address 
    PrintFrame()
    PrintRequest(self.last_request )
    exit(1);
    
 def do_testing(self):
     
   print "TESTING SERVER " + host_base

   # Do login 
   r = self.get_request("?machine=true")
   ret = json.loads( r.text )
   loginurl = ret['login_url']

   r = self.get_request( "_ah/login?email=test%40example.com&admin=True&action=Login&continue=http%3A%2F%2Flocalhost%3A8080%2F%3Fjustdidlogin%3D1" )

   self.cookies = r.history[0].cookies

   print "GOT COOKIES: %s"  % self.cookies

   r = self.get_request( "admin" )
   r = self.get_request( "admin?action=sport_list&page=0&machine=true")
   r = self.get_request( "admin?action=sport_string&machine=true")
   r = self.get_request( "admin?action=sport_info&offset=0&machine=true")
   current_date=datetime.datetime.now().strftime("%Y-%m-%d")
   r = self.get_request( "?page=details&dates=%s&sport=Dancing&machine=true" % current_date  )
   r = self.get_request( "?page=commit&param_dates=%s&param_sport=Dancing&param_hours=1&param_minutes=2&param_f_comment=Hello&machine=true" % current_date )
   
   ret = self.get_json()
   
   if "commit_ok" not in ret:
      print "Something went wrong with commit"
      self.error_exit
   
   print "COMMIT OK, All fine, bye!"
   



###########################################################################################################
# MAIN SCRIPT STARTS HERE
###########################################################################################################
if len(sys.argv) != 2:
   print_usage()
   exit(0)
   
host_base         = sys.argv[1];
test = TestScript( host_base )
test.do_testing()








