// ============================================================
// register.js - Registration page component
// Handles both Student and Company registration in one form.
// ============================================================

var RegisterPage = {
  data: function() {
    return {
      // 'student' or 'company' - controls which fields appear
      role: 'student',
      // Common fields for all roles
      username: '',
      email: '',
      password: '',
      // Student-specific fields
      full_name: '',
      branch: '',
      cgpa: '',
      year: '',
      phone: '',
      // Company-specific fields
      company_name: '',
      hr_contact: '',
      website: '',
      industry: '',
      // UI state
      error: '',
      success: '',
      loading: false
    };
  },
  emits: ['navigate'],
  methods: {
    // Called when the registration form is submitted
    async handleRegister() {
      this.loading = true;
      this.error = '';
      this.success = '';

      // Build the request body based on selected role
      var data = {
        username: this.username,
        email: this.email,
        password: this.password,
        role: this.role
      };

      if (this.role === 'student') {
        data.full_name  = this.full_name;
        data.branch     = this.branch;
        data.cgpa       = parseFloat(this.cgpa) || 0;
        data.year       = parseInt(this.year) || 0;
        data.phone      = this.phone;
      } else {
        data.company_name = this.company_name;
        data.hr_contact   = this.hr_contact;
        data.website      = this.website;
        data.industry     = this.industry;
      }

      try {
        await apiRegister(data);
        this.success = 'Registration successful! You can now log in.';
        // Auto-redirect to login after 2 seconds
        setTimeout(() => this.$emit('navigate', 'login'), 2000);
      } catch (err) {
        this.error = err.error || 'Registration failed. Try a different username.';
      } finally {
        this.loading = false;
      }
    }
  },
  template: `
    <div class="d-flex align-items-center justify-content-center py-4" style="min-height:100vh;">
      <div style="width:100%; max-width:500px;" class="p-3">

        <div class="text-center mb-4">
          <h3><i class="bi bi-person-plus-fill text-primary"></i> Create Account</h3>
          <p class="text-muted small">Register as a student or company</p>
        </div>

        <div class="card shadow-sm">
          <div class="card-body p-4">

            <div v-if="error"   class="alert alert-danger  py-2 small">{{ error }}</div>
            <div v-if="success" class="alert alert-success py-2 small">{{ success }}</div>

            <!-- Role selector tabs -->
            <div class="mb-3">
              <div class="btn-group w-100">
                <button type="button" class="btn"
                        :class="role === 'student' ? 'btn-primary' : 'btn-outline-primary'"
                        @click="role = 'student'">
                  <i class="bi bi-person me-1"></i> Student
                </button>
                <button type="button" class="btn"
                        :class="role === 'company' ? 'btn-primary' : 'btn-outline-primary'"
                        @click="role = 'company'">
                  <i class="bi bi-building me-1"></i> Company
                </button>
              </div>
            </div>

            <form @submit.prevent="handleRegister">
              <!-- Fields common to both roles -->
              <div class="row g-2">
                <div class="col-12">
                  <label class="form-label">Username</label>
                  <input type="text" class="form-control form-control-sm" v-model="username" required>
                </div>
                <div class="col-12">
                  <label class="form-label">Email</label>
                  <input type="email" class="form-control form-control-sm" v-model="email" required>
                </div>
                <div class="col-12">
                  <label class="form-label">Password</label>
                  <input type="password" class="form-control form-control-sm" v-model="password" required minlength="6">
                </div>
              </div>

              <!-- Student-only fields -->
              <div v-if="role === 'student'" class="row g-2 mt-1">
                <div class="col-12">
                  <label class="form-label">Full Name</label>
                  <input type="text" class="form-control form-control-sm" v-model="full_name" required>
                </div>
                <div class="col-6">
                  <label class="form-label">Branch</label>
                  <select class="form-select form-select-sm" v-model="branch" required>
                    <option value="">Select branch</option>
                    <option>CS</option><option>ECE</option><option>ME</option>
                    <option>CE</option><option>IT</option><option>EE</option>
                  </select>
                </div>
                <div class="col-6">
                  <label class="form-label">CGPA</label>
                  <input type="number" class="form-control form-control-sm" v-model="cgpa"
                         min="0" max="10" step="0.01" required>
                </div>
                <div class="col-6">
                  <label class="form-label">Grad Year</label>
                  <input type="number" class="form-control form-control-sm" v-model="year"
                         min="2020" max="2030" required>
                </div>
                <div class="col-6">
                  <label class="form-label">Phone</label>
                  <input type="tel" class="form-control form-control-sm" v-model="phone">
                </div>
              </div>

              <!-- Company-only fields -->
              <div v-if="role === 'company'" class="row g-2 mt-1">
                <div class="col-12">
                  <label class="form-label">Company Name</label>
                  <input type="text" class="form-control form-control-sm" v-model="company_name" required>
                </div>
                <div class="col-6">
                  <label class="form-label">HR Contact</label>
                  <input type="text" class="form-control form-control-sm" v-model="hr_contact">
                </div>
                <div class="col-6">
                  <label class="form-label">Industry</label>
                  <input type="text" class="form-control form-control-sm" v-model="industry"
                         placeholder="e.g. IT, Finance">
                </div>
                <div class="col-12">
                  <label class="form-label">Website</label>
                  <input type="url" class="form-control form-control-sm" v-model="website"
                         placeholder="https://example.com">
                </div>
              </div>

              <button type="submit" class="btn btn-primary w-100 mt-3" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loading ? 'Registering...' : 'Register' }}
              </button>
            </form>

            <p class="text-center mt-3 mb-0 small">
              Already registered?
              <a href="#" @click.prevent="$emit('navigate', 'login')">Sign in here</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  `
};
