// kanban.js - main javascript file for the kanban board page

// This makes the tab work when you click on it
function switchTab(tabId, btn) {

    // get all tab panels and remove active from all of them
    var allPanels = document.querySelectorAll('.tab-panel');
    for (var i = 0; i < allPanels.length; i++) {
        allPanels[i].classList.remove('active');
    }

    // also remove active from all the buttons
    var allBtns = document.querySelectorAll('.tab-btn');
    for (var j = 0; j < allBtns.length; j++) {
        allBtns[j].classList.remove('active');
    }

    // now add active to the right panel
    var panel = document.getElementById('tab-' + tabId);
    if (panel != null) {
        panel.classList.add('active');
    }

    // add active to the button that was clicked
    if (btn != null) {
        btn.classList.add('active');
    }

    // if analytics tab open the charts
    if (tabId === 'analytics') {
        console.log("analytics tab opened");
        if (typeof startCharts === 'function' && !window.chartsInited) {
            startCharts();
            window.chartsInited = true;
        }
    }

    // scroll to bottom of chat if chat tab
    if (tabId === 'chat') {
        setTimeout(scrollChatBottom, 50);
    }
}


// variable to store which card is being dragged
var draggedId = null;

// this runs when user starts dragging a card
function onDragStart(e, taskId) {
    console.log("drag started for task " + taskId);
    draggedId = taskId;
    e.dataTransfer.effectAllowed = 'move';
    var card = document.getElementById('task-' + taskId);
    if (card != null) {
        card.classList.add('dragging');
    }
}

// this runs when dragging over a column
function onDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

// this runs when card leaves the column area
function onDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

// this runs when card is dropped into a column
function onDrop(e, newStatus) {
    e.preventDefault();
    console.log("Card dropped!");
    e.currentTarget.classList.remove('drag-over');

    // if nothing is being dragged just stop
    if (!draggedId) return;

    var card = document.getElementById('task-' + draggedId);
    if (!card) return;

    // move the card into the new column
    e.currentTarget.appendChild(card);
    card.classList.remove('dragging');

    // update the count numbers on each column
    updateCounts();

    // if dropped in completed column show a confirm popup first
    if (newStatus === 'Completed') {
        showCompletionModal(draggedId);
        draggedId = null;
        return;
    }

    // send to server
    updateServer(draggedId, newStatus);
    draggedId = null;
}

// cleanup dragging classes when drag ends
document.addEventListener('dragend', function() {
    var allCards = document.querySelectorAll('.task-card');
    for (var i = 0; i < allCards.length; i++) {
        allCards[i].classList.remove('dragging');
    }
    var allZones = document.querySelectorAll('.kanban-drop-zone');
    for (var j = 0; j < allZones.length; j++) {
        allZones[j].classList.remove('drag-over');
    }
});

// Function to update the count badges on each column
function updateCounts() {
    var allZones = document.querySelectorAll('.kanban-drop-zone');
    for (var i = 0; i < allZones.length; i++) {
        var zone = allZones[i];
        var status = zone.dataset.status;
        if (!status) continue;
        var colId = status.toLowerCase().replace(/ /g, '-');
        var cnt = zone.querySelectorAll('.task-card').length;
        var el = document.getElementById('cnt-' + colId);
        if (el != null) {
            el.textContent = cnt;
        }
    }
}

// Function to send the new status to the server
function updateServer(taskId, newStatus) {
    console.log("Sending task " + taskId + " to status: " + newStatus);
    fetch('/task/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, new_status: newStatus })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success) {
            showToast('✓ Task moved to ' + newStatus);
        } else {
            showToast('✗ Could not update task', true);
            setTimeout(function() { location.reload(); }, 1500);
        }
    })
    .catch(function() {
        console.log("error");
        alert("An error happened");
        setTimeout(function() { location.reload(); }, 1500);
    });
}


// Function to open the modal when task is dropped in completed column
function showCompletionModal(taskId) {
    console.log("showing completion modal for " + taskId);
    var overlay = document.getElementById('completeOverlay');

    // create the overlay div if it doesnt exist yet
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'completeOverlay';
        overlay.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:1100;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px);';
        document.body.appendChild(overlay);
    }

    // put the html inside the overlay
    overlay.innerHTML = '<div class="confirm-box" style="background:linear-gradient(155deg,rgba(20,20,20,0.99) 0%,rgba(12,12,12,1) 100%);border:1px solid rgba(99,220,100,0.2);border-radius:16px;padding:28px;max-width:400px;width:100%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.7);">' +
        '<div style="font-size:2rem;margin-bottom:12px;">✅</div>' +
        '<div style="font-size:1rem;font-weight:600;color:#eee;margin-bottom:8px;">Mark as Completed?</div>' +
        '<div style="font-size:0.8rem;color:#777;margin-bottom:22px;line-height:1.5;">' +
            'This will mark the task as complete.<br>You can still submit a full report from the task detail.' +
        '</div>' +
        '<div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">' +
            '<button onclick="submitCompletion(' + taskId + ')"' +
                    ' style="padding:10px 20px;background:linear-gradient(135deg,#4f8fff,#3568dc);border:none;border-radius:9px;color:#fff;font-size:0.84rem;font-weight:600;font-family:\'DM Sans\',sans-serif;cursor:pointer;display:flex;align-items:center;gap:6px;">' +
                '<i class="bi bi-check2-circle"></i> Confirm Complete' +
            '</button>' +
            '<button onclick="cancelCompletion(' + taskId + ')"' +
                    ' style="padding:10px 16px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:9px;color:#777;font-size:0.84rem;font-family:\'DM Sans\',sans-serif;cursor:pointer;">' +
                'Cancel' +
            '</button>' +
        '</div>' +
    '</div>';

    // show the overlay
    overlay.style.display = 'flex';
}

// this runs when user clicks confirm on the completion modal
function submitCompletion(taskId) {
    console.log("user confirmed task complete: " + taskId);
    var overlay = document.getElementById('completeOverlay');
    if (overlay != null) {
        overlay.style.display = 'none';
    }
    updateServer(taskId, 'Completed');
    showToast('✓ Task marked as completed!');
}

// this runs when user clicks cancel on the completion modal
function cancelCompletion(taskId) {
    var overlay = document.getElementById('completeOverlay');
    if (overlay != null) {
        overlay.style.display = 'none';
    }
    // just reload the page its easier
    location.reload();
}


// variables for the task detail modal
var currentTaskId = null;
var currentUploadUrl = null;

// Function to open the task detail modal
function openTaskModal(taskId) {
    console.log("Fetching data for task " + taskId);
    currentTaskId = taskId;
    currentUploadUrl = null;

    var modal = document.getElementById('taskModal');
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';

    // set loading text while waiting for data
    document.getElementById('modalTitle').textContent = 'Loading...';
    document.getElementById('modalStatus').textContent = '—';
    document.getElementById('modalDesc').textContent = '...';
    document.getElementById('modalAssignee').textContent = '—';
    document.getElementById('modalPriority').textContent = '—';
    document.getElementById('modalDeadline').textContent = '—';
    document.getElementById('fileList').innerHTML = '<div style="font-size:0.78rem;color:#666;padding:10px 0;">Loading...</div>';
    document.getElementById('modalActions').innerHTML = '';
    document.getElementById('uploadSection').style.display = 'none';

    // fetch the task details from server
    fetch('/task/' + taskId + '/detail')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            console.log("got task data");
            // put all the data into the modal fields
            document.getElementById('modalTitle').textContent = data.title;
            document.getElementById('modalStatus').textContent = data.status;
            document.getElementById('modalDesc').textContent = data.description || 'No description provided.';
            document.getElementById('modalAssignee').textContent = data.assignee;
            document.getElementById('modalPriority').textContent = data.priority;
            document.getElementById('modalDeadline').textContent = data.deadline;

            // show the files
            renderFileList(data.files);

            // show upload section if user can upload
            if (data.can_upload) {
                currentUploadUrl = data.upload_url;
                document.getElementById('uploadSection').style.display = 'block';
            }

            // build the action buttons html
            var actions = '';
            if (data.can_upload) {
                actions = actions + '<a href="' + data.report_url + '" class="btn-modal-action btn-complete"><i class="bi bi-check2-circle"></i> Mark Complete</a>';
            }
            if (data.can_edit) {
                actions = actions + '<a href="' + data.edit_url + '" class="btn-modal-action btn-edit-task"><i class="bi bi-pencil"></i> Edit Task</a>';
            }
            document.getElementById('modalActions').innerHTML = actions;
        })
        .catch(function() {
            console.log("error");
            document.getElementById('modalTitle').textContent = 'Error loading task';
        });
}

// Function to show the list of files in the modal
function renderFileList(files) {
    var container = document.getElementById('fileList');

    // if no files show a message
    if (!files || files.length === 0) {
        container.innerHTML = '<div style="font-size:0.78rem;color:#666;padding:10px 0;">No files attached yet.</div>';
        return;
    }

    // Start the loop to build file rows
    var html = '';
    for (var i = 0; i < files.length; i++) {
        var f = files[i];
        html = html + '<div class="file-row">' +
            '<div class="file-icon"><i class="bi bi-file-earmark"></i></div>' +
            '<div class="file-info">' +
                '<div class="file-name" title="' + fixText(f.original_name) + '">' + fixText(f.original_name) + '</div>' +
                '<div class="file-meta">' + fixText(f.uploaded_by) + ' · ' + f.uploaded_at + ' · ' + f.file_size + '</div>' +
            '</div>' +
            '<a href="' + f.download_url + '" class="file-download" download>' +
                '<i class="bi bi-download"></i> Download' +
            '</a>' +
        '</div>';
    }
    container.innerHTML = html;
}

// Function to close the modal
function closeModal() {
    var modal = document.getElementById('taskModal');
    if (modal != null) {
        modal.classList.remove('open');
    }
    document.body.style.overflow = '';
    currentTaskId = null;
    currentUploadUrl = null;
}

// close modal if user clicks outside of it
function closeModalOutside(e) {
    if (e.target === document.getElementById('taskModal')) {
        closeModal();
    }
}

// close modal when escape key is pressed
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});


// this runs when user drags a file over the upload zone
function uploadDragOver(e) {
    e.preventDefault();
    document.getElementById('uploadZone').classList.add('drag-active');
}

// remove the highlight when file leaves the zone
function uploadDragLeave() {
    document.getElementById('uploadZone').classList.remove('drag-active');
}

// this runs when file is dropped on the upload zone
function uploadDrop(e) {
    e.preventDefault();
    document.getElementById('uploadZone').classList.remove('drag-active');
    uploadFiles(e.dataTransfer.files);
}

// this runs when user picks a file with the file picker
function handleFileSelect(e) {
    uploadFiles(e.target.files);
}

// Function to upload files to the server
function uploadFiles(files) {
    if (!files || files.length === 0 || !currentUploadUrl) return;

    var status = document.getElementById('uploadStatus');
    var bar = document.getElementById('uploadProgressBar');
    var fill = document.getElementById('uploadProgressFill');
    var done = 0;
    var total = files.length;

    // show the progress bar
    bar.style.display = 'block';
    fill.style.width = '0%';

    // loop through each file and upload one by one
    var filesArray = Array.from(files);
    for (var i = 0; i < filesArray.length; i++) {
        // use a function to keep the file variable in scope
        (function(file) {
            var fd = new FormData();
            fd.append('file', file);

            // also add csrf token if it exists
            var csrfInput = document.querySelector('input[name="csrf_token"]');
            if (csrfInput != null) {
                fd.append('csrf_token', csrfInput.value);
            }

            if (status != null) {
                status.textContent = 'Uploading ' + file.name + '...';
            }

            console.log("uploading file: " + file.name);

            fetch(currentUploadUrl, { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    done++;
                    fill.style.width = ((done / total) * 100) + '%';

                    if (data.success) {
                        // add the new file to the list
                        var listEl = document.getElementById('fileList');
                        if (listEl.querySelector('div[style]') != null) {
                            listEl.innerHTML = '';
                        }

                        var row = document.createElement('div');
                        row.className = 'file-row';
                        row.innerHTML =
                            '<div class="file-icon"><i class="bi bi-file-earmark"></i></div>' +
                            '<div class="file-info">' +
                                '<div class="file-name">' + fixText(data.file.original_name) + '</div>' +
                                '<div class="file-meta">' + fixText(data.file.uploaded_by) + ' · ' + data.file.uploaded_at + ' · ' + data.file.file_size + '</div>' +
                            '</div>' +
                            '<a href="' + data.file.download_url + '" class="file-download" download>' +
                                '<i class="bi bi-download"></i> Download' +
                            '</a>';
                        listEl.appendChild(row);

                        if (status != null) {
                            status.textContent = '✓ ' + data.file.original_name + ' uploaded';
                        }
                    } else {
                        if (status != null) {
                            status.textContent = '✗ Error: ' + (data.error || 'Upload failed');
                        }
                    }

                    // hide the progress bar after all done
                    if (done === total) {
                        setTimeout(function() { bar.style.display = 'none'; }, 1400);
                    }
                })
                .catch(function() {
                    console.log("error");
                    if (status != null) {
                        status.textContent = '✗ Upload failed';
                    }
                });
        })(filesArray[i]);
    }
}


// quick upload from the card not the modal
var quickUploadTaskId = null;
var quickUploadUrl = null;

// Function to trigger file picker for quick upload
function quickUpload(taskId, uploadUrl) {
    quickUploadTaskId = taskId;
    quickUploadUrl = uploadUrl;
    var input = document.getElementById('quickUploadInput');
    if (input != null) {
        input.value = '';
        input.click();
    }
}

// this runs when quick upload file is selected
function handleQuickUpload(e) {
    var files = e.target.files;
    if (!files || files.length === 0 || !quickUploadUrl) return;

    var csrfInput = document.querySelector('input[name="csrf_token"]');

    // loop through files and upload
    var filesArray = Array.from(files);
    for (var i = 0; i < filesArray.length; i++) {
        (function(file) {
            var fd = new FormData();
            fd.append('file', file);
            if (csrfInput != null) {
                fd.append('csrf_token', csrfInput.value);
            }

            console.log("quick uploading: " + file.name);

            fetch(quickUploadUrl, { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) {
                        // update the file badge on the card
                        var card = document.getElementById('task-' + quickUploadTaskId);
                        if (card != null) {
                            var badge = card.querySelector('.task-files-badge');
                            if (badge != null) {
                                var cur = parseInt(badge.textContent.replace(/\D/g, '')) || 0;
                                badge.innerHTML = '<i class="bi bi-paperclip"></i>' + (cur + 1);
                            } else {
                                var footer = card.querySelector('.task-card-footer > div:last-child');
                                if (footer != null) {
                                    var b = document.createElement('span');
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
                .catch(function() {
                    console.log("error");
                    alert("An error happened");
                });
        })(filesArray[i]);
    }
}


// scroll to the bottom of the chat area
function scrollChatBottom() {
    var el = document.getElementById('chatArea');
    if (el != null) {
        el.scrollTop = el.scrollHeight;
    }
}


// variable for the toast timer
var toastTimer = null;

// Function to show a toast message at the bottom
function showToast(msg, isError) {
    var t = document.getElementById('kanbanToast');

    // create the toast element if it doesnt exist
    if (!t) {
        t = document.createElement('div');
        t.id = 'kanbanToast';
        document.body.appendChild(t);
    }

    t.textContent = msg;

    // change color depending on if its an error or not
    if (isError) {
        t.style.background = 'rgba(220,53,69,0.18)';
        t.style.color = '#e07070';
        t.style.border = '1px solid rgba(220,53,69,0.3)';
    } else {
        t.style.background = 'rgba(40,167,69,0.18)';
        t.style.color = '#5fbe82';
        t.style.border = '1px solid rgba(40,167,69,0.3)';
    }

    t.style.opacity = '1';
    clearTimeout(toastTimer);
    // hide after 3 seconds
    toastTimer = setTimeout(function() { t.style.opacity = '0'; }, 3000);
}


// this fixes special characters in text so html doesnt break
function fixText(str) {
    if (!str) return '';
    var result = str;
    result = result.replace(/&/g, '&amp;');
    result = result.replace(/</g, '&lt;');
    result = result.replace(/>/g, '&gt;');
    result = result.replace(/"/g, '&quot;');
    result = result.replace(/'/g, '&#039;');
    return result;
}

// also keep old name just in case something else calls it
function escapeHtml(str) {
    return fixText(str);
}

// this starts the charts on the analytics tab
function startCharts() {
    console.log("starting charts");
    if (typeof initCharts === 'function') {
        initCharts();
    }
}
