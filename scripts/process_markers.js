// gen_markers.js includes the list_markers
// generated from the xls source-sheet

// check if a configuration is present
// if not, generate an empty one
try {
    marker_cfg = marker_cfg;
} catch (e) {
    marker_cfg = {
          do_execute      : true
        , group_list      : []
        , hide_groups     : true
        // marker-groups
        , showCoverageOnHover         : true
        , spiderfyOnMaxZoom           : false
        , removeOutsideVisibleBounds  : true
        , disableClusteringAtZoom     : 12
        , maxClusterRadius            : 120
    };
}

if (marker_cfg.do_execute)
{
    for (var i = 0; i < list_markers.length; i++)
    {
        // create one marker-group per country
        var cur_group = list_markers [i];

        // allow to exclude individual groups (static setting)
        if ((marker_cfg.hide_groups) && 
            (marker_cfg.group_list.indexOf (list_markers [i].group_label) != -1))
        {
            continue;
        } else if (!(marker_cfg.hide_groups) &&
            (marker_cfg.group_list.indexOf (list_markers [i].group_label) == -1)) 
        {
            continue;
        }

        // custom marker-group - colors from xls sheet
        var cur_markergroup = new L.MarkerClusterGroup({
              // custom fields: icon- and text color. they
              // would be lost if not assigned to the object
              cluster_icon_color:cur_group.marker_color
            , cluster_text_color:cur_group.text_color
              // standard settings
            , showCoverageOnHover        : marker_cfg.showCoverageOnHover
            , spiderfyOnMaxZoom          : marker_cfg.spiderfyOnMaxZoom
            , removeOutsideVisibleBounds : marker_cfg.removeOutsideVisibleBounds
            , disableClusteringAtZoom    : marker_cfg.disableClusteringAtZoom
            , maxClusterRadius           : marker_cfg.maxClusterRadius
              // modified icon-create function with two additional parameters
            , iconCreateFunction : function (cluster, cluster_icon_color, cluster_text_color) {
                var group_html = 
                    '<div class="c_div_outer" style="background-color:' + 
                        cluster_icon_color + '" ></div>' + 
                    '<div class="c_div_inner" style="background-color:' + 
                        cluster_icon_color + '" ></div>' + 
                    '<div class="c_div_text"  style="color:' + 
                        cluster_text_color + '">' + cluster.getChildCount() + "</div>"
                return L.divIcon({ html: group_html, 
                    className: 'cluster_icon', iconSize: L.point(40, 40) });
            }
        });

        // iterate through all markers of the country
        for (var j = 0; j < cur_group.markers.length; j++)
        {
            var cur_marker = cur_group.markers [j]

            // we have specific icons for each marker, all
            // defined within the .xls sheet - create it !
            var the_icon = L.MakiMarkers.icon ({
                  icon    : cur_marker [1]
                , color   : cur_marker [2]
                , size    : cur_marker [3]
            });

            // the marker itself ...
            var the_marker = new L.Marker (
                  new L.LatLng (cur_marker [0][0], cur_marker [0][1])
                , { icon : the_icon, opacity : cur_marker [6] }
            );

            // the opacity is overwritten, so i have to add it to the
            // marker element and use it in the markercluster.js 
            the_marker.c_opacity = cur_marker [6]

            // create a pop-up for markers with a title
            // and a description (only title if no description)
            if (cur_marker [4] != "")
            {
                var marker_string = "<strong>" + cur_marker [4] + "</strong>"
                if (cur_marker [5] != "")
                {
                    marker_string = marker_string.concat (
                        "<br /><div>" + cur_marker [5] + "</div>");
                }
                the_marker.bindPopup (marker_string);
            }
            // add it to the group of markers of the current country
            cur_markergroup.addLayer (the_marker);
        }
        // aaand don't forget to add the markers to the map !
        map.addLayer (cur_markergroup);
    }
} // do_execute

// EOF