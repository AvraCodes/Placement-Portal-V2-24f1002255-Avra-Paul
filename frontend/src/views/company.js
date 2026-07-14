// ============================================================
// company.js - Company dashboard component
// Tabs: Profile | My Drives | Applicants
// ============================================================

var CompanyPage = {
  data: function() {
    return {
      tab: 'profile',
      profile: {},          // company profile data
      drives: [],           // list of my drives
      applicants: [],       // applicants for the selected drive
      selectedDriveId: '',  // drive selected in the Applicants tab
      // Form for creating a new drive
      showCreateForm: false,
      newDrive: {
        drive_name: '', job_title: '', job_description: '',
        eligibility_branch: '', eligibility_cgpa: '', eligibility_year: '',
        salary: '', location: '', application_deadline: ''
      },
      msg: '',
      loading: false,
      store: store          // expose global store so template can access store.username
    };
  },
  async created() {
    await this.loadProfile();
  },
  methods: {
    fmtDate: function(d) { return fmtDate(d); },
    statusClass: function(s) { return statusClass(s); },

    async setTab(t) {
      this.tab = t;
      this.msg = '';
      if (t === 'profile') await this.loadProfile();
      if (t === 'drives')  await this.loadDrives();
    },

    async loadProfile() {
      try { this.profile = await companyGetProfile(); } catch(e) {}
    },

    async loadDrives() {
      try {
        this.drives = await companyGetDrives();
        this.renderChart();
      } catch(e) {}
    },
    renderChart() {
      this.$nextTick(() => {
        var ctx = document.getElementById('companyChart');
        if (!ctx) return;
        if (window.myCompanyChart) {
          window.myCompanyChart.destroy();
        }
        var labels = this.drives.map(function(d) { return d.drive_name; });
        var counts = this.drives.map(function(d) { return d.application_count || 0; });
        window.myCompanyChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Number of Applicants',
              data: counts,
              backgroundColor: 'rgba(13, 110, 253, 0.7)',
              borderColor: '#0d6efd',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                ticks: { stepSize: 1 }
              }
            }
          }
        });
      });
    },

    // Save updated profile
    async saveProfile() {
      this.loading = true;
      try {
        await companyUpdateProfile({
          company_name: this.profile.company_name,
          hr_contact:   this.profile.hr_contact,
          website:      this.profile.website,
          industry:     this.profile.industry,
          description:  this.profile.description
        });
        this.msg = 'Profile updated successfully.';
      } catch(e) {
        this.msg = 'Error: ' + (e.error || 'update failed');
      } finally {
        this.loading = false;
      }
    },

    // Submit a new placement drive
    async createDrive() {
      this.loading = true;
      try {
        var data = Object.assign({}, this.newDrive);
        data.eligibility_cgpa = parseFloat(data.eligibility_cgpa) || 0;
        data.eligibility_year = parseInt(data.eligibility_year) || 0;
        data.salary = parseFloat(data.salary) || 0;
        await companyCreateDrive(data);
        this.msg = 'Drive created! It is pending admin approval.';
        this.showCreateForm = false;
        this.newDrive = { drive_name:'', job_title:'', job_description:'', eligibility_branch:'', eligibility_cgpa:'', eligibility_year:'', salary:'', location:'', application_deadline:'' };
        await this.loadDrives();
      } catch(e) {
        this.msg = 'Error: ' + (e.error || 'create failed');
      } finally {
        this.loading = false;
      }
    },
    // Load applicants for a selected drive
    async loadApplicants() {
      if (!this.selectedDriveId) return;
      try {
        var res = await companyGetApplicants(this.selectedDriveId);
        this.applicants = res.applications || [];
      } catch(e) {
        this.applicants = [];
      }
    },
    // Update application status (shortlist / select / reject)
    async updateStatus(appId, status) {
      try {
        await companyUpdateStatus(appId, status);
        this.msg = 'Status updated to ' + status + '.';
        await this.loadApplicants();
      } catch(e) {
        this.msg = 'Error: ' + (e.error || 'update failed');
      }
    },

    async closeDrive(id) {
      if (!confirm('Close this drive? Students will no longer be able to apply.')) return;
      try {
        await companyCloseDrive(id);
        this.msg = 'Drive closed.';
        await this.loadDrives();
      } catch(e) {
        this.msg = 'Error: ' + (e.error || 'close failed');
      }
    }
  },
  template: `
    <div>
      <!-- Navbar -->
      <nav class="navbar navbar-expand navbar-light bg-white border-bottom px-4">
        <span class="navbar-brand fw-bold text-primary me-4">
          <i class="bi bi-building me-1"></i>Company Portal
        </span>
        <ul class="navbar-nav me-auto gap-1">
          <li class="nav-item" v-for="t in ['profile','drives','applicants']" :key="t">
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

        <!-- ===== PROFILE TAB ===== -->
        <div v-if="tab === 'profile'">
          <h5 class="mb-3">Company Profile</h5>
          <!-- Show pending approval notice -->
          <div v-if="profile.approval_status === 'pending'" class="alert alert-warning small">
            <i class="bi bi-clock me-1"></i>
            Your company is pending admin approval. You cannot create drives until approved.
          </div>
          <div v-if="profile.approval_status === 'rejected'" class="alert alert-danger small">
            Your company registration was rejected. Please contact the institute admin.
          </div>

          <div class="card" style="max-width:600px;">
            <div class="card-body">
              <div class="row g-3">
                <div class="col-12">
                  <label class="form-label">Company Name</label>
                  <input type="text" class="form-control form-control-sm" v-model="profile.company_name">
                </div>
                <div class="col-6">
                  <label class="form-label">HR Contact</label>
                  <input type="text" class="form-control form-control-sm" v-model="profile.hr_contact">
                </div>
                <div class="col-6">
                  <label class="form-label">Industry</label>
                  <input type="text" class="form-control form-control-sm" v-model="profile.industry">
                </div>
                <div class="col-12">
                  <label class="form-label">Website</label>
                  <input type="url" class="form-control form-control-sm" v-model="profile.website">
                </div>
                <div class="col-12">
                  <label class="form-label">Description</label>
                  <textarea class="form-control form-control-sm" v-model="profile.description" rows="3"></textarea>
                </div>
              </div>
              <button class="btn btn-primary btn-sm mt-3" @click="saveProfile" :disabled="loading">
                {{ loading ? 'Saving...' : 'Save Profile' }}
              </button>
            </div>
          </div>
        </div>

        <!-- ===== DRIVES TAB ===== -->
        <div v-if="tab === 'drives'">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">My Placement Drives</h5>
            <button class="btn btn-sm btn-primary" @click="showCreateForm = !showCreateForm">
              <i class="bi bi-plus-lg me-1"></i>Create Drive
            </button>
          </div>

          <!-- Create Drive Form -->
          <div v-if="showCreateForm" class="card mb-3">
            <div class="card-header">New Placement Drive</div>
            <div class="card-body">
              <div class="row g-2">
                <div class="col-6">
                  <label class="form-label">Drive Name</label>
                  <input type="text" class="form-control form-control-sm" v-model="newDrive.drive_name" required>
                </div>
                <div class="col-6">
                  <label class="form-label">Job Title</label>
                  <input type="text" class="form-control form-control-sm" v-model="newDrive.job_title" required>
                </div>
                <div class="col-12">
                  <label class="form-label">Job Description</label>
                  <textarea class="form-control form-control-sm" v-model="newDrive.job_description" rows="2"></textarea>
                </div>
                <div class="col-4">
                  <label class="form-label">Branch (e.g. CS,ECE)</label>
                  <input type="text" class="form-control form-control-sm" v-model="newDrive.eligibility_branch">
                </div>
                <div class="col-4">
                  <label class="form-label">Min CGPA</label>
                  <input type="number" class="form-control form-control-sm" v-model="newDrive.eligibility_cgpa" min="0" max="10" step="0.1">
                </div>
                <div class="col-4">
                  <label class="form-label">Grad Year</label>
                  <input type="number" class="form-control form-control-sm" v-model="newDrive.eligibility_year" min="2020">
                </div>
                <div class="col-4">
                  <label class="form-label">Salary (LPA)</label>
                  <input type="number" class="form-control form-control-sm" v-model="newDrive.salary">
                </div>
                <div class="col-4">
                  <label class="form-label">Location</label>
                  <input type="text" class="form-control form-control-sm" v-model="newDrive.location">
                </div>
                <div class="col-4">
                  <label class="form-label">Deadline</label>
                  <input type="date" class="form-control form-control-sm" v-model="newDrive.application_deadline">
                </div>
              </div>
              <div class="mt-2">
                <button class="btn btn-sm btn-success me-2" @click="createDrive" :disabled="loading">Submit</button>
                <button class="btn btn-sm btn-secondary" @click="showCreateForm = false">Cancel</button>
              </div>
            </div>
          </div>

          <!-- Drives List -->
          <div class="table-responsive">
            <table class="table table-bordered table-sm">
              <thead class="table-light">
                <tr><th>Drive</th><th>Job</th><th>Deadline</th><th>Applicants</th><th>Status</th><th>Action</th></tr>
              </thead>
              <tbody>
                <tr v-if="drives.length === 0">
                  <td colspan="6" class="text-center text-muted">No drives created yet.</td>
                </tr>
                <tr v-for="d in drives" :key="d.id">
                  <td>{{ d.drive_name }}</td>
                  <td>{{ d.job_title }}</td>
                  <td>{{ fmtDate(d.application_deadline) }}</td>
                  <td>{{ d.application_count || 0 }}</td>
                  <td><span :class="statusClass(d.status)">{{ d.status }}</span></td>
                  <td>
                    <button v-if="d.status === 'approved'" class="btn btn-sm btn-outline-secondary"
                            @click="closeDrive(d.id)">Close</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Chart.js Analytics Panel -->
          <div class="card mt-4" v-if="drives.length">
            <div class="card-header bg-white fw-bold"><i class="bi bi-bar-chart-line-fill me-1"></i>Applicants per Placement Drive</div>
            <div class="card-body" style="position: relative; height: 300px;">
              <canvas id="companyChart"></canvas>
            </div>
          </div>

        </div>
        <!-- ===== APPLICANTS TAB ===== -->
        <div v-if="tab === 'applicants'">
          <h5 class="mb-3">View Applicants</h5>
          <div class="d-flex gap-2 mb-3">
            <select class="form-select form-select-sm" style="max-width:300px;"
                    v-model="selectedDriveId" @change="loadApplicants">
              <option value="">-- Select a drive --</option>
              <option v-for="d in drives" :key="d.id" :value="d.id">{{ d.drive_name }}</option>
            </select>
            <button class="btn btn-sm btn-secondary" @click="loadDrives(); loadApplicants()">Refresh</button>
          </div>
          <div class="table-responsive">
            <table class="table table-bordered table-sm" v-if="applicants.length">
              <thead class="table-light">
                <tr><th>Student</th><th>Branch</th><th>CGPA</th><th>Email</th><th>Applied</th><th>Resume</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                <tr v-for="a in applicants" :key="a.id">
                  <td>{{ a.student_name }}</td>
                  <td>{{ a.student_branch }}</td>
                  <td>{{ a.student_cgpa }}</td>
                  <td>{{ a.student_email }}</td>
                  <td>{{ fmtDate(a.application_date) }}</td>
                  <td>
                    <a v-if="a.resume_path" :href="'/api/student/resume/' + a.student_id" target="_blank" class="btn btn-xs btn-sm btn-outline-primary py-0">
                      <i class="bi bi-file-earmark-pdf me-1"></i>View
                    </a>
                    <span v-else class="text-muted small">No Resume</span>
                  </td>
                  <td><span :class="statusClass(a.status)">{{ a.status }}</span></td>
                  <td class="text-nowrap">
                    <button class="btn btn-xs btn-sm btn-outline-info me-1"    @click="updateStatus(a.id, 'shortlisted')">Shortlist</button>
                    <button class="btn btn-xs btn-sm btn-outline-success me-1" @click="updateStatus(a.id, 'selected')">Select</button>
                    <button class="btn btn-xs btn-sm btn-outline-danger"       @click="updateStatus(a.id, 'rejected')">Reject</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-else class="text-muted small">Select a drive above to see applicants.</p>
          </div>
        </div>

      </div>
    </div>
  `
};
