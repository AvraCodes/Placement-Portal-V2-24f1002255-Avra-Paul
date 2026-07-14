// ============================================================
// student.js - Student dashboard component
// Tabs: Drives | My Applications | History | Profile
// ============================================================

var StudentPage = {
  data: function() {
    return {
      tab: 'drives',
      drives: [],         // available approved drives
      applications: [],   // student's current applications
      history: [],        // student's placement history
      profile: {},        // student profile
      // Profile edit form values (separate from profile so cancel works)
      form: { full_name:'', branch:'', cgpa:'', year:'', phone:'' },
      resumeFile: null,
      msg: '',
      loading: false,
      applying: null,     // drive id currently being applied for
      store: store        // expose global store so template can access store.username
    };
  },
  async created() {
    await this.loadDrives();
  },
  methods: {
    fmtDate: function(d) { return fmtDate(d); },
    statusClass: function(s) { return statusClass(s); },

    async setTab(t) {
      this.tab = t;
      this.msg = '';
      if (t === 'drives')        await this.loadDrives();
      if (t === 'applications')  await this.loadApplications();
      if (t === 'history')       await this.loadHistory();
      if (t === 'profile')       await this.loadProfile();
    },

    async loadDrives() {
      try { this.drives = await studentGetDrives(); } catch(e) {}
    },
    async loadApplications() {
      try { this.applications = await studentGetApplications(); } catch(e) {}
    },
    async loadHistory() {
      try { this.history = await studentGetHistory(); } catch(e) {}
    },
    async loadProfile() {
      try {
        this.profile = await studentGetProfile();
        // Copy profile values into the form for editing
        this.form.full_name = this.profile.full_name || '';
        this.form.branch    = this.profile.branch || '';
        this.form.cgpa      = this.profile.cgpa || '';
        this.form.year      = this.profile.year || '';
        this.form.phone     = this.profile.phone || '';
      } catch(e) {}
    },

    // Apply to a placement drive
    async applyToDrive(driveId) {
      this.applying = driveId;
      try {
        await studentApply(driveId);
        this.msg = 'Applied successfully!';
        await this.loadDrives();
      } catch(e) {
        this.msg = 'Error: ' + (e.error || 'Could not apply');
      } finally {
        this.applying = null;
      }
    },

    // Save profile changes
    async saveProfile() {
      this.loading = true;
      try {
        await studentUpdateProfile({
          full_name: this.form.full_name,
          branch:    this.form.branch,
          cgpa:      parseFloat(this.form.cgpa) || 0,
          year:      parseInt(this.form.year) || 0,
          phone:     this.form.phone
        });
        this.msg = 'Profile updated successfully.';
        this.profile = Object.assign({}, this.profile, this.form);
      } catch(e) {
        this.msg = 'Error: ' + (e.error || 'update failed');
      } finally {
        this.loading = false;
      }
    },

    // Handle resume file selection
    onFileChange(event) {
      this.resumeFile = event.target.files[0] || null;
    },

    // Upload the selected resume file
    async uploadResume() {
      if (!this.resumeFile) { this.msg = 'Please select a PDF file first.'; return; }
      this.loading = true;
      var fd = new FormData();
      fd.append('resume', this.resumeFile);
      try {
        await studentUploadResume(fd);
        this.msg = 'Resume uploaded successfully.';
        this.resumeFile = null;
      } catch(e) {
        this.msg = 'Upload failed. Make sure the file is a PDF.';
      } finally {
        this.loading = false;
      }
    },

    // Export placement history as CSV
    async exportCSV() {
      this.loading = true;
      try {
        await studentExportCSV();
        this.msg = 'Export started! You will receive an email when it is ready.';
      } catch(e) {
        this.msg = 'Export failed: ' + (e.error || 'please try again');
      } finally {
        this.loading = false;
      }
    },

    // Check if student has already applied to a drive (by drive_id in applications)
    hasApplied(driveId) {
      return this.applications.some(function(a) { return a.drive_id === driveId; });
    }
  },
  template: `
    <div>
      <!-- Navbar -->
      <nav class="navbar navbar-expand navbar-light bg-white border-bottom px-4">
        <span class="navbar-brand fw-bold text-primary me-4">
          <i class="bi bi-mortarboard-fill me-1"></i>Student Portal
        </span>
        <ul class="navbar-nav me-auto gap-1">
          <li class="nav-item" v-for="t in ['drives','applications','history','profile']" :key="t">
            <button class="btn btn-sm" :class="tab===t?'btn-primary':'btn-outline-secondary'" @click="setTab(t)">
              {{ t.charAt(0).toUpperCase() + t.slice(1) }}
            </button>
          </li>
        </ul>
        <span class="text-muted small me-3">{{ store.username }}</span>
        <button class="btn btn-sm btn-outline-danger" @click="$emit('logout')">Logout</button>
      </nav>

      <div class="container-fluid px-4 py-3">
        <div v-if="msg" class="alert alert-info py-2 small">{{ msg }}</div>

        <!-- ===== DRIVES TAB ===== -->
        <div v-if="tab === 'drives'">
          <h5 class="mb-3">Available Placement Drives</h5>
          <div v-if="drives.length === 0" class="text-muted">No drives available at the moment.</div>
          <div class="row g-3">
            <div class="col-md-6 col-lg-4" v-for="d in drives" :key="d.id">
              <div class="card h-100">
                <div class="card-body">
                  <h6 class="card-title">{{ d.drive_name }}</h6>
                  <p class="card-text small text-muted mb-1">
                    <strong>Company:</strong> {{ d.company_name }}
                  </p>
                  <p class="card-text small text-muted mb-1">
                    <strong>Role:</strong> {{ d.job_title }}
                  </p>
                  <p class="card-text small text-muted mb-1">
                    <strong>Branches:</strong> {{ d.eligibility_branch || 'All' }}
                  </p>
                  <p class="card-text small text-muted mb-1">
                    <strong>Min CGPA:</strong> {{ d.eligibility_cgpa || 0 }}
                  </p>
                  <p class="card-text small text-muted mb-2">
                    <strong>Deadline:</strong> {{ fmtDate(d.application_deadline) }}
                  </p>
                  <div v-if="d.salary" class="badge bg-light text-dark border mb-2">
                    {{ d.salary }} LPA
                  </div>
                </div>
                <div class="card-footer bg-white">
                  <button class="btn btn-sm btn-success w-100"
                          v-if="!hasApplied(d.id)"
                          @click="applyToDrive(d.id)"
                          :disabled="applying === d.id">
                    <span v-if="applying === d.id" class="spinner-border spinner-border-sm me-1"></span>
                    Apply Now
                  </button>
                  <button class="btn btn-sm btn-secondary w-100 disabled" v-else>
                    Already Applied
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== APPLICATIONS TAB ===== -->
        <div v-if="tab === 'applications'">
          <h5 class="mb-3">My Applications</h5>
          <div class="table-responsive">
            <table class="table table-bordered table-sm">
              <thead class="table-light">
                <tr><th>Company</th><th>Drive</th><th>Job</th><th>Applied On</th><th>Status</th></tr>
              </thead>
              <tbody>
                <tr v-if="applications.length === 0">
                  <td colspan="5" class="text-center text-muted">No applications yet. Go to Drives to apply.</td>
                </tr>
                <tr v-for="a in applications" :key="a.id">
                  <td>{{ a.company_name }}</td>
                  <td>{{ a.drive_name }}</td>
                  <td>{{ a.job_title }}</td>
                  <td>{{ fmtDate(a.application_date) }}</td>
                  <td><span :class="statusClass(a.status)">{{ a.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== HISTORY TAB ===== -->
        <div v-if="tab === 'history'">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">Placement History</h5>
            <button class="btn btn-sm btn-outline-primary" @click="exportCSV" :disabled="loading">
              <i class="bi bi-download me-1"></i>
              {{ loading ? 'Exporting...' : 'Export CSV (Email)' }}
            </button>
          </div>
          <div class="table-responsive">
            <table class="table table-bordered table-sm">
              <thead class="table-light">
                <tr><th>Company</th><th>Drive</th><th>Job</th><th>Applied On</th><th>Status</th><th>Remarks</th></tr>
              </thead>
              <tbody>
                <tr v-if="history.length === 0">
                  <td colspan="6" class="text-center text-muted">No placement history yet.</td>
                </tr>
                <tr v-for="h in history" :key="h.id">
                  <td>{{ h.company_name }}</td>
                  <td>{{ h.drive_name }}</td>
                  <td>{{ h.job_title }}</td>
                  <td>{{ fmtDate(h.application_date) }}</td>
                  <td><span :class="statusClass(h.status)">{{ h.status }}</span></td>
                  <td>{{ h.remarks || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== PROFILE TAB ===== -->
        <div v-if="tab === 'profile'">
          <h5 class="mb-3">My Profile</h5>
          <div class="card mb-3" style="max-width:500px;">
            <div class="card-body">
              <div class="row g-3">
                <div class="col-12">
                  <label class="form-label">Full Name</label>
                  <input type="text" class="form-control form-control-sm" v-model="form.full_name">
                </div>
                <div class="col-6">
                  <label class="form-label">Branch</label>
                  <select class="form-select form-select-sm" v-model="form.branch">
                    <option value="">Select branch</option>
                    <option>CS</option><option>ECE</option><option>ME</option>
                    <option>CE</option><option>IT</option><option>EE</option>
                  </select>
                </div>
                <div class="col-6">
                  <label class="form-label">CGPA</label>
                  <input type="number" class="form-control form-control-sm" v-model="form.cgpa"
                         min="0" max="10" step="0.01">
                </div>
                <div class="col-6">
                  <label class="form-label">Graduation Year</label>
                  <input type="number" class="form-control form-control-sm" v-model="form.year" min="2020">
                </div>
                <div class="col-6">
                  <label class="form-label">Phone</label>
                  <input type="tel" class="form-control form-control-sm" v-model="form.phone">
                </div>
              </div>
              <button class="btn btn-primary btn-sm mt-3" @click="saveProfile" :disabled="loading">
                {{ loading ? 'Saving...' : 'Save Profile' }}
              </button>
            </div>
          </div>

          <!-- Resume Upload -->
          <div class="card" style="max-width:500px;">
            <div class="card-body">
              <h6>Upload Resume (PDF only)</h6>
              <p v-if="profile.resume_path" class="small text-muted">
                Current resume: <strong>{{ profile.resume_path }}</strong>
              </p>
              <div class="d-flex gap-2 align-items-center">
                <input type="file" class="form-control form-control-sm" accept=".pdf"
                       @change="onFileChange">
                <button class="btn btn-sm btn-outline-primary text-nowrap"
                        @click="uploadResume" :disabled="loading || !resumeFile">
                  Upload
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  `
};
