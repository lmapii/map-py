
// just a simple function, i know there's other
// stuff out there but i don't really need more
function parseBoolean (name)
{
    if ((name != "true") &&
        (name != "True") &&
        (name != "TRUE") &&
        (name != "YES") &&
        (name != "yes") &&
        (name != "Yes"))
    {
        return false;
    } else
    {
        return true;
    }
}

// change configuration basing on GET paramters
if ($_GET ('show_tracks') != "")
    track_cfg.do_execute = parseBoolean ($_GET ('show_tracks'));

if ($_GET ('show_gpx') != "")
    track_cfg.display_gpx_data = parseBoolean ($_GET ('show_gpx'));

if ($_GET ('show_poly') != "")
    track_cfg.display_poly_data = parseBoolean ($_GET ('show_poly'));

if ($_GET ('tracks_mono') != "")
    track_cfg.display_mono = parseBoolean ($_GET ('tracks_mono'));

if ($_GET ('show_markers') != "")
    marker_cfg.do_execute = parseBoolean ($_GET ('show_markers'));

if ($_GET ('hide_track_list') != "")
    track_cfg.hide_tracks = parseBoolean ($_GET ('hide_track_list'));

if ($_GET ('hide_marker_list') != "")
    marker_cfg.hide_groups = parseBoolean ($_GET ('hide_marker_list'));

if ($_GET ('track_list') != "")
{
    var split_tracks = $_GET ('track_list').split(',');
    track_cfg.track_list = [];
    for (var i = 0; i < split_tracks.length; i++)
    {
        track_cfg.track_list.push (split_tracks [i]);
    }
}

if ($_GET ('marker_list') != "")
{
    var split_marks = $_GET ('marker_list').split(',');
    marker_cfg.group_list = [];
    for (var i = 0; i < split_marks.length; i++)
    {
        marker_cfg.group_list.push (split_marks [i]);
    }
}
