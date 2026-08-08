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
        // Choose API prefix depending on whether we're in support_staff area
        const apiBase = window.location.pathname.startsWith('/teacher/support/shift-supervisor') ? '/teacher/support/shift-supervisor/api/shift/' : (window.location.pathname.startsWith('/teacher/support') ? '/teacher/support/api/shift/' : '/teacher/api/shift/');
        const endpoint = isOnDuty ? `${apiBase}clock-out/` : `${apiBase}clock-in/`;
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
        const apiBase = window.location.pathname.startsWith('/teacher/support/shift-supervisor') ? '/teacher/support/shift-supervisor/api/shift/' : (window.location.pathname.startsWith('/teacher/support') ? '/teacher/support/api/shift/' : '/teacher/api/shift/');
        const endpoint = isOnBreak ? `${apiBase}break-end/` : `${apiBase}break-start/`;
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

async function refreshShiftStatus() {
    try {
        const apiBase = window.location.pathname.startsWith('/teacher/support/shift-supervisor') ? '/teacher/support/shift-supervisor/api/shift/' : (window.location.pathname.startsWith('/teacher/support') ? '/teacher/support/api/shift/' : '/teacher/api/shift/');
        const response = await fetch(`${apiBase}status/`, { method: 'GET', headers: { 'Content-Type': 'application/json' } });
        const data = await response.json();
        if (data.success) {
            const shiftCard = document.getElementById('shiftCard');
            if (data.is_on_duty) {
                document.body.classList.add('on-duty');
                if (shiftCard) {
                    shiftCard.classList.add('on-duty');
                }
            } else {
                document.body.classList.remove('on-duty');
                if (shiftCard) {
                    shiftCard.classList.remove('on-duty');
                }
            }
            if (shiftCard && data.is_on_duty && data.shift_elapsed_minutes !== undefined) {
                const hours = Math.floor(data.shift_elapsed_minutes / 60);
                const minutes = data.shift_elapsed_minutes % 60;
                const elapsedText = `Active for ${hours}h ${minutes}m`;
                const h2 = shiftCard.querySelector('h2');
                if (h2) h2.textContent = elapsedText;
            }
            const breakBtn = document.getElementById('breakBtn');
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

function initShiftStatusTimer() {
    refreshShiftStatus();
    setInterval(refreshShiftStatus, 30000);
}

function attachShiftHandlers() {
    const clockBtn = document.getElementById('clockInOutBtn');
    const breakBtn = document.getElementById('breakBtn');

    // Fallbacks: if IDs are not present (older templates), try to find buttons by their text or icon
    let resolvedClockBtn = clockBtn;
    if (!resolvedClockBtn) {
        resolvedClockBtn = Array.from(document.querySelectorAll('button')).find(b => /clock in|clock out|login/i.test(b.innerText));
    }
    let resolvedBreakBtn = breakBtn;
    if (!resolvedBreakBtn) {
        resolvedBreakBtn = Array.from(document.querySelectorAll('button')).find(b => /break|coffee|end break/i.test(b.innerText));
    }

    if (resolvedClockBtn) {
        resolvedClockBtn.addEventListener('click', handleClockInOut);
    }
    if (resolvedBreakBtn) {
        resolvedBreakBtn.addEventListener('click', handleBreakButton);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        attachShiftHandlers();
        initShiftStatusTimer();
    });
} else {
    attachShiftHandlers();
    initShiftStatusTimer();
}
