// -*- coding: utf-8-unix -*-

function renderChart(data) {

}

(function() {

    fetch("helsinki.json")
        .then(response => response.json())
        .then(data => renderChart(data));

})();
