// Chart configurations for visualizing career recommendation data

// Function to create career match radar chart
function createCareerMatchChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Your Match',
                data: data,
                backgroundColor: 'rgba(78, 115, 223, 0.2)',
                borderColor: 'rgba(78, 115, 223, 1)',
                pointBackgroundColor: 'rgba(78, 115, 223, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(78, 115, 223, 1)',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    ticks: {
                        beginAtZero: true,
                        max: 100,
                        stepSize: 20
                    }
                }
            }
        }
    });
}

// Function to create market trends bar chart
function createMarketTrendsChart(canvasId, careers, demandLevels) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: careers,
            datasets: [{
                label: 'Market Demand',
                data: demandLevels,
                backgroundColor: 'rgba(28, 200, 138, 0.5)',
                borderColor: 'rgba(28, 200, 138, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        callback: function(value) {
                            return (value * 100) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Function to create career comparison chart
function createCareerComparisonChart(canvasId, careers, scores) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Generate colors for each career
    const colors = [];
    for (let i = 0; i < careers.length; i++) {
        const hue = (i * 50) % 360;
        colors.push(`hsla(${hue}, 70%, 60%, 0.7)`);
    }
    
    return new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: careers,
            datasets: [{
                data: scores,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Function to create feedback summary chart
function createFeedbackChart(canvasId, ratings) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['1 ★', '2 ★', '3 ★', '4 ★', '5 ★'],
            datasets: [{
                data: ratings,
                backgroundColor: [
                    'rgba(231, 74, 59, 0.7)',
                    'rgba(246, 194, 62, 0.7)',
                    'rgba(54, 185, 204, 0.7)',
                    'rgba(28, 200, 138, 0.7)',
                    'rgba(0, 172, 105, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}
