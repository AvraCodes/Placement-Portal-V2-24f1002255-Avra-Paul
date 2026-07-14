# Step-by-Step Flow: Student Applies for a Job

This guide walks through exactly what happens (step-by-step) when a Student uses the Placement Portal. It maps the student's actions directly to the code files and functions.

---

## Step 1: Student Opens the Placement Portal Website
* **Student's Action:** The student opens `http://localhost:5001/` in the browser.
* **Backend Connection:**
  * The browser sends a `GET /` request to the backend.
  * In [app.py](file:///Users/avra/proj2mad/backend/app.py) (line 69), Flask handles this request:
    ```python
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND, 'index.html')
    ```
  * Flask sends back the file [index.html](file:///Users/avra/proj2mad/frontend/index.html).
* **Browser Action:**
  * The browser loads `index.html`.
  * It downloads the Bootstrap stylesheet, Chart.js, and the Vue 3 framework.
  * It then reads and executes the JavaScript files in order:
    1. `api.js` — Defines the global `store` (for login token storage) and the API request helper functions.
    2. `login.js`, `register.js`, `admin.js`, `company.js`, `student.js` — Load the templates and components for each dashboard view.
    3. `app.js` — Creates the Vue instance, binds it to `<div id="app"></div>`, and displays the Login screen.

---

## Step 2: Student Registers a New Account
* **Student's Action:** The student clicks "Register", selects "Student", fills in their name, username, email, CGPA, graduation year, and password, and clicks "Register".
* **Frontend Flow:**
  * In [register.js](file:///Users/avra/proj2mad/frontend/src/views/register.js), Vue intercepts the form submission and triggers `handleRegister()`.
  * `handleRegister()` calls the global helper function `apiRegister(data)` defined in [api.js](file:///Users/avra/proj2mad/frontend/src/api.js).
  * `apiRegister` makes a POST request to `/api/auth/register` carrying the student's input.
* **Backend Flow:**
  * In [auth.py](file:///Users/avra/proj2mad/backend/routes/auth.py) (line 40), Flask receives the request at `/api/auth/register`.
  * It hashes the password: `generate_password_hash(password)`.
  * It inserts a base credentials row into the `User` table and a profile record in the `StudentProfile` table in the database.
  * It responds with a success message.
  * The frontend receives the success response and redirects the student to the Login screen.

---

## Step 3: Student Logs In
* **Student's Action:** The student types in their username/password and clicks "Sign In".
* **Frontend Flow:**
  * In [login.js](file:///Users/avra/proj2mad/frontend/src/views/login.js), Vue triggers `handleLogin()`.
  * It calls `apiLogin(username, password)` in [api.js](file:///Users/avra/proj2mad/frontend/src/api.js).
  * `api.js` issues a POST request to the backend: `/api/auth/login`.
* **Backend Flow:**
  * In [auth.py](file:///Users/avra/proj2mad/backend/routes/auth.py) (line 11), Flask receives the request.
  * It queries the `User` table for the matching username and validates the password hash: `check_password_hash()`.
  * If valid, it generates a JWT string token: `create_access_token(identity=user.id)`.
  * It responds to the browser with the token: `{"token": "eyJ...", "user": {"id": 1, "role": "student", ...}}`.
* **Frontend Flow:**
  * The frontend receives the response.
  * It calls `setAuth(token, user)` inside [api.js](file:///Users/avra/proj2mad/frontend/src/api.js) which stores the token in `localStorage` so the session survives page reloads.
  * In [app.js](file:///Users/avra/proj2mad/frontend/src/app.js), the root component updates its reactive state: `this.page = 'student'`.
  * Vue immediately hides the login page and renders [student.js](file:///Users/avra/proj2mad/frontend/src/views/student.js) (the Student Dashboard).

---

## Step 4: Student Views Available Placement Drives
* **Student's Action:** The student opens the "Drives" tab on their dashboard.
* **Frontend Flow:**
  * In [student.js](file:///Users/avra/proj2mad/frontend/src/views/student.js), Vue triggers the `loadDrives()` method.
  * `loadDrives()` calls `studentGetDrives()` in [api.js](file:///Users/avra/proj2mad/frontend/src/api.js).
  * `api.js` makes a GET request to `/api/student/drives`.
  * **JWT Security:** The helper function `request()` in `api.js` automatically injects the student's token:
    `Authorization: Bearer eyJ...`
* **Backend Flow:**
  * In [student.py](file:///Users/avra/proj2mad/backend/routes/student.py) (line 111), Flask receives the request.
  * `@jwt_required()` reads and validates the student's JWT token.
  * `@role_required('student')` verifies the user role is student.
  * **Redis Caching:** Flask checks if the drives list is cached in Redis:
    * **Cache Hit:** If `'approved_drives_raw'` exists, it retrieves the drives from Redis instantly.
    * **Cache Miss:** If not, it queries SQLite, saves the results to Redis for 60 seconds, and returns them.
  * For each drive, Flask calls `check_eligibility(student, drive)` (in [utils.py](file:///Users/avra/proj2mad/backend/utils.py)) to verify if the student's branch, graduation year, and CGPA match the drive criteria.
  * It returns the drives data containing `'is_eligible': True/False`.
* **Frontend Flow:**
  * [student.js](file:///Users/avra/proj2mad/frontend/src/views/student.js) receives the drives array and renders them. If the student is eligible, they see a green "Apply Now" button. If ineligible, the button is disabled and tells them why.

---

## Step 5: Student Uploads a Resume
* **Student's Action:** The student goes to the "Profile" tab, selects their `resume.pdf` file, and clicks "Upload".
* **Frontend Flow:**
  * In [student.js](file:///Users/avra/proj2mad/frontend/src/views/student.js), Vue triggers `uploadResume()`.
  * It creates a `FormData` object containing the file.
  * It calls `studentUploadResume(formData)` in [api.js](file:///Users/avra/proj2mad/frontend/src/api.js).
* **Backend Flow:**
  * In [student.py](file:///Users/avra/proj2mad/backend/routes/student.py) (line 65), Flask receives the file.
  * It checks the file extension. If it's not `.pdf`, `.doc`, or `.docx`, it rejects it with a `400` error.
  * It saves the file under `backend/uploads/resume_1.pdf` (using the student's user ID to prevent naming collisions).
  * It updates the `StudentProfile` table column `resume_path` in SQLite.
  * It returns success. The student profile tab updates to show the uploaded resume.

---

## Step 6: Student Applies for a Drive
* **Student's Action:** The student clicks the green "Apply Now" button on an approved placement CS Drive.
* **Frontend Flow:**
  * In [student.js](file:///Users/avra/proj2mad/frontend/src/views/student.js), Vue triggers `applyToDrive(driveId)`.
  * It calls `studentApply(driveId)` in [api.js](file:///Users/avra/proj2mad/frontend/src/api.js).
  * `api.js` makes a POST request to `/api/student/drives/<driveId>/apply`.
* **Backend Flow:**
  * In [student.py](file:///Users/avra/proj2mad/backend/routes/student.py) (line 170), Flask receives the request.
  * **Mandatory Resume Check:** It checks if `p.resume_path` is set. If the student has no resume, it blocks the application: `return jsonify({'error': 'You must upload your resume before applying'}), 400`.
  * **Eligibility Check:** It checks if the student qualifies: `check_eligibility(p, drive)`.
  * **Duplicate Check:** It checks if they already applied.
  * If all checks pass, it inserts a new row in the `Application` database table with `status='applied'`.
  * It clears the admin dashboard cache key so stats update.
  * It returns success. The student dashboard updates to show "Already Applied".

---

## Step 7: Company HR Reviews the Application and Resume
* **HR's Action:** The company representative logs in and views their dashboard. They go to the "Applicants" tab, select the drive, and click "View" next to the student's name.
* **Frontend Flow:**
  * In [company.js](file:///Users/avra/proj2mad/frontend/src/views/company.js), Vue renders the applicants table.
  * For the student, the "Resume" column renders a link:
    `<a href="/api/student/resume/1?jwt=eyJ...">View</a>`
* **Browser Flow:**
  * When HR clicks "View", the browser opens a new tab pointing to `/api/student/resume/1?jwt=eyJ...`.
* **Backend Flow:**
  * In [student.py](file:///Users/avra/proj2mad/backend/routes/student.py) (line 95), Flask handles this request at `/api/student/resume/1`.
  * **Query String Authentication:** Flask-JWT-Extended parses `jwt=eyJ...` from the query string parameters and validates HR's identity.
  * Flask locates the file at `backend/uploads/resume_1.pdf` and streams it back to HR's browser tab using `send_file`.
