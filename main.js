// -*- coding: utf-8-unix -*-

// Lower limits of "abundant" level as per norkko.fi (grains/m3)
// https://norkko.fi/usein-kysytyt-kysymykset/
const YMAX_DEFAULT_LEVELS = {
    alder:   100,
    birch:   100,
    grass:    30,
    mugwort:  30,
    ragweed:  30,
};

function formatDate(string) {
    const date = new Date(string);
    const weekday = ["su", "ma", "ti", "ke", "to", "pe", "la"][date.getDay()];
    return `${weekday} ${date.getDate()}.${date.getMonth()+1}.${date.getFullYear()}`;
}

function renderRow(data, key, label) {
    const chart = document.getElementById("chart");
    const last = data[data.length-1];

    // Label
    var div = document.createElement("div");
    div.classList.add("align-left");
    div.innerHTML = label.substring(0, 3);
    tippy(div, {content: label, placement: "right"});
    chart.appendChild(div);

    // Bar
    // Render the Y-axis maximum at YMAX_DEFAULT_LEVELS
    // or maximum seen in the data, whichever is greater.
    var div = document.createElement("div");
    div.classList.add("bars");
    div.style.gridTemplateColumns = `repeat(${data.length}, 1fr)`;
    var ref = data.reduce((ymax, y) => Math.max(ymax, y[key]), 0);
    ref = Math.max(YMAX_DEFAULT_LEVELS[key], ref);
    for (var item of data) {
        var bar = document.createElement("div");
        bar.classList.add("bar");
        bar.classList.add(item.partition);
        // Need to use px so that span positioning below works.
        // Note the height defined also in style.css for #chart.
        var height = 48 * item[key] / ref;
        bar.style.height = `${height}px`;
        if (item.partition === "today") {
            var span = document.createElement("span");
            span.style.position = "relative";
            span.style.top = `${height-3}px`;
            span.innerHTML = "↑";
            bar.appendChild(span);
        }
        var text = `${formatDate(item.date)} · ${item[key].toFixed(0)} h/m³`;
        tippy(bar, {content: text, placement: "bottom"});
        div.appendChild(bar);
    }
    chart.appendChild(div);

    // Percent change
    // Compare the latest date against mean of the previous seven.
    // Avoid showing huge percentages given tiny denominators.
    var div = document.createElement("div");
    div.classList.add("align-right");
    var prev = data.filter(x => x.partition === "past").slice(-7);
    var ref = prev.reduce((total, x) => total + x[key], 0) / prev.length;
    if (ref >= YMAX_DEFAULT_LEVELS[key] / 10) {
        var value = (last[key] - ref) / ref;
        value = Math.max(-9.99, Math.min(9.99, value));
        sign = value === 0 ? "" : (value < 0 ? "–" : "+");
        div.innerHTML = `${sign}${Math.abs(100*value).toFixed(0)}%`;
    } else {
        div.innerHTML = `⋯`;
    }
    chart.appendChild(div);

    // Value (grains/m3)
    var div = document.createElement("div");
    div.classList.add("align-right");
    var value = Number(last[key].toPrecision(2));
    div.innerHTML = `${value.toFixed(0)}`;
    chart.appendChild(div);

}

function renderChart(data) {
    // Make sure we have at most the expected amount of data.
    data = (data.filter(x => x.partition === "past").slice(-7)
            .concat(data.filter(x => x.partition === "today")
                    .concat(data.filter(x => x.partition === "future").slice(0, 3))));

    const p = document.getElementById("intro");
    const date = data[data.length-1].date;
    intro.innerHTML = `Tilanne ${formatDate(date)}`;
    // In chronological order of appearance
    // https://www.siitepolytieto.fi/mika-allergia/siitepolykausi
    renderRow(data, "alder", "Leppä");
    renderRow(data, "birch", "Koivu");
    renderRow(data, "grass", "Heinä");
    renderRow(data, "mugwort", "Pujo");
    renderRow(data, "ragweed", "Tuoksukki");
}

(function() {
    fetch("helsinki.json")
        .then(response => response.json())
        .then(data => renderChart(data));
})();
