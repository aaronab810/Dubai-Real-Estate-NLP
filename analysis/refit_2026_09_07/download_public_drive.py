"""Download an already identified shared Drive file, including its confirmation form."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import urllib.request
import urllib.parse
import http.cookiejar
import json
import hashlib

p=argparse.ArgumentParser()
p.add_argument('file_id');p.add_argument('output',type=Path)
a=p.parse_args()
class Form(HTMLParser):
    action=None
    fields={}
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='form' and d.get('id')=='download-form': self.action=d.get('action')
        if tag=='input' and 'name' in d: self.fields[d['name']]=d.get('value','')
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
url='https://drive.google.com/uc?'+urllib.parse.urlencode({'export':'download','id':a.file_id})
response=opener.open(url,timeout=90)
if 'text/html' in response.headers.get('Content-Type',''):
    page=response.read().decode('utf-8')
    form=Form();form.feed(page)
    if not form.action or urllib.parse.urlparse(form.action).hostname not in {'drive.usercontent.google.com','drive.google.com'}:
        raise RuntimeError('No recognized Google download confirmation form; file may require sign-in.')
    response=opener.open(form.action+'?'+urllib.parse.urlencode(form.fields),timeout=90)
if 'text/html' in response.headers.get('Content-Type',''): raise RuntimeError('Received HTML rather than file content')
a.output.parent.mkdir(parents=True,exist_ok=True)
sha=hashlib.sha256();size=0
with a.output.open('wb') as target:
    while chunk:=response.read(1024*1024):
        target.write(chunk);sha.update(chunk);size+=len(chunk)
print(json.dumps({'file_id':a.file_id,'path':str(a.output),'bytes':size,'sha256':sha.hexdigest()}))
