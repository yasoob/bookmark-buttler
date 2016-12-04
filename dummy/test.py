import requests

with open('remote_urls.txt', 'r') as f:
    data = f.readlines()

for c, url in enumerate(data):
    print "Doing [%s/%s]" %(c+1, len(data)) 
    requests.get('http://localhost:5000/book?url='+url.strip())