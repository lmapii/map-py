// gen_tracks.js includes the list_gpx_tracks
// generated from the xls source-sheet

// check if a configuration is present
// if not, generate an empty one
try {
    track_cfg = track_cfg;
} catch (e) {
    track_cfg = {
          do_execute          : true
        , track_list          : []
        , hide_tracks         : true
        , display_gpx_data    : false
        , display_poly_data   : true
        , display_mono        : false
    };
}

var gpx_tracks = Array ();
var gpx_tracks_cnt = 0;

if (track_cfg.do_execute)
{
    for (var i = 0; i < list_gpx_tracks.length; i++)
    {
        // allow to exclude individual groups (static setting)
        if ((track_cfg.hide_tracks) && 
            (track_cfg.track_list.indexOf (list_gpx_tracks [i].group_label) != -1))
        {
            // console.log ("A to exclude: " + list_gpx_tracks [i].group_label);
            continue;
        } else if (!(track_cfg.hide_tracks) &&
            (track_cfg.track_list.indexOf (list_gpx_tracks [i].group_label) == -1)) 
        {
            // console.log ("B to exclude: " + list_gpx_tracks [i].group_label);
            continue;
        }
       

        if (track_cfg.display_gpx_data)
        {
            // gpx-files should be used directly to be displayed
            // on the map. so add them (notice: files are big)
            for (var j = 0; j < list_gpx_tracks [i].gpx_tracks.length; j++)
            {
                var cur_gpx_track = list_gpx_tracks [i].gpx_tracks [j];
                gpx_tracks [gpx_tracks_cnt] = omnivore.gpx (cur_gpx_track [0]);


                if (track_cfg.display_mono)
                {
                    gpx_tracks [gpx_tracks_cnt].c_color   = "red"
                    gpx_tracks [gpx_tracks_cnt].c_weight  = "4"
                    gpx_tracks [gpx_tracks_cnt].c_opacity = "0.66"
                } else
                {
                    gpx_tracks [gpx_tracks_cnt].c_color = cur_gpx_track [1];
                    gpx_tracks [gpx_tracks_cnt].c_weight = cur_gpx_track [2];
                    gpx_tracks [gpx_tracks_cnt].c_opacity = cur_gpx_track [3];
                }

                gpx_tracks [gpx_tracks_cnt].c_dashArray = cur_gpx_track [4];
                gpx_tracks [gpx_tracks_cnt].on ('ready', function (event)
                {
                    // console.log ("woot");
                    event.target.setStyle ({
                          "color"     : event.target.c_color
                        , "weight"    : event.target.c_weight
                        , "opacity"   : event.target.c_opacity
                        , "dashArray" : event.target.c_dashArray});

                    event.target.addTo (map);
                });

                gpx_tracks_cnt += 1;
            } 
        }

        if (track_cfg.display_poly_data)
        {
            // use the polygon objects in the structure
            // and add them to the map (faster than .gpx)
            for (var j = 0; j < list_gpx_tracks [i].poly_tracks.length; j++)
            {
                var cur_poly_track = list_gpx_tracks [i].poly_tracks [j];

                if (track_cfg.display_mono)
                {
                    cur_poly_track.setStyle ({
                          "color"     : "red"
                        , "weight"    : "4"
                        , "opacity"   : "0.66"});
                }
                // just add it to the layer
                map.addLayer (cur_poly_track);
            } 


        }
    }
} // do_execute

// EOF