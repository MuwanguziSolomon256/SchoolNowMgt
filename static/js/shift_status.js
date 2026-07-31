// Shared shift status handlers (extracted from teacher dashboard)
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
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-3 rounded-lg font-bold text-white z-50 ${
        type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
    }`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

async function handleClockInOut(event) {
    event.preventDefault();
    const btn = event.target.closest('button');
    if (!btn) return;
    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="material-symbols-outlined animate-spin">hourglass_empty</span><span class="hidden sm:inline">Processing...</span>';
    try {
        const isOnDuty = document.body.classList.contains('on-duty');
        const endpoint = isOnDuty ? '/teacher/api/shift/clock-out/' : '/teacher/api/shift/clock-in/';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => { window.location.reload(); }, 800);
        } else {
            showNotification(data.error || 'Operation failed', 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function handleBreakButton(event) {
    event.preventDefault();
    const btn = event.target.closest('button');
    if (!btn) return;
    if (!document.body.classList.contains('on-duty')) {
        showNotification('Please clock in first', 'error');
        return;
    }
    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="material-symbols-outlined animate-spin">hourglass_empty</span>';
    try {
        const isOnBreak = btn.classList.contains('break-active');
        const endpoint = isOnBreak ? '/teacher/api/shift/break-end/' : '/teacher/api/shift/break-start/';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (data.success) {
            showNotification(data.message, 'success');
            if (isOnBreak) {
                btn.classList.remove('break-active');
                btn.innerHTML = '<span class="material-symbols-outlined text-lg md:text-base">coffee</span><span class="hidden sm:inline">Break</span>';
            } else {
                btn.classList.add('break-active');
                btn.innerHTML = '<span class="material-symbols-outlined text-lg md:text-base">stop_circle</span><span class="hidden sm:inline">End Break</span>';
            }
            await refreshShiftStatus();
        } else {
            showNotification(data.error || 'Operation failed', 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
    btn.disabled = false;
}

function getInitialDutyStatus() {
    if (document.body.classList.contains('on-duty')) {
        return true;
    }
    const main = document.querySelector('main[data-is-on-duty]');
    return main?.dataset?.isOnDuty === 'true';
}

async function refreshShiftStatus() {
    try {
        const response = await fetch('/teacher/api/shift/status/', { method: 'GET', headers: { 'Content-Type': 'application/json' } });
        const data = await response.json();
        if (data.success) {
            const shiftCard = document.getElementById('shiftCard');
            const clockBtn = document.getElementById('clockInOutBtn');
            const breakBtn = document.getElementById('breakBtn');
            const shiftStatusText = document.getElementById('shiftStatusText');
            const shiftStatusSubtitle = document.getElementById('shiftStatusSubtitle');
            const shiftStatusDot = document.getElementById('shiftStatusDot');

            if (data.is_on_duty) {
                document.body.classList.add('on-duty');
                if (shiftCard) shiftCard.classList.add('on-duty');
            } else {
                document.body.classList.remove('on-duty');
                if (shiftCard) shiftCard.classList.remove('on-duty');
            }

            if (shiftStatusText) {
                if (data.is_on_duty && data.shift_elapsed_minutes !== undefined) {
                    const hours = Math.floor(data.shift_elapsed_minutes / 60);
                    const minutes = data.shift_elapsed_minutes % 60;
                    shiftStatusText.textContent = `Active for ${hours}h ${minutes}m`;
                } else {
                    shiftStatusText.textContent = 'Not on duty';
                }
            }

            if (shiftStatusSubtitle) {
                if (data.is_on_duty) {
                    shiftStatusSubtitle.textContent = `ON DUTY - ${new Date().toLocaleDateString(undefined, { weekday: 'long' })}`;
                } else {
                    shiftStatusSubtitle.textContent = 'Clock in to start your shift';
                }
            }

            if (shiftStatusDot) {
                shiftStatusDot.classList.toggle('bg-emerald-400', data.is_on_duty);
                shiftStatusDot.classList.toggle('bg-red-400', !data.is_on_duty);
            }

            if (clockBtn) {
                clockBtn.innerHTML = data.is_on_duty
                    ? '<span class="material-symbols-outlined text-base">logout</span><span>Clock Out</span>'
                    : '<span class="material-symbols-outlined text-base">login</span><span>Clock In</span>';
            }

            if (breakBtn) {
                if (data.is_on_break) {
                    breakBtn.classList.add('break-active', 'bg-orange-500', 'text-white');
                    breakBtn.innerHTML = '<span class="material-symbols-outlined">stop_circle</span><span class="hidden sm:inline">End Break</span>';
                } else {
                    breakBtn.classList.remove('break-active', 'bg-orange-500', 'text-white');
                    breakBtn.innerHTML = '<span class="material-symbols-outlined">coffee</span><span class="hidden sm:inline">Break</span>';
                }
            }
        }
    } catch (error) {
        console.error('Error refreshing shift status:', error);
    }
}

async function initShiftStatusTimer() {
    if (getInitialDutyStatus()) {
        document.body.classList.add('on-duty');
    }
    refreshShiftStatus();
    setInterval(refreshShiftStatus, 30000);
}

function attachShiftHandlers() {
    const clockBtn = document.getElementById('clockInOutBtn');
    const breakBtn = document.getElementById('breakBtn');

    if (clockBtn) {
        clockBtn.addEventListener('click', handleClockInOut);
    }
    if (breakBtn) {
        breakBtn.addEventListener('click', handleBreakButton);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    attachShiftHandlers();
    initShiftStatusTimer();
});
