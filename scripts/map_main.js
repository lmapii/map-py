
// function to parse GET-data via javascript
function $_GET (name)
{
    name = name.replace (/[\[]/,"\\\[").replace (/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp (regexS);
    var results = regex.exec (window.location.href);
    if (results == null)
        return "";
    else
        return results [1];
}

// mapbox no longer works
// var map = L.mapbox.map('map', 'examples.map-9ijuk24y')

// open street maps (include tile-layer)
var map = L.map('map')

var attribution_string;
var tileLayer;

var maptiles = $_GET ('maptiles')
var viewport = $_GET ('viewport')
var viewzoom = $_GET ('zoom')

//
// process map tiles to use, can be either
// mapquest or HERE for now.
//
if ((maptiles == "HERE") || 
    (maptiles == "here"))
{
    attribution_string = 
        'Map &copy; 1987-2014 <a href="http://developer.here.com">HERE</a>'

    tileLayer = L.tileLayer (
          'http://{s}.{base}.maps.cit.api.here.com/maptile/2.1/maptile/{mapID}/terrain.day' + 
          '/{z}/{x}/{y}/256/png8?app_id={app_id}&app_code={app_code}'
        , {
              attribution: attribution_string
            , subdomains:   '1234'
            , mapID:        'newest'
            , app_id:       'OHUl6ttB6FJOnpeQB4D7'
            , app_code:     'r2LD8DWb3gwXCeKCVGwznQ'
            , base:         'aerial'
            //, minZoom: 0
            //, maxZoom: 20
    }).addTo (map);

} else // if ((maptiles == "mapquest") || \
       //    (maptiles == "MapQuest"))
{
    var attribution_string = 
        'Tiles Courtesy of <a href="http://www.mapquest.com/">MapQuest</a> &mdash;' +
        'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors,' + 
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'

    var tileLayer = L.tileLayer (
          'http://otile{s}.mqcdn.com/tiles/1.0.0/map/{z}/{x}/{y}.jpeg'
        , { attribution: attribution_string, subdomains: '1234' })
        .addTo (map)
} 



// default values
var view_coords = [-7.10611, -82.24609];
var view_zoom = 3;

//
// process viewport and zoom to use on load
//

if (viewport != "")
{
    var split_viewport = viewport.split(',');
    try {
        var lat = parseFloat (split_viewport [0]);
        var lon = parseFloat (split_viewport [1]);

        // both have to be valid numbers
        if (!isNaN (lat) && !isNaN (lon))
        {
            view_coords = [lat, lon];
        }
    } catch (e) {
        // nothing to do
    }
}

if (viewzoom != "")
{
    try {
        var val = parseInt (viewzoom);

        if ((val > 0) && (val < 20))
            view_zoom = val;
    } catch (e) {
        // nothing to do
    }
}

// console.log ("viewport="+ map.getCenter().lat + "," + map.getCenter().lng + "&zoom=" + map.getZoom()

// initial view-port
map.setView (view_coords, view_zoom);

// show scale
L.control.scale(maxWidth = 300).addTo(map);
