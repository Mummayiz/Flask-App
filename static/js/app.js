function mountThemeToggle() {
  const body = document.body;
  const toggle = document.querySelector("[data-theme-toggle]");
  const savedTheme = localStorage.getItem("pulseboard-theme") || "light";
  body.dataset.theme = savedTheme;
  if (!toggle) return;

  toggle.addEventListener("click", () => {
    const nextTheme = body.dataset.theme === "dark" ? "light" : "dark";
    body.dataset.theme = nextTheme;
    localStorage.setItem("pulseboard-theme", nextTheme);
  });
}

function buildHeatmap(node, data) {
  const cells = (data || [])
    .map((item) => `<div class="heat-cell heat-${item.level}" title="${item.date}: ${item.value}"></div>`)
    .join("");
  node.innerHTML = cells || "<p class='muted-empty'>No heatmap data yet.</p>";
}

function chartConfig(kind, labels, values) {
  const palette = [
    "rgba(68, 138, 255, 0.84)",
    "rgba(37, 198, 218, 0.84)",
    "rgba(102, 187, 106, 0.84)",
    "rgba(255, 202, 40, 0.84)",
    "rgba(255, 112, 67, 0.84)",
    "rgba(171, 71, 188, 0.84)",
    "rgba(126, 87, 194, 0.84)",
    "rgba(38, 166, 154, 0.84)",
  ];
  if (kind === "line") {
    return {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Value",
          data: values,
          borderColor: "rgba(68, 138, 255, 1)",
          backgroundColor: "rgba(68, 138, 255, 0.18)",
          borderWidth: 3,
          fill: true,
          tension: 0.35,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
      },
    };
  }
  return {
    type: kind,
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: labels.map((_, index) => palette[index % palette.length]),
        borderWidth: 0,
        borderRadius: kind === "bar" ? 12 : 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: kind !== "bar" } },
      scales: kind === "bar" ? { y: { beginAtZero: true } } : {},
    },
  };
}

function mountCharts() {
  document.querySelectorAll(".chart-canvas").forEach((node) => {
    const payload = JSON.parse(node.dataset.chart || "{}");
    const key = node.dataset.key;
    const chartData = payload[key] || {};
    let labels = [];
    let values = [];

    if (Array.isArray(chartData.labels) && Array.isArray(chartData.values)) {
      labels = chartData.labels;
      values = chartData.values;
    } else {
      labels = Object.keys(chartData);
      values = Object.values(chartData);
    }

    if (!labels.length || typeof Chart === "undefined") return;
    new Chart(node, chartConfig(node.dataset.chartKind || "bar", labels, values));
  });

  document.querySelectorAll(".heatmap").forEach((node) => {
    buildHeatmap(node, JSON.parse(node.dataset.heatmap || "[]"));
  });
}

function mountTimer() {
  const display = document.querySelector("#focus-timer");
  const minutesField = document.querySelector("#focus-minutes");
  if (!display || !minutesField) return;

  let remaining = Number(minutesField.value || 25) * 60;
  let interval = null;

  const render = () => {
    const minutes = String(Math.floor(remaining / 60)).padStart(2, "0");
    const seconds = String(remaining % 60).padStart(2, "0");
    display.textContent = `${minutes}:${seconds}`;
  };

  document.querySelector("[data-timer-start]")?.addEventListener("click", () => {
    clearInterval(interval);
    remaining = Number(minutesField.value || 25) * 60;
    render();
    interval = setInterval(() => {
      remaining = Math.max(0, remaining - 1);
      render();
      if (remaining === 0) clearInterval(interval);
    }, 1000);
  });

  document.querySelector("[data-timer-reset]")?.addEventListener("click", () => {
    clearInterval(interval);
    remaining = Number(minutesField.value || 25) * 60;
    render();
  });

  minutesField.addEventListener("change", () => {
    remaining = Number(minutesField.value || 25) * 60;
    render();
  });

  render();
}

function mountCoachExamples() {
  const input = document.querySelector("#coach-input");
  if (!input) return;
  document.querySelectorAll("[data-coach-example]").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.coachExample || "";
      input.focus();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  mountThemeToggle();
  mountCharts();
  mountTimer();
  mountCoachExamples();
});
