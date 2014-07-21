# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <headingcell level=1>

# Read Overpass-API to Python Pandas Dataframe

# <markdowncell>

# The [Overpass API](http://wiki.openstreetmap.org/wiki/Overpass_API) provides access to the data behind the Openstreetmaps Map Data.
# The [Overpass-Turbo](http://overpass-turbo.eu/) is the easyiest way to test requests and get the correct code to ask the database.

# <codecell>

import pandas as pd
import requests
import json
pd.set_option('display.max_columns', 200)

# <headingcell level=1>

# Kreuzungen in OSM finden

# <markdowncell>

# Annahme: Eine Kreuzung ist dadurch definiert, dass es ein `Node` gibt, der mindestens zu 2 verschiedenen `highways` gehört.

# <markdowncell>

# Gebiet festlegen, am besten mit einer [Bounding Box](http://boundingbox.klokantech.com/)

# <codecell>

# Get yours at: http://boundingbox.klokantech.com/
bbox = [13.57838,50.962397,13.896025,51.125713]

# Links unten
minLat = bbox[1]
minLon = bbox[0]

# Rechts oben
maxLat = bbox[3]
maxLon = bbox[2]

# <markdowncell>

# Request from [Overpass-Turbo](http://overpass-api.de/api/convert?data=%3C!--%0AThis%20has%20been%20generated%20by%20the%20overpass-turbo%20wizard.%0AThe%20original%20search%20was%3A%0A%E2%80%9CBushaltestelle%E2%80%9D%0A--%3E%0A%3Cosm-script%20output%3D%22json%22%20timeout%3D%2225%22%3E%0A%20%20%3C!--%20gather%20results%20--%3E%0A%20%20%3Cunion%3E%0A%20%20%20%20%3C!--%20query%20part%20for%3A%20%E2%80%9CBushaltestelle%E2%80%9D%20--%3E%0A%20%20%20%20%3Cquery%20type%3D%22node%22%3E%0A%20%20%20%20%20%20%3Chas-kv%20k%3D%22highway%22%20v%3D%22bus_stop%22%2F%3E%0A%20%20%20%20%20%20%3Cbbox-query%20s%3D%2250.973778188690716%22%20w%3D%2213.552322387695312%22%20n%3D%2251.12033393562918%22%20e%3D%2213.898735046386719%22%2F%3E%0A%20%20%20%20%3C%2Fquery%3E%0A%20%20%3C%2Funion%3E%0A%20%20%3C!--%20print%20results%20--%3E%0A%20%20%3Cprint%20mode%3D%22body%22%2F%3E%0A%20%20%3Crecurse%20type%3D%22down%22%2F%3E%0A%20%20%3Cprint%20mode%3D%22skeleton%22%20order%3D%22quadtile%22%2F%3E%0A%3C%2Fosm-script%3E&target=mapql)

# <codecell>

data = 'way["highway"]' # what we are looking for!

osmrequest = {'data': '[out:json][timeout:25];(%s(%s,%s,%s,%s););out body;>;out skel qt;' % (data, minLat, minLon, maxLat, maxLon)}
osmurl = 'http://overpass-api.de/api/interpreter'

# Ask the API
osm = requests.get(osmurl, params=osmrequest)

# <markdowncell>

# The JSON can't be directyl imported to a Pandas Dataframe:
# 
# Thanks to [unutbu from stackoverflow.com](http://stackoverflow.com/questions/24848416/expected-string-or-unicode-when-reading-json-with-pandas) for fiddling this out!

# <headingcell level=3>

# Get all highways

# <codecell>

osmdata = osm.json()
osmdata = osmdata['elements']
for dct in osmdata:
    if dct['type']=='way':
        for key, val in dct['tags'].iteritems():
            dct[key] = val
        del dct['tags']
    else:
        pass # nodes

# <headingcell level=3>

# Now put everything to the Pandas Dataframe

# <codecell>

osmdf = pd.DataFrame(osmdata)

# <headingcell level=3>

# Look at the whole Dataframe

# <codecell>

osmdf.tail(5)

# <headingcell level=2>

# Look at some Tags

# <codecell>

for tag in osmdf.highway.unique():
    print tag

# <codecell>

for tag in osmdf.maxspeed.unique():
    print tag

# <headingcell level=3>

# The interesting ones are

# <markdowncell>

# Nur ways behalten, die auch als `highway` gekennzeichnet sind und einen Namen haben.

# <codecell>

highwaydf = osmdf[['id', 'highway', 'lanes', 'name', 'maxspeed', 'nodes', 'ref']].dropna(subset=['name','highway'], how='any')
highwaydf.tail(5)

# <headingcell level=3>

# Clean a little bit up

# <markdowncell>

# Zu kleine Straßen raus werfen

# <codecell>

majorhighways = ['primary','secondary','secondary_link','tertiary','tertiary_link','living_street','residential']

highwaydf = highwaydf[highwaydf['highway'].isin(majorhighways)]

# <markdowncell>

# Replace `NaN` with word `unknown` and reset the index

# <codecell>

highwaydf = highwaydf.fillna(u'unknown').reset_index(drop=True)
highwaydf.tail(5)

# <headingcell level=2>

# Now get all Nodes

# <codecell>

nodes = []
for dct in osmdata:
    #print dct
    if dct['type']=='way':
        pass
    elif dct['type']=='node':
        nodes.append(dct)
    else:
        pass

# <codecell>

nodesdf = pd.DataFrame(nodes)

# <codecell>

nodesdf.tail(5)

# <headingcell level=2>

# Find all highways belonging to a node

# <markdowncell>

# Jeden Knoten durch gehen und schauen, ob er bei einer Straße genutzt wird. Wenn ja, die Straßen IDs zurück geben.
# 
# Dauert sehr sehr lang, wenn BoundingBox groß gewählt wurde!

# <codecell>

def gethighwayids(nodeid):
    highwayids = []
    for n, nodes in enumerate(highwaydf['nodes']):
        for nid in nodes: # alle nodes des highways
            if nid == int(nodeid):
                highwayids.append(highwaydf['id'][n])
    return highwayids

# <codecell>

nodesdf['highwayids'] = nodesdf['id'].apply(gethighwayids)

# <codecell>

nodesdf.tail(25)

# <headingcell level=2>

# Identify a Junction

# <markdowncell>

# Node with at least 3 different highways

# <codecell>

def idetifyjunction(highwayids):
    #print len(highwayids)
    if len(highwayids) < 2:
        return False
    else:
        return True

# <codecell>

nodesdf['junction'] = nodesdf['highwayids'].apply(idetifyjunction)

# <codecell>

nodesdf.head(25)

# <codecell>

junctionsdf = nodesdf[['id','lat','lon']][nodesdf['junction']==True]

# <headingcell level=2>

# Export to CSV

# <codecell>

junctionsdf.to_csv('junctions.csv', index=False)
print('done.')

# <markdowncell>

# ![junctions](junctions.png)

