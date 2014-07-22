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
bbox = [13.521945,50.919085,13.976063,51.18772]

# Links unten
minLat = bbox[1]
minLon = bbox[0]

# Rechts oben
maxLat = bbox[3]
maxLon = bbox[2]

# <headingcell level=3>

# Construct the Overpass Query String

# <markdowncell>

# Request from [Overpass-Turbo](http://overpass-turbo.eu/)

# <codecell>

tags = ['primary','secondary','secondary_link','tertiary','tertiary_link','living_street','residential']
objects = ['way'] # like way, node, relation

compactOverpassQLstring = '[out:json][timeout:60];('
for tag in tags:
    for obj in objects:
        compactOverpassQLstring += '%s["highway"="%s"](%s,%s,%s,%s);' % (obj, tag, minLat, minLon, maxLat, maxLon)
compactOverpassQLstring += ');out body;>;out skel qt;'    

# <codecell>

osmrequest = {'data': compactOverpassQLstring}
osmurl = 'http://overpass-api.de/api/interpreter'

# Ask the API
osm = requests.get(osmurl, params=osmrequest)

# <headingcell level=3>

# Reformat the JSON to fit in a Pandas Dataframe

# <markdowncell>

# The JSON can't be directyl imported to a Pandas Dataframe:
# 
# Thanks to [unutbu from stackoverflow.com](http://stackoverflow.com/questions/24848416/expected-string-or-unicode-when-reading-json-with-pandas) for fiddling this out!

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

highwaydf = highwaydf[highwaydf['highway'].isin(tags)]

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

# <codecell>

def gethighwayids(nodeid):
    highwayids = []
    for n, nodes in enumerate(highwaydf['nodes']):
        for nid in nodes: # alle nodes des highways
            if nid == int(nodeid):
                highwayids.append(highwaydf['id'][n])
    return highwayids

# <markdowncell>

# Dauert sehr sehr lang, wenn BoundingBox groß gewählt wurde!

# <codecell>

nodesdf['highwayids'] = nodesdf['id'].apply(gethighwayids)

# <codecell>

nodesdf.head(10)

# <headingcell level=2>

# Identify a Junction

# <markdowncell>

# Node with at least 3 different highways

# <codecell>

def identifyjunction(highwayids):
    #print highwayids
    if len(highwayids) < 2:
        return False
    elif len(highwayids)==2:
        # Wenn beide Highways den gleichen Namen haben, ist es nur
        # ein Zwischenstück und keine Kreuzung
        name1=unicode(highwaydf[highwaydf['id']==highwayids[0]]['name'].values)
        name2=unicode(highwaydf[highwaydf['id']==highwayids[1]]['name'].values)
        if name1==name2:
            #print('%s=%s' % (name1, name2))
            return False
        else:
            return True
    else:
        return True

# <codecell>

nodesdf['junction'] = nodesdf['highwayids'].apply(identifyjunction)

# <codecell>

nodesdf.tail(10)

# <codecell>

junctionsdf = nodesdf[['id','lat','lon']][nodesdf['junction']==True]

# <headingcell level=2>

# Export to CSV

# <codecell>

junctionsdf.to_csv('junctions.csv', index=False)
print('done.')

