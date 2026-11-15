/**
 * ExamPro - Advanced Examination Management System
 * Interactive Performance Analytics Engine with Chart.js
 */

class AnalyticsEngine {
    static initStudentCharts(analyticsData) {
        if (!window.Chart || !analyticsData) return;

        // 1. Performance Over Time (Line Chart)
        const timelineCanvas = document.getElementById('chart-student-timeline');
        if (timelineCanvas && analyticsData.timeline) {
            new Chart(timelineCanvas, {
                type: 'line',
                data: {
                    labels: analyticsData.timeline.labels || [],
                    datasets: [{
                        label: 'Exam Score (%)',
                        data: analyticsData.timeline.scores || [],
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#2563eb',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `Score: ${ctx.parsed.y}%`
                            }
                        }
                    },
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            ticks: { callback: (val) => val + '%' }
                        }
                    }
                }
            });
        }

        // 2. Subject-wise Performance (Bar Chart)
        const subjectCanvas = document.getElementById('chart-student-subjects');
        if (subjectCanvas && analyticsData.subjects) {
            new Chart(subjectCanvas, {
                type: 'bar',
                data: {
                    labels: analyticsData.subjects.labels || [],
                    datasets: [{
                        label: 'Subject Average (%)',
                        data: analyticsData.subjects.scores || [],
                        backgroundColor: '#4f46e5',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { min: 0, max: 100, ticks: { callback: (val) => val + '%' } }
                    }
                }
            });
        }

        // 3. Question Format Breakdown (Doughnut Chart)
        const typeCanvas = document.getElementById('chart-student-types');
        if (typeCanvas && analyticsData.qtypes) {
            new Chart(typeCanvas, {
                type: 'doughnut',
                data: {
                    labels: analyticsData.qtypes.labels || [],
                    datasets: [{
                        data: analyticsData.qtypes.data || [],
                        backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        }
    }

    static initAdminCharts(adminData) {
        if (!window.Chart || !adminData) return;

        // 1. Grade Distribution Chart
        const gradeCanvas = document.getElementById('chart-admin-grades');
        if (gradeCanvas && adminData.grades) {
            const labels = Object.keys(adminData.grades);
            const values = Object.values(adminData.grades);
            new Chart(gradeCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Students in Grade',
                        data: values,
                        backgroundColor: [
                            '#10b981', '#3b82f6', '#6366f1', '#f59e0b', '#f97316', '#ec4899', '#ef4444'
                        ],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    }
                }
            });
        }

        // 2. Pass vs Fail Ratio (Doughnut Chart)
        const passFailCanvas = document.getElementById('chart-admin-pass-fail');
        if (passFailCanvas && adminData.pass_fail) {
            new Chart(passFailCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Passed', 'Failed'],
                    datasets: [{
                        data: [adminData.pass_fail.passed_count || 0, adminData.pass_fail.failed_count || 0],
                        backgroundColor: ['#10b981', '#ef4444'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        }
    }
}

window.AnalyticsEngine = AnalyticsEngine;

