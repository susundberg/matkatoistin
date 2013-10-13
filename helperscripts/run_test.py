import requests
import json
import time
import inspect
import string
import random
import sys
import datetime


def print_usage():
   print "USAGE: ./python test_server <host to test> <settings.json>"

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
      
 def get_request( self, url ):
   self.last_request = requests.get(self.host_base + url , cookies=self.cookies )
   return self.last_request 

 def error_exit(self):
    print "ERROR! Request failed\n"
    PrintFrame()
    PrintRequest(self.last_request )
    exit(1);
    
 def do_testing(self):
     
   print "TESTING SERVER " + host_base
   r = self.get_request( "/" )

   #######################################################
   # LOGIN
   #######################################################
   if (r.status_code != requests.codes.ok ):
      self.error_exit()
      
   PrintTestOk()

   # Then do login 
   r = self.get_request("?machine=true")
   ret = json.loads( r.text )
   loginurl = ret['login_url']

   r = self.get_request( "_ah/login?email=test%40example.com&admin=True&action=Login&continue=http%3A%2F%2Flocalhost%3A8080%2F%3Fjustdidlogin%3D1" )
   if (r.status_code != requests.codes.ok ):
      PrintFrame()
      PrintRequest(r)
      exit(1);

   cookies = r.history[0].cookies

   print "GOT COOKIES: %s"  % cookies


   r = self.get_request( "oauthme?machine=true", cookies=cookies )
   if (r.status_code != requests.codes.ok ):
      PrintFrame()
      PrintRequest(r)
      exit(1);

   PrintRequest(r)
   resp = json.loads(r.text)
   if "oauth_link" not in resp :
      print "Invalid response, key oauth_link missing"
      PrintFrame()
      exit(1)

   print "Please click following link " + resp['oauth_link'] 
   wait_for_input = raw_input("Press enter when authorization done")
   # The callback will set browser to local page, handling the rest
   # We should now have proper oauth and all, get some sports



###########################################################################################################
# MAIN SCRIPT STARTS HERE
###########################################################################################################
if len(sys.argv) != 3:
   print_usage()
   exit(0)
   
host_base         = sys.argv[1];
settings_file     = sys.argv[2];
test = TestScript( host_base )
test.do_testing()








