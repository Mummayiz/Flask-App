function adminPalette(alpha = 0.82) {
  return [
    `rgba(55, 125, 241, ${alpha})`,
    `rgba(20, 184, 166, ${alpha})`,
    `rgba(245, 158, 11, ${alpha})`,
    `rgba(244, 114, 182, ${alpha})`,
    `rgba(99, 102, 241, ${alpha})`,
    `rgba(34, 197, 94, ${alpha})`,
    `rgba(251, 113, 133, ${alpha})`,
    `rgba(14, 165, 233, ${alpha})`,
    `rgba(168, 85, 247, ${alpha})`,
    `rgba(249, 115, 22, ${alpha})`,
  ];
}

function adminChartOptions(kind) {
  const textColor = getComputedStyle(document.body).getPropertyValue("--text").trim() || "#10233b";
  const lineColor = getComputedStyle(document.body).getPropertyValue("--line").trim() || "rgba(58, 102, 156, 0.12)";
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: kind === "doughnut",
        labels: {
          color: textColor,
          padding: 16,
        },
      },
    },
    scales: kind === "doughnut" ? {} : {
      x: {
        ticks: { color: textColor },
        grid: { display: false },
      },
      y: {
        beginAtZero: true,
        ticks: { color: textColor },
        grid: { color: lineColor },
      },
    },
  };
}

function renderAdminChart(canvasId, kind, labels, values, label) {
  const node = document.getElementById(canvasId);
  if (!node || typeof Chart === "undefined" || !labels.length) return;

  const baseColors = adminPalette();
  const config = {
    type: kind,
    data: {
      labels,
      datasets: [{
        label,
        data: values,
        backgroundColor: kind === "line" ? "rgba(55, 125, 241, 0.14)" : labels.map((_, index) => baseColors[index % baseColors.length]),
        borderColor: kind === "line" ? "rgba(55, 125, 241, 1)" : labels.map((_, index) => baseColors[index % baseColors.length]),
        borderWidth: kind === "line" ? 3 : 0,
        fill: kind === "line",
        tension: 0.35,
        borderRadius: kind === "bar" ? 12 : 0,
      }],
    },
    options: adminChartOptions(kind),
  };

  new Chart(node, config);
}

function mountAdminCharts() {
  const payloadNode = document.getElementById("admin-chart-data");
  if (!payloadNode) return;

  const payload = JSON.parse(payloadNode.textContent || "{}");
  renderAdminChart("top-productive-chart", "bar", payload.topProductive?.labels || [], payload.topProductive?.values || [], "Productivity score");
  renderAdminChart("top-active-chart", "bar", payload.topActive?.labels || [], payload.topActive?.values || [], "Activity events");
  renderAdminChart("completion-rate-chart", "bar", payload.completionRate?.labels || [], payload.completionRate?.values || [], "Completion rate");
  renderAdminChart("average-focus-chart", "bar", payload.averageFocus?.labels || [], payload.averageFocus?.values || [], "Average focus minutes");
  renderAdminChart("daily-active-chart", "line", payload.dailyActiveUsers?.labels || [], payload.dailyActiveUsers?.values || [], "Daily active users");
  renderAdminChart("weekly-productivity-chart", "line", payload.weeklyProductivity?.labels || [], payload.weeklyProductivity?.values || [], "Weekly productivity");
  renderAdminChart("task-priority-chart", "doughnut", payload.taskPriorities?.labels || [], payload.taskPriorities?.values || [], "Task priorities");
}

document.addEventListener("DOMContentLoaded", mountAdminCharts);
