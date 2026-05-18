/* ============================================================
   TeamFlow — kanban.js
   Handles: tab switching, drag & drop, task detail modal,
            file upload (modal + quick), completion confirm,
            column counts, toast notifications.
   Loaded via: <script src="{{ url_for('static', filename='js/kanban.js') }}"></script>
   ============================================================ */

'use strict';

// ══════════════════════════════════════
//  TAB SWITCHING
// ══════════════════════════════════════

/**
 * Switch between kanban / analytics / chat / members tabs.
 * @param {string} tabId  - matches the id "tab-{tabId}"
 * @param {HTMLElement} btn - the clicked button element
 */
function switchTab(tabId, btn) {
    // hide all panels
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    // deactivate all tab buttons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    // show target panel
    const panel = document.getElementById('tab-' + tabId);
    if (panel) panel.classList.add('active');

    // activate clicked button
    if (btn) btn.classList.add('active');

    // lazy-init charts when analytics tab is opened
    if (tabId === 'analytics' && typeof initCharts === 'function' && !window.chartsInited) {
        window.chartsInited = true;
        initCharts();
    }

    // scroll chat to bottom when chat tab is opened
    if (tabId === 'chat') {
        setTimeout(scrollChatBottom, 50);
    }
}


// ══════════════════════════════════════
//  DRAG & DROP
// ══════════════════════════════════════

let draggedId = null;

function onDragStart(e, taskId) {
    draggedId = taskId;
    const card = document.getElementById('task-' + taskId);
    if (card) card.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function onDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

function onDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

function onDrop(e, newStatus) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');

    if (!draggedId) return;

    const card = document.getElementById('task-' + draggedId);
    if (!card) return;

    // move card to new column
    e.currentTarget.appendChild(card);
    card.classList.remove('dragging');
    updateCounts();

    // special handling for Completed — show confirmation first
    if (newStatus === 'Completed') {
        showCompletionModal(draggedId);
        draggedId = null;
        return;
    }

    persistMove(draggedId, newStatus);
    draggedId = null;
}

// cleanup after drag ends regardless of where it lands
document.addEventListener('dragend', () => {
    document.querySelectorAll('.task-card').forEach(c => c.classList.remove('dragging'));
    document.querySelectorAll('.kanban-drop-zone').forEach(z => z.classList.remove('drag-over'));
});

/**
 * Recount cards in each column and update the counter badge.
 */
function updateCounts() {
    document.querySelectorAll('.kanban-drop-zone').forEach(zone => {
        const status = zone.dataset.status;
        if (!status) return;
        const colId = status.toLowerCase().replace(/ /g, '-');
        const cnt = zone.querySelectorAll('.task-card').length;
        const el = document.getElementById('cnt-' + colId);
        if (el) el.textContent = cnt;
    });
}

/**
 * Send the status change to the server.
 * @param {number} taskId
 * @param {string} newStatus
 */
function persistMove(taskId, newStatus) {
    fetch('/task/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, new_status: newStatus })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('✓ Task moved to ' + newStatus);
        } else {
            showToast('✗ Could not update task', true);
            // reload so the board reflects real state
            setTimeout(() => location.reload(), 1500);
        }
    })
    .catch(() => {
        showToast('✗ Network error', true);
        setTimeout(() => location.reload(), 1500);
    });
}


// ══════════════════════════════════════
//  COMPLETION CONFIRMATION OVERLAY
// ══════════════════════════════════════

function showCompletionModal(taskId) {
    let overlay = document.getElementById('completeOverlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'completeOverlay';
        overlay.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:1100;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px);';
        document.body.appendChild(overlay);
    }

    overlay.innerHTML = `
        <div class="confirm-box" style="background:linear-gradient(155deg,rgba(20,20,20,0.99) 0%,rgba(12,12,12,1) 100%);border:1px solid rgba(99,220,100,0.2);border-radius:16px;padding:28px;max-width:400px;width:100%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.7);">
            <div style="font-size:2rem;margin-bottom:12px;">✅</div>
            <div style="font-size:1rem;font-weight:600;color:#eee;margin-bottom:8px;">Mark as Completed?</div>
            <div style="font-size:0.8rem;color:#777;margin-bottom:22px;line-height:1.5;">
                This will mark the task as complete.<br>You can still submit a full report from the task detail.
            </div>
            <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
                <button onclick="submitCompletion(${taskId})"
                        style="padding:10px 20px;background:linear-gradient(135deg,#4f8fff,#3568dc);border:none;border-radius:9px;color:#fff;font-size:0.84rem;font-weight:600;font-family:'DM Sans',sans-serif;cursor:pointer;display:flex;align-items:center;gap:6px;">
                    <i class="bi bi-check2-circle"></i> Confirm Complete
                </button>
                <button onclick="cancelCompletion(${taskId})"
                        style="padding:10px 16px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:9px;color:#777;font-size:0.84rem;font-family:'DM Sans',sans-serif;cursor:pointer;">
                    Cancel
                </button>
            </div>
        </div>`;

    overlay.style.display = 'flex';
}

function submitCompletion(taskId) {
    const overlay = document.getElementById('completeOverlay');
    if (overlay) overlay.style.display = 'none';
    persistMove(taskId, 'Completed');
    showToast('✓ Task marked as completed!');
}

function cancelCompletion(taskId) {
    const overlay = document.getElementById('completeOverlay');
    if (overlay) overlay.style.display = 'none';
    // reload to restore the card to its previous column
    location.reload();
}


// ══════════════════════════════════════
//  TASK DETAIL MODAL
// ══════════════════════════════════════

let currentTaskId   = null;
let currentUploadUrl = null;

function openTaskModal(taskId) {
    currentTaskId    = taskId;
    currentUploadUrl = null;

    const modal = document.getElementById('taskModal');
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';

    // reset to loading state
    document.getElementById('modalTitle').textContent  = 'Loading...';
    document.getElementById('modalStatus').textContent = '—';
    document.getElementById('modalDesc').textContent   = '...';
    document.getElementById('modalAssignee').textContent = '—';
    document.getElementById('modalPriority').textContent = '—';
    document.getElementById('modalDeadline').textContent = '—';
    document.getElementById('fileList').innerHTML       = '<div style="font-size:0.78rem;color:#666;padding:10px 0;">Loading...</div>';
    document.getElementById('modalActions').innerHTML   = '';
    document.getElementById('uploadSection').style.display = 'none';

    fetch('/task/' + taskId + '/detail')
        .then(r => r.json())
        .then(data => {
            document.getElementById('modalTitle').textContent    = data.title;
            document.getElementById('modalStatus').textContent   = data.status;
            document.getElementById('modalDesc').textContent     = data.description || 'No description provided.';
            document.getElementById('modalAssignee').textContent = data.assignee;
            document.getElementById('modalPriority').textContent = data.priority;
            document.getElementById('modalDeadline').textContent = data.deadline;

            renderFileList(data.files);

            if (data.can_upload) {
                currentUploadUrl = data.upload_url;
                document.getElementById('uploadSection').style.display = 'block';
            }

            // build action buttons
            let actions = '';
            if (data.can_upload) {
                actions += `<a href="${data.report_url}" class="btn-modal-action btn-complete"><i class="bi bi-check2-circle"></i> Mark Complete</a>`;
            }
            if (data.can_edit) {
                actions += `<a href="${data.edit_url}" class="btn-modal-action btn-edit-task"><i class="bi bi-pencil"></i> Edit Task</a>`;
            }
            document.getElementById('modalActions').innerHTML = actions;
        })
        .catch(() => {
            document.getElementById('modalTitle').textContent = 'Error loading task';
        });
}

function renderFileList(files) {
    const container = document.getElementById('fileList');
    if (!files || files.length === 0) {
        container.innerHTML = '<div style="font-size:0.78rem;color:#666;padding:10px 0;">No files attached yet.</div>';
        return;
    }
    container.innerHTML = files.map(f => `
        <div class="file-row">
            <div class="file-icon"><i class="bi bi-file-earmark"></i></div>
            <div class="file-info">
                <div class="file-name" title="${escapeHtml(f.original_name)}">${escapeHtml(f.original_name)}</div>
                <div class="file-meta">${escapeHtml(f.uploaded_by)} · ${f.uploaded_at} · ${f.file_size}</div>
            </div>
            <a href="${f.download_url}" class="file-download" download>
                <i class="bi bi-download"></i> Download
            </a>
        </div>
    `).join('');
}

function closeModal() {
    const modal = document.getElementById('taskModal');
    if (modal) modal.classList.remove('open');
    document.body.style.overflow = '';
    currentTaskId    = null;
    currentUploadUrl = null;
}

function closeModalOutside(e) {
    if (e.target === document.getElementById('taskModal')) closeModal();
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
});


// ══════════════════════════════════════
//  FILE UPLOAD — MODAL DROP ZONE
// ══════════════════════════════════════

function uploadDragOver(e) {
    e.preventDefault();
    document.getElementById('uploadZone').classList.add('drag-active');
}

function uploadDragLeave() {
    document.getElementById('uploadZone').classList.remove('drag-active');
}

function uploadDrop(e) {
    e.preventDefault();
    document.getElementById('uploadZone').classList.remove('drag-active');
    uploadFiles(e.dataTransfer.files);
}

function handleFileSelect(e) {
    uploadFiles(e.target.files);
}

function uploadFiles(files) {
    if (!files || files.length === 0 || !currentUploadUrl) return;

    const status = document.getElementById('uploadStatus');
    const bar    = document.getElementById('uploadProgressBar');
    const fill   = document.getElementById('uploadProgressFill');

    let done  = 0;
    const total = files.length;
    bar.style.display  = 'block';
    fill.style.width   = '0%';

    Array.from(files).forEach(file => {
        const fd = new FormData();
        fd.append('file', file);

        // get csrf token from the hidden input that Flask renders in the page
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) fd.append('csrf_token', csrfInput.value);

        if (status) status.textContent = 'Uploading ' + file.name + '...';

        fetch(currentUploadUrl, { method: 'POST', body: fd })
            .then(r => r.json())
            .then(data => {
                done++;
                fill.style.width = ((done / total) * 100) + '%';

                if (data.success) {
                    // add new file row without reloading
                    const listEl = document.getElementById('fileList');
                    // clear the "no files yet" message if present
                    if (listEl.querySelector('div[style]')) listEl.innerHTML = '';

                    const row = document.createElement('div');
                    row.className = 'file-row';
                    row.innerHTML = `
                        <div class="file-icon"><i class="bi bi-file-earmark"></i></div>
                        <div class="file-info">
                            <div class="file-name">${escapeHtml(data.file.original_name)}</div>
                            <div class="file-meta">${escapeHtml(data.file.uploaded_by)} · ${data.file.uploaded_at} · ${data.file.file_size}</div>
                        </div>
                        <a href="${data.file.download_url}" class="file-download" download>
                            <i class="bi bi-download"></i> Download
                        </a>`;
                    listEl.appendChild(row);

                    if (status) status.textContent = '✓ ' + data.file.original_name + ' uploaded';
                } else {
                    if (status) status.textContent = '✗ Error: ' + (data.error || 'Upload failed');
                }

                if (done === total) {
                    setTimeout(() => { bar.style.display = 'none'; }, 1400);
                }
            })
            .catch(() => {
                if (status) status.textContent = '✗ Upload failed';
            });
    });
}


// ══════════════════════════════════════
//  QUICK UPLOAD (from card button)
// ══════════════════════════════════════

let quickUploadTaskId = null;
let quickUploadUrl    = null;

function quickUpload(taskId, uploadUrl) {
    quickUploadTaskId = taskId;
    quickUploadUrl    = uploadUrl;
    const input = document.getElementById('quickUploadInput');
    if (input) { input.value = ''; input.click(); }
}

function handleQuickUpload(e) {
    const files = e.target.files;
    if (!files || files.length === 0 || !quickUploadUrl) return;

    const csrfInput = document.querySelector('input[name="csrf_token"]');

    Array.from(files).forEach(file => {
        const fd = new FormData();
        fd.append('file', file);
        if (csrfInput) fd.append('csrf_token', csrfInput.value);

        fetch(quickUploadUrl, { method: 'POST', body: fd })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // update the file count badge on the card
                    const card = document.getElementById('task-' + quickUploadTaskId);
                    if (card) {
                        let badge = card.querySelector('.task-files-badge');
                        if (badge) {
                            const cur = parseInt(badge.textContent.replace(/\D/g, '')) || 0;
                            badge.innerHTML = '<i class="bi bi-paperclip"></i>' + (cur + 1);
                        } else {
                            const footer = card.querySelector('.task-card-footer > div:last-child');
                            if (footer) {
                                const b = document.createElement('span');
                                b.className = 'task-files-badge';
                                b.innerHTML = '<i class="bi bi-paperclip"></i>1';
                                footer.insertBefore(b, footer.firstChild);
                            }
                        }
                    }
                    showToast('✓ ' + data.file.original_name + ' uploaded');
                } else {
                    showToast('✗ ' + (data.error || 'Upload failed'), true);
                }
            })
            .catch(() => showToast('✗ Upload failed', true));
    });
}


// ══════════════════════════════════════
//  CHAT
// ══════════════════════════════════════

function scrollChatBottom() {
    const el = document.getElementById('chatArea');
    if (el) el.scrollTop = el.scrollHeight;
}


// ══════════════════════════════════════
//  TOAST NOTIFICATION
// ══════════════════════════════════════

let toastTimer = null;

/**
 * Show a small toast at the bottom-right of the screen.
 * @param {string}  msg      - message text
 * @param {boolean} isError  - red style if true, green if false
 */
function showToast(msg, isError) {
    let t = document.getElementById('kanbanToast');
    if (!t) {
        t = document.createElement('div');
        t.id = 'kanbanToast';
        document.body.appendChild(t);
    }

    t.textContent = msg;
    t.style.background = isError ? 'rgba(220,53,69,0.18)'  : 'rgba(40,167,69,0.18)';
    t.style.color      = isError ? '#e07070'               : '#5fbe82';
    t.style.border     = isError ? '1px solid rgba(220,53,69,0.3)' : '1px solid rgba(40,167,69,0.3)';
    t.style.opacity    = '1';

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.style.opacity = '0'; }, 3000);
}


// ══════════════════════════════════════
//  UTILITY
// ══════════════════════════════════════

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
