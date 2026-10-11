import http.server, json, sys
LOG=[]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _send(self,o,code=200):
        b=json.dumps(o).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); body=self.rfile.read(n).decode()
        LOG.append((self.path,body)); open('/tmp/mock_log.txt','a').write(self.path+' '+body[:200]+'\n')
        if self.path.endswith('/media'): self._send({'id':'C%d'%len(LOG)})
        elif self.path.endswith('/media_publish'): self._send({'id':'M%d'%len(LOG)})
        else: self._send({},404)
    def do_GET(self):
        LOG.append((self.path,'')); self._send({'status_code':'FINISHED','id':'x'})
http.server.HTTPServer(('127.0.0.1',8765),H).serve_forever()
