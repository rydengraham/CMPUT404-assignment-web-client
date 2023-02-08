#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# Modified 2023 by Ryden Graham
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

STANDARD_PORT = 80

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    def get_path(self, urlData):
        #Fix path if / is missing
        path = urlData.path
        if not path.endswith('/'):
            path += '/'

        return path

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port or STANDARD_PORT))
        self.socket.settimeout(30)
        return None

    def get_code(self, headerDict):
        if 'HTTP/1.1' in headerDict:
            code = [h for h in headerDict['HTTP/1.1'] if h.isdigit()]
            if len(code) > 0:
                return int(code[0])
        if 'HTTP/1.0' in headerDict:
            code = [h for h in headerDict['HTTP/1.0'] if h.isdigit()]
            if len(code) > 0:
                return int(code[0]) 
        return None

    def get_headers(self,data):
        headers = data.split(b'\r\n\r\n')[0]
        # Michel Keijzers
        # https://stackoverflow.com/users/1187220/michel-keijzers
        # Convert list of strings to dictionary
        # https://stackoverflow.com/a/22981155 
        headerDictionary = {}
        for header in headers.split(b'\r\n'):
            headerInfo = header.decode('utf-8').split(' ')
            headerDictionary[headerInfo[0]] = headerInfo[1:]
        return headerDictionary

    def get_body(self, data):
        return data.split(b'\r\n\r\n')[1]

    def get_body_encoding(self, headerDict):
        bodyEncoding = "utf-8"
        
        if 'Content-Type:' in headerDict:
            charset = [h for h in headerDict['Content-Type:'] if h.startswith('charset')]
            if (len(charset) > 0):
                bodyEncoding = charset[0][8:]

        return bodyEncoding
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        try:
            while not done:
                part = sock.recv(1024)
                sock.settimeout(0.1)
                if (part):
                    buffer.extend(part)
                else:
                    done = not part
        except socket.timeout:
            pass
        sock.settimeout(30)
        return (self.get_headers(buffer), self.get_body(buffer))

    def GET(self, url, args=None):
        # Parse url
        urlData = urllib.parse.urlparse(url)
        # Set up socket
        self.connect(urlData.hostname, urlData.port)

        path = self.get_path(urlData)

        requestBody = ("GET " + path + " HTTP/1.1\r\n" +
            "Host: " + urlData.hostname + "\r\n" +
            "Accept-Charset: UTF-8" +
            "\r\n\r\n")

        # Send GET request
        self.sendall(requestBody)

        headerDict, body = self.recvall(self.socket)

        bodyEncoding = self.get_body_encoding(headerDict)

        code = self.get_code(headerDict)
        bodyString = body.decode(bodyEncoding)
        print(code)
        if code == 200:
            print(bodyString)
        self.close()

        return HTTPResponse(code, bodyString)

    def POST(self, url, args=None):
        # Parse url
        urlData = urllib.parse.urlparse(url)
        # Set up socket
        self.connect(urlData.hostname, urlData.port)

        postBody = "" if args is None else urllib.parse.urlencode(args)

        path = self.get_path(urlData)

        requestBody = ("POST " + path + " HTTP/1.1\r\n" +
            "Host: " + urlData.hostname + "\r\n" +
            "Accept-Charset: UTF-8" + "\r\n" +
            "Content-Type: application/x-www-form-urlencoded" + "\r\n" +
            "Content-Length: " + str(len(postBody)) +
            "\r\n\r\n" +
            postBody)
        
        # Send POST request
        self.sendall(requestBody)

        headerDict, body = self.recvall(self.socket)

        bodyEncoding = self.get_body_encoding(headerDict)

        code = self.get_code(headerDict)
        if code == 200:
            print(body.decode(bodyEncoding))
        print(code)
        self.close()

        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
