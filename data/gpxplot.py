# simple python script to parse .gpx files to
# poly-lines and/or reduce points (greatly reduces file-size)

# martin lampacher

import sys
import datetime
import getopt
import string
import copy
import os

from re      import sub
from math    import sqrt,sin,cos,asin,pi,ceil,pow
from os      import listdir
from os.path import basename

import logging

GPX10 = '{http://www.topografix.com/GPX/1/0}'
GPX11 = '{http://www.topografix.com/GPX/1/1}'



#
# simple class to parse the .gpx file to a polyline
# supported by leaflet. gpx parser stuff adapted from
# 
# (c) Sergey Astanin <s.astanin@gmail.com> 2008
#
class GPX_Parser (object) :

    def __init__ (
          self
        , gpx_file
        , skipcount = 0) :

        # call super-init to avoid problems ...
        super (GPX_Parser , self).__init__()

        if not gpx_file :
            raise NameError ('need gpx file ...') 

        self.file_gpx   = gpx_file
        self.skipcount    = skipcount

        if not os.path.exists (self.file_gpx) :
            raise NameError ('could not grab gpx-file "%s"...' % self.file_gpx) 

        return



    def distance (self, p1, p2) :
        # Earth volumetric radius
        R = 6371.0008 

        lat1,lon1 = [a * pi / 180.0 for a in p1]
        lat2,lon2 = [a * pi / 180.0 for a in p2]

        deltalat = lat2 - lat1
        deltalon = lon2 - lon1
        
        def haversin (theta):
            return sin (0.5 * theta) ** 2

        h = haversin (deltalat) + cos (lat1) * cos (lat2) * haversin (deltalon)
        dist = 2 * R * asin (sqrt (h))
        return dist



    def read_all_segments (
          self
        , trksegs
        , ns = GPX10
        , pttag = 'trkpt') :

        trk = []
        
        for seg in trksegs:
            s = []
            prev_ele, prev_time = 0.0, None
            trkpts = seg.findall (ns + pttag)

            for pt in trkpts :
                # i just use lat / lon
                lat = float (pt.attrib ['lat'])
                lon = float (pt.attrib ['lon'])
                s.append ([lat, lon, 0, 0])

            trk.append (s)
        return trk



    def reduce_points (
          self
        , trk
        , npoints = None) :

        skip = npoints + 1

        newtrk = []
        for seg in trk :
            if len (seg) > 0 :
                newseg = seg [ : -1 : skip] + [seg [-1]]
                newtrk.append (newseg)
        return newtrk



    def load_xml_library (self) :
        try:
            import xml.etree.ElementTree as ET
        except:
            # i need to go deeper
            try:
                import elementtree.ElementTree as ET
            except:
                # i need to go deeper
                try:
                    import cElementTree as ET
                except:
                    # i need to go deeper
                    try:
                        import lxml.etree as ET
                    except:
                        # time is now relative
                        print ('this script needs ElementTree (Python>=2.5)')
                        sys.exit (EXIT_EDEPENDENCY)
        return ET;



    def parse_gpx_data (
          self
        , gpxdata
        , npoints = 0):

        ET = self.load_xml_library ();

        def find_trksegs_or_route (etree, ns) :
            trksegs = etree.findall ('.//' + ns + 'trkseg')
            
            if trksegs :
                return trksegs, "trkpt"
            else : 
                # try to display route if track is missing
                rte = etree.findall ('.//' + ns + 'rte')
                return rte, "rtept"

        try :
            ET.register_namespace ('', GPX11.strip ('{}'))
            ET.register_namespace ('', GPX10.strip ('{}'))
            etree = ET.XML (gpxdata)

        except ET.ParseError as v :
            row, column = v.position
            print ("error on row %d, column %d:%d" % row, column, v)

        NS = GPX10
        trksegs, pttag = find_trksegs_or_route (etree, NS)
        if not trksegs : 
            # try GPX11 namespace otherwise
            NS = GPX11
            trksegs, pttag = find_trksegs_or_route (etree, GPX11)

        if not trksegs : 
            # try without any namespace
            NS = ""
            trksegs, pttag = find_trksegs_or_route (etree, "")

        trk = self.read_all_segments (
              trksegs
            , ns = NS
            , pttag = pttag)

        trk_reduced = self.reduce_points (
              trk
            , npoints = npoints)
        return (trk, trk_reduced)



    def read_gpx_trk (
          self
        , input_file_name
        , npoints) :

        gpx = open (input_file_name).read()
        # logging.debug ("length(gpx) from file = %d" % len(gpx))
        return self.parse_gpx_data (gpx, npoints)


    def parse (self) :

        return self.read_gpx_trk (
              input_file_name = self.file_gpx
            , npoints = int (self.skipcount))

# EOF
