URL_BASE = '/api/v1/snowplow/'

map = null
plows = {}

plow_icon = L.icon(
    iconUrl: 'img/bulldozer-helblue.png'
    iconSize: [32, 37]
    iconAnchor: [16, 35]
    popupAnchor: [0, -37]
)
moment.lang('fi')

add_plow = (plow) ->
    loc = plow.last_loc
    marker = L.marker([loc.coords[1], loc.coords[0]],
        icon: plow_icon
    )
    marker.addTo(map)
    marker.plow = plow
    plow.marker = marker
    marker.on('click', (e) ->
        plow = e.target.plow
        if plow.trail
            map.removeLayer(plow.trail)
            plow.trail = null
        else
            show_plow_trail(e.target.plow)
    )
    plows[plow.id] = plow

refresh_plows = ->
    console.log "refresh"
    url = URL_BASE + '?callback=?'
    $.getJSON(url, (data) ->
        console.log "got data for #{ data.length } plows"
        for plow_info in data
            if plow_info.id not of plows
                plow = add_plow(plow_info)
            plow = plows[plow_info.id]

            marker = plow.marker
            if plow.last_loc.timestamp != plow_info.last_loc.timestamp
                old_ll = marker.getLatLng()
                coords = plow_info.last_loc.coords
                new_ll = new L.LatLng(coords[1], coords[0])
                console.log "plow #{plow.id} moved " + new_ll.distanceTo(old_ll)
                marker.setLatLng(new_ll)
                plow.last_loc = plow_info.last_loc

            ts = moment(plow.last_loc.timestamp).calendar()
            marker.unbindPopup()
            marker.bindPopup("<b>#{ plow.id }</b><br />Sijainti päivitetty #{ ts }")
    )

show_plow_trail = (plow) ->
    url = URL_BASE + plow.id + '?history=500&callback=?'
    $.getJSON(url, (data) ->
        console.log "history for " + plow.id
        # First remove all other trails
        for plow_id of plows
            p = plows[plow_id]
            if not p.trail
                continue
            map.removeLayer(p.trail)
            p.trail = null

        line = []
        lines = [line]
        last_latlng = null
        for pnt in data.history
            latlng = new L.LatLng(pnt.coords[1], pnt.coords[0])
            # Do not a consequtive line for samples that jump too much
            if last_latlng and latlng.distanceTo(last_latlng) > 200
                line = [latlng]
                lines.push(line)
            else
                line.push(latlng)
            last_latlng = latlng

        line = L.multiPolyline(lines)
        line.addTo(map)
        plow.trail = line
    )

jQuery ->
    map = L.map('map').setView([60.184167, 24.949167], 11)
    L.tileLayer('http://{s}.tile.cloudmade.com/BC9A493B41014CAABB98F0471D759707/997/256/{z}/{x}/{y}.png',
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>'
    ).addTo(map)
    refresh_plows()
    setInterval(refresh_plows, 10000)
