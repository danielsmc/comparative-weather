import collections
import csv
import pygrib
import pyproj
import json
import urllib

grib_url = "http://weather.noaa.gov/pub/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/AR.conus/VP.001-003/ds.maxt.bin"
build_dir = "web/json/"

class Layer:
    def __init__(self,m):
        self.pj=pyproj.Proj(m.projparams)
        lat1 = m['latitudeOfFirstGridPointInDegrees']
        lon1 = m['longitudeOfFirstGridPointInDegrees']
        self.dx = m['DxInMetres']
        self.dy = m['DyInMetres']
        self.firstx, self.firsty = self.pj(lon1,lat1)
        self.values = m.values
        
    def ll_to_val(self,lat,lon):
        ourx, oury = self.pj(lon,lat)
        gridx = int((ourx-self.firstx)/self.dx)
        gridy = int((oury-self.firsty)/self.dy)
        bb = self.values.shape
        if gridx < 0 or gridx >= bb[1] or gridy < 0 or gridy >= bb[0]:
            return None
        return self.values[int(gridy),int(gridx)]

def k2f(k):
    return k*1.8-459.67

def to_list(vals):
    foo = []
    for i in xrange(vals.shape[0]):
        bar = []
        for j in xrange(vals.shape[1]):
            if vals[i,j]:
                bar.append(int(round(k2f(vals[i,j]))))
            else:
                bar.append(None)
        foo.append(bar)
    return foo

print "downloading grib"

fn, nobodycares = urllib.urlretrieve(grib_url)
g = pygrib.open(fn)
gm = g.message(1)
maxt = Layer(gm)

print "running through blocks"

temps = collections.defaultdict(int)
with open("blocks.csv") as fh:
    r = csv.DictReader(fh)
    for i,row in enumerate(r):
        if i%100000==0:
            print i
        tempk = maxt.ll_to_val(float(row['Y']),float(row['X']))
        if tempk:
            tempf = int(round(k2f(tempk)))
            temps[tempf] += int(row['POP2010'])

with open(build_dir + "histogram.json",'wb') as fh:
    json.dump({'tempbins':list(temps.iteritems())},fh)

print "dumping grid"
the_grid = to_list(gm.values)
projstr = " ".join(["+%s=%s"%kv for kv in gm.projparams.iteritems()])
with open(build_dir + "grid.json",'wb') as fh:
    json.dump({'values':the_grid,
               'proj':projstr,
               'firstLat':gm['latitudeOfFirstGridPointInDegrees'],
               'firstLon':gm['longitudeOfFirstGridPointInDegrees'],
               'dx':gm['DxInMetres'],'dy':gm['DyInMetres']},fh)
