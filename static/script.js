/* ─────────────────────────────────────────────────────────────
   1. UTILITY & HELPER FUNCTIONS
   ───────────────────────────────────────────────────────────── */

// Auth & Session Management
function logout() {
    window.location.href = "/logout";
}

function confirmLogout(event) {
    if (event) event.preventDefault();
    showAppConfirm(
        'Confirm Logout',
        'Are you sure you want to log out?',
        logout,
        null,
        { confirmText: 'Logout', cancelText: 'Cancel', type: 'warning' }
    );
    return false;
}

function createToastContainer() {
    let container = document.getElementById('app-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'app-toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    container.style.display = 'flex';
    return container;
}

function showAppToast(message, type = 'error', duration = 4200) {
    const container = createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-message">${message}</div>
        <button type="button" class="toast-close" aria-label="Close">&times;</button>
    `;
    container.appendChild(toast);

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn?.addEventListener('click', () => toast.remove());

    setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, duration);
}

function showAppModal(title, message, type = 'info') {
    const modal = document.getElementById('appMessageModal');
    if (!modal) {
        if (window.confirm) {
            window.alert(message);
        } else {
            showAppToast(message, type);
        }
        return;
    }
    const titleEl = document.getElementById('app-modal-title');
    const bodyEl = document.getElementById('app-modal-body');
    const iconEl = document.getElementById('app-modal-icon');

    if (titleEl) titleEl.textContent = title;
    if (bodyEl) bodyEl.textContent = message;
    if (iconEl) {
        iconEl.className = `app-modal-icon ${type}`;
        iconEl.textContent = type === 'success' ? '✓' : type === 'error' ? '!' : 'i';
    }
    modal.style.display = 'block';
}

function closeAppModal() {
    const modal = document.getElementById('appMessageModal');
    if (modal) modal.style.display = 'none';
}

let appConfirmCallback = null;
let appConfirmCancelCallback = null;

function showAppConfirm(title, message, onConfirm, onCancel, options = {}) {
    const modal = document.getElementById('appConfirmModal');
    if (!modal) {
        if (window.confirm(message)) {
            onConfirm?.();
        } else {
            onCancel?.();
        }
        return;
    }

    const titleEl = document.getElementById('app-confirm-title');
    const bodyEl = document.getElementById('app-confirm-body');
    const iconEl = document.getElementById('app-confirm-icon');
    const okBtn = document.getElementById('app-confirm-ok-btn');
    const cancelBtn = document.getElementById('app-confirm-cancel-btn');

    if (titleEl) titleEl.textContent = title;
    if (bodyEl) bodyEl.textContent = message;
    if (iconEl) {
        iconEl.className = `app-modal-icon ${options.type || 'warning'}`;
        iconEl.textContent = options.type === 'success' ? '✓' : options.type === 'error' ? '!' : '!';
    }
    if (okBtn) okBtn.textContent = options.confirmText || 'Confirm';
    if (cancelBtn) cancelBtn.textContent = options.cancelText || 'Cancel';

    appConfirmCallback = onConfirm;
    appConfirmCancelCallback = onCancel;
    modal.style.display = 'block';
}

function closeAppConfirm() {
    const modal = document.getElementById('appConfirmModal');
    if (modal) modal.style.display = 'none';
    appConfirmCallback = null;
    appConfirmCancelCallback = null;
}

function acceptAppConfirm() {
    if (appConfirmCallback) appConfirmCallback();
    closeAppConfirm();
}

function cancelAppConfirm() {
    if (appConfirmCancelCallback) appConfirmCancelCallback();
    closeAppConfirm();
}

// Form Validation
function validateReviewerForm(event) {
    const nameInput = document.getElementById('reviewer-name');
    const emailInput = document.getElementById('reviewer-email');
    const passwordInput = document.getElementById('reviewer-password');
    const errorBox = document.getElementById('reviewer-form-error');

    if (!nameInput || !emailInput || !passwordInput) return true;

    const name = (nameInput.value || '').trim();
    const email = (emailInput.value || '').trim();
    const password = passwordInput.value || '';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    let error = '';
    if (!name) error = 'Full name is required.';
    else if (!email) error = 'Email is required.';
    else if (!emailRegex.test(email)) error = 'Please enter a valid email address.';
    else if (!password) error = 'Password is required.';
    else if (password.length < 8 || !/\d/.test(password)) {
        error = 'Password must be at least 8 characters and include at least one number.';
    }

    if (error) {
        if (event) event.preventDefault();
        if (errorBox) {
            errorBox.textContent = error;
            errorBox.style.display = 'block';
        } else {
            showAppToast(error, 'error');
        }
        return false;
    }

    if (errorBox) {
        errorBox.textContent = '';
        errorBox.style.display = 'none';
    }
    return true;
}

// User Management
function searchUser(query) {
    const rows = document.querySelectorAll('#user-table-body tr');
    const q = query.toLowerCase();
    rows.forEach(row => {
        const name = row.cells[1]?.textContent.toLowerCase() || '';
        const role = row.cells[3]?.textContent.toLowerCase() || '';
        row.style.display = (name.includes(q) || role.includes(q)) ? '' : 'none';
    });
}

async function deleteUser(userID) {
    showAppConfirm(
        'Delete User',
        'Are you sure you want to delete this user?',
        async () => {
            try {
                const response = await fetch(`/api/user/${userID}/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                if (data.success) {
                    showAppToast('User deleted successfully.', 'success');
                    location.reload();
                } else {
                    showAppToast('Error: ' + (data.error || 'Failed to delete user'), 'error');
                }
            } catch (err) {
                showAppToast('Error deleting user.', 'error');
            }
        },
        null,
        { confirmText: 'Delete', cancelText: 'Cancel', type: 'error' }
    );
}

// Navigation
function showSection(sectionId) {
    document.querySelectorAll('.content-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('section-' + sectionId).classList.add('active');
    document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
    if (window.event?.currentTarget) {
        window.event.currentTarget.classList.add('active');
    }
}

/* ─────────────────────────────────────────────────────────────
   2. MODAL HANDLERS
   ───────────────────────────────────────────────────────────── */

// Coral Info Modal (Alert-based fallback)
function openCardModal(coralID, scientificName, healthStatus, confidence, iucnStatus, regionName, growthForm, tempRange, phRange) {
    const details = [
        `Coral ID: ${coralID || 'N/A'}`,
        `Scientific Name: ${scientificName || 'N/A'}`,
        `Health Status: ${healthStatus || 'N/A'}`,
        `Confidence: ${confidence || 0}%`,
        `IUCN Status: ${iucnStatus || 'N/A'}`,
        `Region: ${regionName || 'N/A'}`,
        `Growth Form: ${growthForm || 'N/A'}`,
        `Temperature Range: ${tempRange || 'N/A'}`,
        `pH Range: ${phRange || 'N/A'}`
    ].join('\n');
    showAppModal('Coral Details', details, 'info');
}

// PDF Export
function openPdfModal() {
    const cards = Array.from(document.querySelectorAll('#edu-gallery .edu-card'))
        .filter(card => !card.classList.contains('hidden'));
    const selectedCards = cards.filter(card => card.querySelector('.edu-check')?.checked);
    const source = selectedCards.length > 0 ? selectedCards : cards;

    if (source.length === 0) {
        showAppToast('No coral entries available to export.', 'error');
        return;
    }

    const rows = source.map(card => {
        const id = card.querySelector('.coral-card-id')?.textContent?.trim() || 'N/A';
        const scientific = card.querySelector('.coral-card-genus')?.textContent?.trim() || 'N/A';
        const status = card.querySelector('.badge')?.textContent?.trim() || 'N/A';
        const iucnRaw = card.querySelector('.card-meta-label .text-amber-warn')?.textContent?.trim() || 'N/A';
        const iucn = iucnRaw.replace(/^IUCN:\s*/i, '');
        const confidence = card.querySelector('.card-meta-small')?.textContent?.trim() || 'N/A';
        return { id, scientific, status, iucn, confidence };
    });

    const now = new Date();
    const generatedAt = now.toLocaleString('en-MY', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });

    const htmlRows = rows.map((r, idx) => `
        <tr>
            <td>${idx + 1}</td>
            <td>${r.id}</td>
            <td>${r.scientific}</td>
            <td>${r.status}</td>
            <td>${r.iucn}</td>
            <td>${r.confidence}</td>
        </tr>
    `).join('');

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        showAppToast('Popup blocked. Please allow popups to download the PDF report.', 'error');
        return;
    }

    printWindow.document.write(`
        <html>
        <head>
            <title>CoralKita Educator Report</title>
            <style>
                body { font-family: Arial, sans-serif; color: #0f172a; margin: 24px; }
                h1 { margin: 0 0 8px 0; font-size: 22px; }
                .meta { margin-bottom: 16px; color: #475569; font-size: 13px; }
                table { width: 100%; border-collapse: collapse; font-size: 12px; }
                th, td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; }
                th { background: #f1f5f9; }
                .footer { margin-top: 14px; font-size: 11px; color: #64748b; }
                @page { size: A4; margin: 16mm; }
            </style>
        </head>
        <body>
            <h1>CoralKita Educator Coral Report</h1>
            <div class="meta">Generated on ${generatedAt} | Total entries: ${rows.length}</div>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Coral ID</th>
                        <th>Scientific Name</th>
                        <th>Health Status</th>
                        <th>IUCN Status</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>${htmlRows}</tbody>
            </table>
            <div class="footer">Tip: use "Save as PDF" in your browser print dialog.</div>
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => printWindow.print(), 250);
}

/* ─────────────────────────────────────────────────────────────
   3. EDUCATOR DASHBOARD - FILTERING
   ───────────────────────────────────────────────────────────── */

const eduFilterState = {
    genus: 'all',
    health: 'all'
};

function eduFilter(value, chipEl) {
    const groupGenus = ['Acropora', 'Montipora', 'Porites'];
    const groupHealth = ['Bleaching', 'Non-Bleaching'];

    if (value === 'all') {
        eduFilterState.genus = 'all';
        eduFilterState.health = 'all';
    } else if (groupGenus.includes(value)) {
        eduFilterState.genus = value;
    } else if (groupHealth.includes(value)) {
        eduFilterState.health = value;
    }

    // Update active chip styles
    const chips = document.querySelectorAll('.filter-chip');
    chips.forEach(chip => chip.classList.remove('active'));

    const allChip = document.getElementById('edu-f-all');
    if (eduFilterState.genus === 'all' && eduFilterState.health === 'all') {
        if (allChip) allChip.classList.add('active');
    } else {
        if (eduFilterState.genus !== 'all') {
            const genusChip = document.getElementById(`edu-f-${eduFilterState.genus.toLowerCase()}`);
            if (genusChip) genusChip.classList.add('active');
        }
        if (eduFilterState.health !== 'all') {
            const healthChipId = eduFilterState.health === 'Non-Bleaching' ? 'edu-f-non-bleaching' : 'edu-f-bleaching';
            const healthChip = document.getElementById(healthChipId);
            if (healthChip) healthChip.classList.add('active');
        }
    }

    // Filter cards
    const cards = document.querySelectorAll('#edu-gallery .edu-card');
    const rows = document.querySelectorAll('#edu-stats-table tbody tr');
    let visibleCount = 0;

    cards.forEach(card => {
        const genus = (card.dataset.genus || '').trim();
        const health = (card.dataset.health || '').trim();
        const genusMatch = eduFilterState.genus === 'all' || genus === eduFilterState.genus;
        const healthMatch = eduFilterState.health === 'all' || health === eduFilterState.health;
        const show = genusMatch && healthMatch;

        card.classList.toggle('hidden', !show);
        if (show) visibleCount += 1;
    });

    rows.forEach(row => {
        const genus = (row.dataset.genus || '').trim();
        const health = (row.dataset.health || '').trim();
        const genusMatch = eduFilterState.genus === 'all' || genus === eduFilterState.genus;
        const healthMatch = eduFilterState.health === 'all' || health === eduFilterState.health;
        row.style.display = (genusMatch && healthMatch) ? '' : 'none';
    });

    const countEl = document.getElementById('edu-count');
    if (countEl) countEl.textContent = `Showing ${visibleCount} entries`;
}

/* ─────────────────────────────────────────────────────────────
   4. SST MONITORING & MAPS
   ───────────────────────────────────────────────────────────── */

async function loadSSTData() {
    const sstTemp = document.getElementById('sst-temperature');
    const sstTimestamp = document.getElementById('sst-timestamp');
    const sstAlertBadge = document.getElementById('sst-alert-badge');
    const dhwTableBody = document.getElementById('dhw-table-body');

    if (!sstTemp || !dhwTableBody) return;

    const renderSST = (records, isCached = false) => {
        if (!Array.isArray(records) || records.length === 0) return;

        const sorted = records.sort((a, b) => a.regionID - b.regionID);
        window.sstData = sorted;

        const avgSST = sorted.reduce((sum, r) => sum + r.sstValue, 0) / sorted.length;
        sstTemp.textContent = avgSST.toFixed(2) + '°C';

        const now = new Date();
        const prefix = isCached ? 'Cached at ' : 'Retrieved on ';
        sstTimestamp.textContent = prefix + now.toLocaleString('en-MY', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });

        if (sstAlertBadge) {
            const hasAlert = sorted.some(r => r.alertLevel !== null);
            sstAlertBadge.style.display = hasAlert ? 'inline-block' : 'none';
        }

        dhwTableBody.innerHTML = '';
        sorted.forEach(region => {
            const statusClass = region.status === 'Alert Level 2' ? 'status-alert2'
                : region.status === 'Alert Level 1' ? 'status-alert1'
                : region.status === 'Bleaching Warning' ? 'status-warning'
                : region.status === 'Bleaching Watch' ? 'status-watch'
                : 'status-normal';
            dhwTableBody.innerHTML += `
                <tr>
                    <td>${region.regionName}</td>
                    <td>${region.daysAccumulated}</td>
                    <td>${region.dhw}</td>
                    <td><span class="status-badge ${statusClass}">${region.status}</span></td>
                </tr>`;
        });
    };

    // Check cache first
    try {
        const cachedRaw = sessionStorage.getItem('sstDataCacheV1');
        if (cachedRaw) {
            const cached = JSON.parse(cachedRaw);
            if (cached && Array.isArray(cached.data) && Date.now() - cached.savedAt < 5 * 60 * 1000) {
                renderSST(cached.data, true);
            }
        }
    } catch (err) {
        console.warn('SST cache read skipped:', err);
    }

    // Fetch fresh data
    try {
        const response = await fetch('/api/sst', { cache: 'no-store' });
        if (!response.ok) return;
        const data = await response.json();
        renderSST(data, false);

        if (Array.isArray(data) && data.length > 0) {
            sessionStorage.setItem('sstDataCacheV1', JSON.stringify({
                savedAt: Date.now(),
                data
            }));
        }
    } catch (err) {
        console.error('SST fetch error:', err);
    }
}

function getMarkerColor(sstValue, dhw = 0) {
    const hotspot = sstValue - 29.0;

    if (hotspot <= 0) {
        return '#4ade80'; // No Stress
    }

    if (hotspot < 1.0) {
        return '#facc15'; // Bleaching Watch
    }

    if (dhw <= 0) {
        return '#facc15'; // Still a watch if hotspot is above baseline but DHW has not accumulated
    }

    if (dhw < 4) {
        return '#f97316'; // Bleaching Warning
    }

    if (dhw < 8) {
        return '#ef4444'; // Alert Level 1
    }

    return '#7f1d1d'; // Alert Level 2
}

function initMap() {
    const mapContainer = document.getElementById('sst-map-container');
    if (!mapContainer) return;

    if (!window.sstData || window.sstData.length === 0) {
        setTimeout(initMap, 500);
        return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
        container: 'sst-map-container',
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [103.1198, 5.3126],
        zoom: 8
    });

    map.addControl(new mapboxgl.NavigationControl());

    window.sstData.forEach(region => {
        const color = getMarkerColor(region.sstValue, region.dhw);
        const el = document.createElement('div');
        el.style.cssText = `
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: ${color};
            border: 2px solid white;
            box-shadow: 0 0 8px ${color};
            cursor: pointer;
        `;

        const popup = new mapboxgl.Popup({
            offset: 20,
            closeButton: false,
            className: 'sst-popup'
        }).setHTML(`
            <div style="
                background: #062030;
                border: 1px solid rgba(12,184,182,0.4);
                border-radius: 8px;
                padding: 10px 14px;
                font-family: 'DM Sans', sans-serif;
                color: #f0f4f5;
                min-width: 160px;
            ">
                <div style="font-size:0.85rem; font-weight:600; margin-bottom:6px; color:#0cb8b6;">
                    ${region.regionName}
                </div>
                <div style="font-size:0.78rem; margin-bottom:3px;">
                    SST: <strong>${region.sstValue.toFixed(2)}°C</strong>
                </div>
                <div style="font-size:0.78rem; margin-bottom:3px;">
                    Corals: <strong>${region.coralCount}</strong>
                </div>
                <div style="font-size:0.78rem; margin-bottom:3px;">
                    DHW: <strong>${region.dhw} °C-weeks</strong>
                </div>
                <div style="
                    margin-top:6px;
                    font-size:0.72rem;
                    padding: 2px 8px;
                    border-radius: 10px;
                    display: inline-block;
                    background: ${color}22;
                    color: ${color};
                    border: 1px solid ${color}55;
                ">
                    ${region.status}
                </div>
            </div>
        `);

        new mapboxgl.Marker(el)
            .setLngLat([region.longitude, region.latitude])
            .setPopup(popup)
            .addTo(map);

        el.addEventListener('mouseenter', () => popup.addTo(map));
        el.addEventListener('mouseleave', () => popup.remove());
    });

    const islandSelect = document.getElementById('island');
    if (islandSelect) {
        islandSelect.addEventListener('change', function () {
            const regionID = parseInt(this.value);
            const selected = window.sstData.find(r => r.regionID === regionID);
            if (selected) {
                map.flyTo({
                    center: [selected.longitude, selected.latitude],
                    zoom: 11,
                    speed: 1.2
                });
            }
        });
    }

    window.sstMap = map;
}

/* ─────────────────────────────────────────────────────────────
   5. REVIEW ACTIONS (Approve, Reject, Health Log)
   ───────────────────────────────────────────────────────────── */

// Approve review handler
const setupApproveReview = () => {
    const approveReviewModal = document.getElementById('approveReviewModal');
    const approveIucnSelect = document.getElementById('approveIucnSelect');
    const confirmApproveBtn = document.getElementById('confirmApproveBtn');
    const closeApproveModalBtn = document.getElementById('closeApproveModalBtn');
    const cancelApproveBtn = document.getElementById('cancelApproveBtn');
    let activeApproveReviewID = null;

    const submitApprove = async (reviewID, iucnID) => {
        const response = await fetch(`/api/review/${reviewID}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ iucnID: iucnID || null })
        });
        const data = await response.json();
        if (data.success) {
            showAppToast('Review approved successfully!', 'success');
            location.reload();
            return;
        }
        showAppToast('Error: ' + (data.error || 'Failed to approve review'), 'error');
    };

    document.querySelectorAll('.btn-approve[data-review-id]').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const reviewID = this.getAttribute('data-review-id');
            const existingIucnID = this.getAttribute('data-existing-iucn-id');

            if (existingIucnID) {
                submitApprove(reviewID, existingIucnID).catch(err => {
                    console.error('Error approving review:', err);
                    showAppToast('Error approving review.', 'error');
                });
                return;
            }

            activeApproveReviewID = reviewID;
            if (approveIucnSelect) approveIucnSelect.value = '';
            if (approveReviewModal) approveReviewModal.style.display = 'block';
        });
    });

    const closeApproveModal = () => {
        if (approveReviewModal) approveReviewModal.style.display = 'none';
    };

    if (closeApproveModalBtn) closeApproveModalBtn.addEventListener('click', closeApproveModal);
    if (cancelApproveBtn) cancelApproveBtn.addEventListener('click', closeApproveModal);

    if (confirmApproveBtn) {
        confirmApproveBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (!activeApproveReviewID) {
                showAppToast('No review selected.', 'error');
                return;
            }
            try {
                await submitApprove(
                    activeApproveReviewID,
                    (approveIucnSelect?.value) ? approveIucnSelect.value : null
                );
            } catch (err) {
                console.error('Error approving review:', err);
                showAppToast('Error approving review.', 'error');
            }
        });
    }
};

// Reject review handler
const setupRejectReview = () => {
    const rejectModal = document.getElementById('rejectModal');
    const rejectReason = document.getElementById('rejectReason');
    const confirmRejectBtn = document.getElementById('confirmRejectBtn');
    const closeRejectModalBtn = document.getElementById('closeRejectModalBtn');
    const cancelRejectBtn = document.getElementById('cancelRejectBtn');
    let activeRejectReviewID = null;

    const closeRejectModal = () => {
        if (rejectModal) rejectModal.style.display = 'none';
        if (rejectReason) rejectReason.value = '';
        activeRejectReviewID = null;
    };

    document.querySelectorAll('.btn-reject').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const reviewID = btn.getAttribute('data-review-id');
            if (!reviewID) {
                showAppToast('Review ID not found.', 'error');
                return;
            }
            activeRejectReviewID = reviewID;
            if (rejectReason) rejectReason.value = '';
            if (rejectModal) rejectModal.style.display = 'block';
        });
    });

    if (closeRejectModalBtn) closeRejectModalBtn.addEventListener('click', closeRejectModal);
    if (cancelRejectBtn) cancelRejectBtn.addEventListener('click', closeRejectModal);

    if (confirmRejectBtn) {
        confirmRejectBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const reason = rejectReason?.value?.trim();
            if (!activeRejectReviewID) {
                showAppToast('Review ID not found.', 'error');
                return;
            }
            if (!reason) {
                showAppToast('Rejection reason cannot be empty.', 'error');
                return;
            }
            try {
                const response = await fetch(`/api/review/${activeRejectReviewID}/reject`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason })
                });
                const data = await response.json();
                if (data.success) {
                    showAppToast('Review rejected successfully!', 'success');
                    closeRejectModal();
                    location.reload();
                    return;
                }
                showAppToast('Error: ' + (data.error || 'Failed to reject review'), 'error');
            } catch (err) {
                console.error('Error rejecting review:', err);
                showAppToast('Error rejecting review.', 'error');
            }
        });
    }
};

// Health log handler
const setupHealthLog = () => {
    document.querySelectorAll('.btn-health-log').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const coralID = btn.getAttribute('data-coral-id');
            if (!coralID) {
                showAppToast('Coral ID not found.', 'error');
                return;
            }
            window.location.href = `/dashboard/upload_coral?prefillCoralID=${coralID}`;
        });
    });
};

// View details handler
const setupViewDetails = () => {
    document.querySelectorAll('.btn-view').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const coralID = btn.getAttribute('data-coral-id');
            if (!coralID) {
                showAppToast('Coral ID not found.', 'error');
                return;
            }
            try {
                const response = await fetch(`/api/coral/${coralID}/view`);
                const data = await response.json();
                if (data.success && data.coral) {
                    const coral = data.coral;
                    let details = `Coral ID: ${coral.coralID}\n`;
                    details += `Scientific Name: ${coral.genus} ${coral.species}\n`;
                    details += `Region: ${coral.regionName || 'N/A'}\n`;
                    details += `Growth Form: ${coral.growthFormName || 'N/A'}\n`;
                    details += `Temperature Range: ${coral.waterTempMin || 'N/A'}°C - ${coral.waterTempMax || 'N/A'}°C\n`;
                    details += `pH Range: ${coral.pHMin || 'N/A'} - ${coral.pHMax || 'N/A'}\n`;
                    details += `Submitted By: ${coral.submittedByName || 'N/A'}\n`;
                    details += `Submitted At: ${coral.submittedAt || 'N/A'}`;
                    if (coral.iucnName) details += `\nIUCN Status: ${coral.iucnName}`;
                    if (coral.reviewStatus?.toLowerCase() === 'rejected' && coral.rejectionReason) {
                        details += `\nRejection Reason: ${coral.rejectionReason}`;
                    }
                    showAppModal('Coral Details', details, 'info');
                } else {
                    showAppToast('Coral not found.', 'error');
                }
            } catch (err) {
                console.error('Error fetching coral details:', err);
                showAppToast('Error loading coral details.', 'error');
            }
        });
    });
};

/* ─────────────────────────────────────────────────────────────
   6. IMAGE UPLOAD HANDLERS
   ───────────────────────────────────────────────────────────── */

const setupImageUpload = () => {
    const uploadBtn = document.getElementById('batchUploadBtn');
    const fileInput = document.getElementById('batchFileInput');
    const uploadArea = document.getElementById('batchUploadArea');
    const preview = document.getElementById('imagePreview');

    if (!uploadBtn || !fileInput || !uploadArea) return;

    const renderPreview = (file) => {
        if (!preview || !file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `<img src="${e.target.result}" alt="Coral preview" class="coral-thumbnail" style="max-width:100%;width:220px;height:auto;">`;
        };
        reader.readAsDataURL(file);
    };

    const setSelectedFile = (file) => {
        if (!file) return;
        if (!file.type?.startsWith('image/')) {
            showAppToast('Please upload a valid image file.', 'error');
            return;
        }
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        uploadBtn.textContent = file.name;
        renderPreview(file);
    };

    uploadBtn.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('click', (e) => {
        if (e.target.id !== 'batchUploadBtn') fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadBtn.textContent = fileInput.files[0].name;
            renderPreview(fileInput.files[0]);
        } else {
            uploadBtn.textContent = 'Select Image';
            if (preview) preview.innerHTML = '';
        }
    });

    // Drag and drop handlers
    ['dragenter', 'dragover'].forEach(evt => {
        uploadArea.addEventListener(evt, (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        uploadArea.addEventListener(evt, (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });
    });

    uploadArea.addEventListener('drop', (e) => {
        const droppedFiles = e.dataTransfer?.files;
        if (droppedFiles?.length > 0) setSelectedFile(droppedFiles[0]);
    });
};

/* ─────────────────────────────────────────────────────────────
   7. PASSWORD FIELD TOGGLES
   ───────────────────────────────────────────────────────────── */

const setupPasswordToggles = () => {
    document.querySelectorAll('.show-password-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = btn.getAttribute('data-target');
            if (!targetId) return;
            const input = document.getElementById(targetId);
            if (!input) return;
            
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '⌣';
            } else {
                input.type = 'password';
                btn.textContent = '👁';
            }
        });
    });

    // Set initial icon state
    document.querySelectorAll('input[type="password"]').forEach(input => {
        const toggleBtn = input.closest('.password-field-wrap')?.querySelector('.show-password-toggle');
        if (toggleBtn) toggleBtn.textContent = '👁';
    });
};

/* ─────────────────────────────────────────────────────────────
   8. FORGOT PASSWORD HANDLER
   ───────────────────────────────────────────────────────────── */

const setupForgotPassword = () => {
    const forgotLink = document.getElementById('forgot-password-link');
    const forgotForm = document.getElementById('forgot-password-form');
    
    if (forgotLink && forgotForm) {
        forgotLink.addEventListener('click', (e) => {
            e.preventDefault();
            const isHidden = forgotForm.style.display === 'none' || forgotForm.style.display === '';
            forgotForm.style.display = isHidden ? 'block' : 'none';
            if (isHidden) forgotForm.scrollIntoView({ behavior: 'smooth' });
        });
    }
};

/* ─────────────────────────────────────────────────────────────
   9. READ MORE BUTTONS (Educator Cards)
   ───────────────────────────────────────────────────────────── */

const setupReadMoreButtons = () => {
    document.querySelectorAll('.edu-read-more').forEach(btn => {
        btn.addEventListener('click', () => {
            openCardModal(
                btn.dataset.coralId || '',
                btn.dataset.scientificName || '',
                btn.dataset.healthStatus || '',
                btn.dataset.confidence || '0',
                btn.dataset.iucnStatus || '',
                btn.dataset.regionName || '',
                btn.dataset.growthForm || '',
                btn.dataset.tempRange || '',
                btn.dataset.phRange || ''
            );
        });
    });
};

/* ─────────────────────────────────────────────────────────────
   10. CLEAR PROFILE PASSWORD FIELD
   ───────────────────────────────────────────────────────────── */

const clearProfilePasswordField = () => {
    const profilePasswordField = document.getElementById('password');
    if (profilePasswordField?.closest('.profile-form')) {
        profilePasswordField.value = '';
        setTimeout(() => { profilePasswordField.value = ''; }, 0);
    }
};

/* ─────────────────────────────────────────────────────────────
   11. SST INITIALIZATION
   ───────────────────────────────────────────────────────────── */

const initializeSST = () => {
    const hasSSTPanel = document.getElementById('sst-monitor');
    const overviewPanel = document.getElementById('section-overview');
    const shouldInitSST = hasSSTPanel || (overviewPanel?.classList.contains('active'));
    
    if (shouldInitSST) {
        loadSSTData().then(() => initMap());
    }
};

/* ─────────────────────────────────────────────────────────────
   12. DOM CONTENT LOADED - MAIN INITIALIZATION
   ───────────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
    // Setup all handlers
    setupImageUpload();
    setupPasswordToggles();
    setupForgotPassword();
    setupReadMoreButtons();
    setupApproveReview();
    setupRejectReview();
    setupHealthLog();
    setupViewDetails();
    const appModalCloseBtn = document.getElementById('closeAppMessageModalBtn');
    if (appModalCloseBtn) appModalCloseBtn.addEventListener('click', closeAppModal);

    const appConfirmCloseBtn = document.getElementById('closeAppConfirmModalBtn');
    const appConfirmOkBtn = document.getElementById('app-confirm-ok-btn');
    const appConfirmCancelBtn = document.getElementById('app-confirm-cancel-btn');
    if (appConfirmCloseBtn) appConfirmCloseBtn.addEventListener('click', cancelAppConfirm);
    if (appConfirmOkBtn) appConfirmOkBtn.addEventListener('click', acceptAppConfirm);
    if (appConfirmCancelBtn) appConfirmCancelBtn.addEventListener('click', cancelAppConfirm);

    clearProfilePasswordField();
    initializeSST();
});