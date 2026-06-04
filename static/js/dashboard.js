// Dashboard Interactivity

document.addEventListener('DOMContentLoaded', function() {
    setupTaskListeners();
    setupSearchListener();
});

// ===== TASK MANAGEMENT =====

function setupTaskListeners() {
    document.querySelectorAll('.task-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function(e) {
            e.preventDefault();
            toggleTaskStatus(this.dataset.taskId, this.checked);
        });
    });

    document.querySelector('.quick-task-btn').addEventListener('click', openQuickTaskModal);
}

function toggleTaskStatus(taskId, completed) {
    const formData = new FormData();
    formData.append('status', completed ? 'completed' : 'pending');

    fetch(`/teacher/api/tasks/${taskId}/toggle/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskItem) {
                const title = taskItem.querySelector('.task-title');
                if (data.new_status === 'completed') {
                    title.classList.add('line-through', 'opacity-50');
                    taskItem.classList.add('opacity-75');
                } else {
                    title.classList.remove('line-through', 'opacity-50');
                    taskItem.classList.remove('opacity-75');
                }
            }
            showNotification('Task updated successfully', 'success');
        } else {
            showNotification('Failed to update task: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function handleCreateTask(e) {
    e.preventDefault();
    const form = document.getElementById('quickTaskForm');
    const formData = new FormData(form);

    fetch('/teacher/api/tasks/create/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Task created successfully!', 'success');
            form.reset();
            closeQuickTaskModal();
            // Optionally reload or add task to list
            setTimeout(() => location.reload(), 1500);
        } else {
            showNotification('Failed to create task: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

// ===== MODAL MANAGEMENT =====

function openQuickTaskModal() {
    document.getElementById('quickTaskModal').classList.remove('hidden');
}

function closeQuickTaskModal(e) {
    if (e && e.target.id !== 'quickTaskModal') return;
    document.getElementById('quickTaskModal').classList.add('hidden');
}

function openGradeModal() {
    document.getElementById('gradeModal').classList.remove('hidden');
}

function closeGradeModal(e) {
    if (e && e.target.id !== 'gradeModal') return;
    document.getElementById('gradeModal').classList.add('hidden');
}

function openCircularModal() {
    document.getElementById('circularModal').classList.remove('hidden');
}

function closeCircularModal(e) {
    if (e && e.target.id !== 'circularModal') return;
    document.getElementById('circularModal').classList.add('hidden');
}

// ===== GRADE ENTRY =====

function handleGradeEntry(e) {
    e.preventDefault();
    const form = document.getElementById('gradeForm');
    const formData = new FormData(form);

    fetch('/teacher/api/grades/quick-add/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Grade recorded for ${data.grade.student}: ${data.grade.score}`, 'success');
            form.reset();
            closeGradeModal();
        } else {
            showNotification('Failed to record grade: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

// ===== CIRCULAR SENDING =====

function handleSendCircular(e) {
    e.preventDefault();
    const form = document.getElementById('circularForm');
    const formData = new FormData(form);

    fetch('/teacher/api/circulars/send/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            form.reset();
            closeCircularModal();
        } else {
            showNotification('Failed to send circular: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

// ===== STUDENT SEARCH =====

function setupSearchListener() {
    const searchInput = document.getElementById('student-search');
    const searchResults = document.getElementById('search-results');

    if (!searchInput) return;

    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();

        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        fetch(`/teacher/api/students/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    searchResults.innerHTML = data.results.map(student => `
                        <div class="p-3 border-b hover:bg-gray-100 cursor-pointer" onclick="selectStudent(${student.id}, '${student.name}')">
                            <p class="font-semibold">${student.name}</p>
                            <p class="text-sm text-gray-600">${student.admission_number} • ${student.class}</p>
                        </div>
                    `).join('');
                    searchResults.classList.remove('hidden');
                } else {
                    searchResults.innerHTML = '<div class="p-3 text-gray-500">No students found</div>';
                    searchResults.classList.remove('hidden');
                }
            })
            .catch(error => console.error('Search error:', error));
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#student-search')) {
            searchResults.classList.add('hidden');
        }
    });
}

function selectStudent(studentId, studentName) {
    console.log('Selected student:', studentId, studentName);
    // Could open student detail page or perform other actions
    document.getElementById('student-search').value = '';
    document.getElementById('search-results').classList.add('hidden');
}

// ===== ATTENDANCE HANDLER =====

function handleAttendanceClick(e) {
    e.preventDefault();
    // Navigate to attendance page
    window.location.href = '/teacher/attendance/';
}

// ===== UTILITY FUNCTIONS =====

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showNotification(message, type = 'info') {
    // Create a simple notification (can be replaced with toast library)
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-3 rounded-lg font-bold text-white z-50 animation-fade-in ${
        type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
    }`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// ===== PERFORMANCE CHART (Optional Enhancement) =====

function initPerformanceChart() {
    const canvas = document.getElementById('performanceChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const stats = window.performanceStats || [];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: stats.map((_, i) => `Day ${i + 1}`),
            datasets: [{
                label: 'Average Score',
                data: stats.map(s => s.score),
                backgroundColor: '#feb700',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}
