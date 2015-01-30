__author__ = 'dasumba'

#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep
import cgi

PORT_NUMBER = 8080

class Interpreter:
    def __init__(self):
        self.idx = 0
        return

    def GetNavigationMenuRef(self, args):
        while True:
            try:
                if WebServer.cp.GetInstalledMods()[self.idx][4] is not None:
                    if WebServer.cp.GetInstalledMods()[self.idx][4].GetID()[1]:
                        return WebServer.cp.GetInstalledMods()[self.idx][4].GetID()[1]
                else:
                    self.NextIDX()
            except AttributeError:
                self.NextIDX()
            except IndexError:
                return ""
        return ""

    def GetNavigationMenuName(self, args):
        while True:
            try:
                if WebServer.cp.GetInstalledMods()[self.idx][4] is not None:
                    if WebServer.cp.GetInstalledMods()[self.idx][4].GetID()[0]:
                        return WebServer.cp.GetInstalledMods()[self.idx][4].GetID()[0]
                else:
                    self.NextIDX()
            except AttributeError:
                self.NextIDX()
            except IndexError:
                return ""
        return ""


    def NextIDX(self):
        self.idx += 1
        return


    def Command(self, args):
        if args.find('$DroneName') != -1:
            args = args.replace("$DroneName", WebServer.cp.Drone_Name)
        if args.find('$navigation-ref') != -1:
            args = args.replace('$navigation-ref', self.GetNavigationMenuRef(args))
        if args.find('$navigation-name') != -1:
            args = args.replace('$navigation-name', self.GetNavigationMenuName(args))
        if args.find('$active') != -1:
            args = args.replace('$active', 'active')
        if args.find('$navigation++') != -1:
            self.NextIDX()
            args = args.replace('$navigation++', '')
        return args

# This class will handles any incoming request from
#the browser
class myHandler(BaseHTTPRequestHandler):
    #Handler for the GET requests
    def do_GET(self):
            if self.path == "index.html":
                self.path = "index.html"

            self.path = "./WEB/DEFAULT_DESIGN/" + self.path
            print self.path
            try:
                #Check the file extension required and
                #set the right mime type
                sendReply = False
                if self.path.endswith(".html"):
                    mimetype = 'text/html'
                    sendReply = True
                if self.path.endswith(".jpg"):
                    mimetype = 'image/jpg'
                    sendReply = True
                if self.path.endswith(".png"):
                    mimetype = 'image/png'
                    sendReply = True
                if self.path.endswith(".gif"):
                    mimetype = 'image/gif'
                    sendReply = True
                if self.path.endswith(".js"):
                    mimetype = 'application/javascript'
                    sendReply = True
                if self.path.endswith(".css"):
                    mimetype = 'text/css'
                    sendReply = True

                if sendReply == True:
                    #Open the static file requested and send it
                    f = open(curdir + sep + self.path)
                    self.send_response(200)
                    self.send_header('Content-type', mimetype)
                    self.end_headers()
                    data = f.read()
                    if mimetype == 'text/html':
                        data = Interpreter().Command(data)
                    self.wfile.write(data)
                    f.close()
                return

            except IOError:
                self.send_error(404, 'File Not Found: %s' % self.path)

    #Handler for the POST requests
    def do_POST(self):
        if self.path == "/send":
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                         'CONTENT_TYPE': self.headers['Content-Type'],
                })

            print "Your name is: %s" % form["your_name"].value
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Thanks %s !" % form["your_name"].value)
            return

class WebServer:
    def __init__(self, CP):
        self.server = None
        self.cp = CP
        global WebServer
        WebServer = self
    def start(self):
        try:
            #Create a web server and define the handler to manage the
            #incoming request
            self.server = HTTPServer(('', PORT_NUMBER), myHandler)
            print 'Started httpserver on port ', PORT_NUMBER

            #Wait forever for incoming http requests
            self.server.serve_forever()

        except KeyboardInterrupt:
            print '^C received, shutting down the web server'
        return
    def stop(self):
        self.server.socket.close()
        return
