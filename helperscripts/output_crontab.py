
#!/usr/bin/python

print "cron:"

loop = 0
for loop in range(0,30):
   print "- description: fetch page %d" % loop
   print "  url: admin?action=sport_list&page=%d" % loop
   print "  schedule: every sunday 00:%02d" % loop
   print " "
   
print " "
print " - description: update all sports string "
print "   url: admin?action=sport_string"
print "   schedule: every sunday 00:%d" % (loop + 1)
print " "
print " "

for loop in range(0,59):
   print "- description: fetch sport info %d" % loop
   print "  url: admin?action=sport_info&offset=%d" % (loop*10)
   print "  schedule: every sunday 01:%02d" % loop
   print " "
 
 



