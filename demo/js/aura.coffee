URL_BASE = 'http://localhost:5000/api/v1/snowplow/'

jQuery ->
    map = L.map('map').setView([60.184167, 24.949167], 11)
    L.tileLayer('http://{s}.tile.cloudmade.com/BC9A493B41014CAABB98F0471D759707/997/256/{z}/{x}/{y}.png',
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>'
    ).addTo(map)
    url = URL_BASE + '?callback=?'
    plow_icon = L.icon(
        iconUrl: 'img/bulldozer-helblue.png'
        iconSize: [32, 37]
        iconAnchor: [16, 35]
        popupAnchor: [0, -37]
    )
    moment.lang('fi')
    refresh_plows = ->
      console.log "refr"

    show_plow_trail = (plow) ->
        url = URL_BASE + plow.id + '?history=500&callback=?'
        $.getJSON(url, (data) ->
            console.log "history for " + plow.id
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

            line = L.multiPolyline(lines).addTo(map)
        )
    $.getJSON(url, (data) ->
        console.log "got data for #{ data.length } plows"
        for plow in data
            loc = plow.last_loc
            marker = L.marker([loc.coords[1], loc.coords[0]],
                icon: plow_icon
            )
            ts = moment(loc.timestamp).calendar()
            marker.bindPopup("<b>#{ plow.id }</b><br />Sijainti päivitetty #{ ts }")
            marker.addTo(map)
            marker.plow = plow
            marker.on('click', (e) ->
                show_plow_trail(e.target.plow)
            )
    )
