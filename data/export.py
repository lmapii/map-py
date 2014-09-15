import logging 
import argparse
import os.path
import time

import cgi
import xlrd

from xlutils.view import View
from itertools    import islice

from gpxplot import GPX_Parser

# identifiers of the sheets in the .xls file
SHEET_CFG    = 'export_cfg'
# where to put the generated .js files
SCRIPTS_PATH = "../scripts/"

# header content of the gpx-files
GPX_HEADER = '\
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n\
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1"\n\
    creator="tr15a" \n\
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n\
    xmlns:dklgpx="http://na.na.na/GPX/1/1"\n\
    xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">\n\
    <metadata>\n\
        <name>tr15a - generated GPX file</name>\n\
    </metadata>\n'

# footer (closing tag) for gpx-files
GPX_FOOTER = '\
</gpx>'


#
# simple class to parse the .xls file containing 
# the map data - uses the xlutils library
#
class XLS_Parser (object) :

    def __init__ (self, file_name) :
        # call super-init to avoid problems ...
        super (XLS_Parser , self).__init__()

        # try to grab the xls-data already upon initialization
        # we can't do anything without it so ...
        self.xls_data = None
        self.markers = None
        self.tracks  = None

        self.cfg = {
              'JS_marks'     : None
            , 'JS_tracks'    : None
            , 'GPX_src'      : None
            , 'GPX_tgt_trk'  : None
            , 'GPX_tgt_wp'   : None
            , 'sheet_marks'  : None
            , 'sheet_tracks' : None
        }

        self.datetime = time.strftime("%Y-%m-%d %H:%M:%S")

        try :
            # retrieve xls sheet data
            self.xls_data = xlrd.open_workbook (file_name)
        except Exception, e:
            raise NameError ('could not grab xls-file "%s"...' % file_name) 

        self.read_cfg_from_xls (self.xls_data.sheet_by_name (SHEET_CFG))

        if not self.check_cfg () :
            raise Exception ('xls-file, tab "%s" does not contain a valid configuration...' % SHEET_CFG) 

        return



    #
    # retrieve export configuration from .xls sheet, contains worksheets,
    # paths and filenames which should be used.
    #
    def read_cfg_from_xls (self, ws_cfg) :

        # skip the first row, it is only a header
        for cur_row in range (1, ws_cfg.nrows) :
            # get the info from the current item
            # listed as key-value pairs in the spreadsheet
            cur_cfg = {
                  'key'   : ws_cfg.cell_value (cur_row,  0)
                , 'value' : ws_cfg.cell_value (cur_row,  1)
            }

            # try to match it with a required configuration
            for cur_key in self.cfg :
                if cur_key == cur_cfg ['key'] :
                    self.cfg [cur_key] = cur_cfg ['value']
        pass 



    #
    # check that all the necessary data
    # is contained in the configuration (not 'None')
    #

    def check_cfg (self) :
        # could be extended to check paths ..
        for cur_key in self.cfg :
            if self.cfg [cur_key] is None :
                return False

        return True

        
    def execute (self) :

        self.get_markers_from_xls (self.xls_data.sheet_by_name (self.cfg ['sheet_marks']))
        self.process_markers_for_device ()
        self.process_markers_for_map ()

        self.get_tracks_from_xls (self.xls_data.sheet_by_name (self.cfg ['sheet_tracks']))
        self.get_segments_from_gpx_tracks ()
        self.process_tracks_for_map ()
        self.process_tracks_for_device ()
        
        return



    #
    # retrieves all markers from the worksheet ws_markers
    # grouped by "marker-group"
    #

    def get_markers_from_xls (self, ws_markers) :

        # delete current markers
        self.markers = {}

        # skip the first row, it is only a header
        for cur_row in range (1, ws_markers.nrows) :

            # retrieve all the info from the xls sheet
            # separate marker and marker group as they will be joined
            # in a structure (organized by marker-groups)

            cur_marker = {
                  'enabled' : ws_markers.cell_value (cur_row,  0)
                , 'coords'  : ws_markers.cell_value (cur_row,  4)
                , 'icon'    : ws_markers.cell_value (cur_row,  5)
                , 'color'   : ws_markers.cell_value (cur_row,  6)
                , 'opacity' : ws_markers.cell_value (cur_row,  7)
                , 'size'    : ws_markers.cell_value (cur_row,  8)
                , 'title'   : ws_markers.cell_value (cur_row,  9)
                , 'comment' : ws_markers.cell_value (cur_row, 10)
            }

            cur_group = {
                  'group-label'  : ws_markers.cell_value (cur_row, 1) # .lower ()
                , 'marker-color' : ws_markers.cell_value (cur_row, 2)
                , 'text-color'   : ws_markers.cell_value (cur_row, 3)
                , 'markers'      : []
            }
            
            # enabled markers contain some value (e.g. 'x')
            if cur_marker ['enabled'] == "" :
                continue

            # create groups on-the-fly, so check if it already
            # exists. if not, create the group with the required colors
            if cur_group ['group-label'] not in self.markers :
                # create a new group in the list of marks
                self.markers.update ({
                    cur_group ['group-label'] : cur_group})

            # add the marker to the corresponding group in the list
            self.markers [cur_group ['group-label']] ['markers'].append (cur_marker)

        return



    #
    # creates the data-structure which can be accessed via java-script
    # to display all markers on the html-map
    #

    def process_markers_for_map (self) :

        if self.markers is None :
            raise Exception ("cannot process markers, no markers retrieved ...")
            return

        file_markers = open (
              SCRIPTS_PATH + self.cfg ['JS_marks']
            , mode = "w")

        file_markers.write (
            "//\n" + 
            "// generated file - do not modify\n" + 
            "// creation date: %s\n" % (self.datetime) +  
            "//\n\n" );
        file_markers.write (
            "var list_markers = [\n");

        current_group  = "XXX"
        changed_group  = False
        is_first_group = True

        for cur_group_str in self.markers :
            
            cur_group = self.markers [cur_group_str]
            # we want marker-groups for each country
            if cur_group ['group-label'] != current_group :

                if is_first_group :
                    # this is the very first row and thus group
                    file_markers.write ("    {\n");
                    is_first_group = False
                else :
                    # already had a group, close first one
                    file_markers.write ("    },\n");
                    file_markers.write ("    {\n");
                
                group_str = \
                    "          group_label  : \"%s\"\n" % (cur_group ['group-label']) + \
                    "        , marker_color : \"%s\"\n" % (cur_group ['marker-color']) + \
                    "        , text_color   : \"%s\"\n" % (cur_group ['text-color']) + \
                    "        , markers      : \n" + \
                    "        [\n"

                file_markers.write (group_str.encode('utf-8'))

                current_group = cur_group ['group-label']
                changed_group = True

            for cur_marker in cur_group ['markers'] :

                # add items to the current group of markers
                add_str = "            ,"
                if changed_group :
                    add_str = "             "
                    changed_group = False

                marker_string = add_str + \
                    " [ " + \
                    "  [ %s ]"  % (cur_marker ['coords']) + \
                    ", \"%s\" " % (cur_marker ['icon']) + \
                    ", \"%s\" " % (cur_marker ['color']) + \
                    ", \"%s\" " % (cur_marker ['size']) + \
                    ", \"%s\" " % (cur_marker ['title']) + \
                    ", \"%s\" " % (cur_marker ['comment']) + \
                    ", \"%s\" " % (cur_marker ['opacity']) + \
                    " ]\n"

                file_markers.write (marker_string.encode('utf-8'))

            # all markers added, add closing bracket for marker-list
            file_markers.write (
                "        ]\n")

        if self.markers.__len__ () > 0 :
            file_markers.write (
                "    }\n" + 
                "];\n\n"  + 
                "// EOF \n");
        else :
            file_markers.write (
                "];\n\n"  + 
                "// EOF \n");
        file_markers.close ()
        return



    #
    # creates the .gpx files to upload onto the GPS device
    # for all waypoints in the xls-sheet
    #

    def process_markers_for_device (self) :

        if self.markers is None :
            raise Exception ("cannot process waypoints, no markers retrieved ...")
            return

        # generate markers in .gpx format for GPS device
        # one file for each group

        cur_gpx_file   = None

        current_group  = "XXX"
        changed_group  = False

        for cur_group_str in self.markers :
            
            cur_group = self.markers [cur_group_str]

            # we create a wp_file for each group
            if cur_group ['group-label'] != current_group :
                current_group = cur_group ['group-label']
                changed_group = True

            for cur_marker in cur_group ['markers'] :

                if changed_group :
                    changed_group = False

                    # closing the "None" will fail for the first
                    # time so this is just a dirty workaround
                    try:
                        cur_gpx_file.write (GPX_FOOTER);
                        cur_gpx_file.close ()
                    except Exception, e:
                        pass

                    # grouped by countries, create new gpx file
                    cur_gpx_filename = \
                        "../" + self.cfg ['GPX_tgt_wp'] + "/" + \
                        "wp_" + current_group + ".gpx"

                    cur_gpx_file = open (
                          cur_gpx_filename
                        , mode = "w")

                    cur_gpx_file.write (GPX_HEADER);
                    print "processing " + cur_gpx_filename + " ..."

                # get the coordinates (single item in xls sheet)
                lat = (cur_marker['coords'].split(',') [0]).replace (" ", "")
                lon = (cur_marker['coords'].split(',') [1]).replace (" ", "")

                # get rid of extra tags (from html map)
                gpx_name    = cgi.escape(cur_marker ['title'])
                gpx_comment = cgi.escape(cur_marker ['comment'])

                # select custom icons if available, sadly garmin only
                # supports r/g/b flags. all other icons will be a red circle
                if ((cur_group ['marker-color'].lower () == "green") or \
                    (cur_group ['marker-color'].lower () == "red")   or \
                    (cur_group ['marker-color'].lower () == "blue")) :
                    gpx_icon = "Flag, " + cur_group ['marker-color']
                else :
                    gpx_icon = "Circle, Red"

                # create waypoint; garmin montana uses the "cmt" tag as note to 
                # display. just add both (description + comment) to make it work
                # watch out ! cmt -> desc order is important for base-camp ...
                # else it will try to tell you that this is an invalid gpx file ...
                gpx_string = \
                    "    <wpt lat='" + lat + "' lon='" + lon + "'>\n" + \
                    "        <name>" + gpx_name + "</name>\n" + \
                    "        <cmt>"  + gpx_comment + "</cmt>\n" + \
                    "        <desc>" + gpx_comment + "</desc>\n" + \
                    "        <sym>"  + gpx_icon + "</sym>\n" + \
                    "    </wpt>\n"

                cur_gpx_file.write (gpx_string.encode('utf-8'))

            cur_gpx_file.write (GPX_FOOTER)
            cur_gpx_file.close ()

        return


    #
    # retrieves all gpx-tracks from the worksheet ws_tracks
    # grouped by "track-group"
    #

    def get_tracks_from_xls (self, ws_tracks) :

        # delete current markers
        self.tracks = {}

        # skip the first row, it is only a header
        for cur_row in range (1, ws_tracks.nrows) :

            gpx_file_path = \
                "../" + self.cfg ['GPX_src'] + "/" + \
                ws_tracks.cell_value (cur_row, 1)

            cur_track = {
                  'enabled'    : ws_tracks.cell_value (cur_row, 0)
                , 'gpx-file'   : gpx_file_path
                , 'color'      : ws_tracks.cell_value (cur_row, 3)
                , 'weight'     : ws_tracks.cell_value (cur_row, 4)
                , 'opacity'    : ws_tracks.cell_value (cur_row, 5)
                , 'dasharray'  : ws_tracks.cell_value (cur_row, 6)
                , 'skipcount'  : ws_tracks.cell_value (cur_row, 7)
                , 'trk-full'   : None
                , 'trk-skip'   : None
            }

            cur_group = {
                  'group-label'  : ws_tracks.cell_value (cur_row, 2) # .lower ()
                , 'tracks'       : []
            }
            
            # enabled tracks contain some value (e.g. 'x')
            if cur_track ['enabled'] == "" :
                continue

            # create groups on-the-fly, so check if it already
            # exists. if not, create the group
            if cur_group ['group-label'] not in self.tracks :
                # create a new group in the list of marks
                self.tracks.update ({
                    cur_group ['group-label'] : cur_group})

            # add the marker to the corresponding group in the list
            self.tracks [cur_group ['group-label']] ['tracks'].append (cur_track)

        return



    #
    # retrieves all the track-segments from the gpx-files
    # which may then be used to create a polygon
    #

    def get_segments_from_gpx_tracks (self) :

        if self.tracks is None :
            raise Exception ("cannot process gpx-tracks, no tracks in list...")
            return

        for cur_group_str in self.tracks :
            cur_group = self.tracks [cur_group_str]

            for cur_track in cur_group ['tracks'] :
                print ("processing %s ... " % cur_track ['gpx-file'])

                gpx_parser = GPX_Parser (
                      gpx_file  = cur_track ['gpx-file']
                    , skipcount = cur_track ['skipcount'])
                (trk, trk_reduced) = gpx_parser.parse ()

                cur_track ['trk-full'] = trk
                cur_track ['trk-skip'] = trk_reduced

        return



    def get_poly_for_track (self, the_track, indent_str) :

        first_entry = True
        first_seg   = True
        i = 0
        poly_str = ""

        for seg in the_track ['trk-skip'] :
            if len (seg) == 0:
                continue

            if first_seg :
                poly_str += "new L.Polyline ([";
                first_seg = False
            else :
                poly_str += "\n" + indent_str + ", new L.Polyline ([";
                first_entry = True

            for p in seg:
                coord_str = "[%s, %s]" %(p[0], p[1])

                if first_entry :
                    poly_str += " " + coord_str.encode('utf-8')
                    first_entry = False
                else :
                    poly_str += ", " + coord_str.encode('utf-8')
            
            style_str = " {" + \
                "   color : \"%s\""  % (the_track ['color']) + \
                " , weight : \"%s\""  % (the_track ['weight']) + \
                " , opacity : \"%s\""  % (the_track ['opacity']) + \
                " , dashArray : \"%s\""  % (the_track ['dasharray']) + \
                " }"

            poly_str += "], %s)" % style_str;

            # no longer statically added to map, can now be
            # customized via GET variables

            # out_file.write (
            #     "], %s).addTo(map);\n\n" % style_str);

            i += 1

        return poly_str



    #
    # creates the java-script data-structure for all gpx files
    #

    def process_tracks_for_map (self) :

        if self.tracks is None :
            raise Exception ("cannot create track list, no tracks in list...")
            return

        file_tracks = open (
              SCRIPTS_PATH + self.cfg ['JS_tracks']
            , "w")
        file_tracks.write (
            "//\n" + 
            "// generated file - do not modify\n" + 
            "// creation date: %s\n" % (self.datetime) +  
            "//\n\n" );
        file_tracks.write (
            "var list_gpx_tracks = [\n");

        current_group  = "XXX"
        changed_group  = False
        is_first_group = True

        for cur_group_str in self.tracks :
            
            cur_group = self.tracks [cur_group_str]
            # create track-groups
            if cur_group ['group-label'] != current_group :

                if is_first_group :
                    # this is the very first row and thus group
                    file_tracks.write ("    {\n");
                    is_first_group = False
                else :
                    # already had a group, close first one
                    file_tracks.write ("    },\n");
                    file_tracks.write ("    {\n");
                
                group_str = \
                    "          group_label : \"%s\"\n" % (cur_group ['group-label']) + \
                    "        , gpx_tracks  : \n" + \
                    "        [\n"

                file_tracks.write (group_str.encode('utf-8'))

                current_group = cur_group ['group-label']
                changed_group = True

            # create track-list
            for cur_track in cur_group ['tracks'] :

                add_str = "            ,"
                if changed_group :
                    add_str = "             "
                    changed_group = False

                file_new_path = os.path.splitext (cur_track ['gpx-file']) [0]
                file_new_path = file_new_path.replace (
                    "../", "./")
                file_new_path += ".gpx"

                track_string = add_str + \
                    " [ " + \
                    "  \"%s\""  % (file_new_path) + \
                    ", \"%s\""  % (cur_track ['color']) + \
                    ", %s"      % (cur_track ['weight']) + \
                    ", %s"      % (cur_track ['opacity']) + \
                    ", \"%s\""  % (cur_track ['dasharray']) + \
                    " ]\n"

                file_tracks.write (track_string.encode('utf-8'))

            # all tracks added, add closing bracket
            file_tracks.write (
                "        ]\n")

            # same story again for polygons
            file_tracks.write (
                "        , poly_tracks  : \n" + \
                "        [\n")
            changed_group = True
            for cur_track in cur_group ['tracks'] :

                # file also contains all polygons - need to be processed first
                if cur_track ['trk-skip'] is None :
                    raise Exception ("cannot create polygon, call get_segments_from_gpx_tracks...")
                    return

                add_str = "            ,"
                
                if changed_group :
                    add_str = "             "
                    changed_group = False

                track_string = add_str + \
                    " %s\n" % self.get_poly_for_track (
                          the_track = cur_track
                        , indent_str = "            ")

                file_tracks.write (track_string.encode('utf-8'))

            # all added, add closing bracket
            file_tracks.write (
                "        ]\n")

        file_tracks.write (
            "    }\n" + 
            "];\n\n"  + 
            "// EOF \n");
        file_tracks.close ()
        return



    def get_trk_str_for_track (self, the_track, trk_name) :

        gpx_string = \
            "<trk>\n" + \
            "    <name>" + trk_name + "</name>\n" + \
            "    <trkseg>\n"

        for seg in the_track ['trk-skip'] :
            if len (seg) == 0:
                continue

            for p in seg:
                lat = "%s" % p [0]
                lon = "%s" % p [1]

                gpx_string += \
                    "<trkpt lat='" + lat + "' lon='" + lon + "'>" + \
                    "</trkpt>\n"

        # terminate trak
        gpx_string += \
            "    </trkseg>\n" + \
            "</trk>\n"

        return gpx_string



    #
    # creates the java-script data-structure for all gpx files
    #

    def process_tracks_for_device (self) :

        if self.tracks is None :
            raise Exception ("cannot create track list, no tracks in list...")
            return

        for cur_group_str in self.tracks :
            cur_group = self.tracks [cur_group_str]

            # create track-list
            for cur_track in cur_group ['tracks'] :

                # create track-file to generate from route of gpx file
                file_no_ext = os.path.splitext (cur_track ['gpx-file']) [0]
                file_no_ext = file_no_ext.replace (
                    "../" + self.cfg ['GPX_src'] + "/", "")

                # place file in different folder than gpx / data files
                cur_gpx_filename = \
                    "../" + self.cfg ['GPX_tgt_trk'] + \
                    "/trk_" + file_no_ext + ".gpx"

                cur_gpx_file = open (
                      cur_gpx_filename
                    , mode = "w")

                # write the gpx header, parser will add track / segments
                cur_gpx_file.write (GPX_HEADER)
                # cur_gpx_file.close ()

                cur_gpx_file.write (self.get_trk_str_for_track (
                      the_track = cur_track
                    , trk_name = file_no_ext).encode('utf-8'))

                cur_gpx_file.write (GPX_FOOTER)
                cur_gpx_file.close ()

        return



#
# checks that a file exists, used for FILE cmd-line arguments
#
def is_file (parser, x):
    if not os.path.exists (x) :
        parser.error ("the file '%s' does not exist!" % x)
    return x



#
# main function
#
def execute () :
    # custom argument parser for command line argumets
    parser = argparse.ArgumentParser()

    # add required argument : the input .xls file 
    parser.add_argument (
          "-i", "--input"
        , dest     = "xls_file"
        , required = True
        , help     = "input .xls sheet containing the map data"
        , metavar  = "FILE"
        , type     = lambda x: is_file (parser,x))

    cmd_args = parser.parse_args ()

    # build stuff
    xls_parser = XLS_Parser (file_name = cmd_args.xls_file)
    xls_parser.execute ()
    pass


if __name__ == "__main__":
    execute ()

# EOF
