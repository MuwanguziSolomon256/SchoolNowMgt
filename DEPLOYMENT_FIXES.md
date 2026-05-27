# Deployment Fixes - Database Initialization Issues

## Problem
The app was crashing with `ProgrammingError: relation "SchoolNowMgt_school" does not exist` when accessed on Render, indicating that database migrations weren't creating tables properly or there was a race condition during initial deployment.

## Root Causes
1. **Manager Configuration Issue**: Migration 0003 was removing all managers from `CustomUser`, breaking user creation
2. **Circular Dependency**: `CustomUserManager.create_user()` was auto-creating a School, which failed when the table didn't exist
3. **No Error Handling**: Views were calling `School.objects.first()` without handling database errors during initial deployment
4. **Race Condition**: Render's health checks might hit endpoints before migrations complete

## Solutions Implemented

### 1. Fixed Migration 0003
**File**: [SchoolNowMgt/migrations/0003_alter_customuser_managers.py](SchoolNowMgt/migrations/0003_alter_customuser_managers.py)
- Restored `CustomUserManager` to the migration operations
- Now properly maintains the custom manager after migration

### 2. Updated CustomUserManager
**File**: [SchoolNowMgt/models.py](SchoolNowMgt/models.py)
- Removed auto-creation of default School in `create_user()`
- Now requires explicit School parameter, avoiding database access during migrations

### 3. Created Management Command
**File**: [SchoolNowMgt/management/commands/ensure_default_school.py](SchoolNowMgt/management/commands/ensure_default_school.py)
- Safely creates a default School after migrations complete
- Includes comprehensive error handling and logging
- Only runs if database table exists (checked with try-except)

### 4. Added Defensive View Functions
**Files**: 
- [SchoolNowMgt/views.py](SchoolNowMgt/views.py)
- [SchoolNowMgt/registration/views.py](SchoolNowMgt/registration/views.py)

Added `get_school_safe()` helper function that:
- Catches `ProgrammingError` if table doesn't exist
- Returns `None` instead of crashing
- Allows views to render with partial data during initialization

Updated all views using School to use `get_school_safe()` instead of `School.objects.first()`:
- `home()` 
- `enquiry_form()`
- `register_teacher()`
- `register_admin()`
- `register_non_teaching_staff()`
- `register_parent()`

### 5. Improved Deployment Configuration
**File**: [render.yaml](render.yaml)
- Added step-by-step deployment logging
- Increased Gunicorn timeout to 120 seconds for slow database connections
- Added proper error handling in startup sequence
- Creates staticfiles directory during build
- Disconnects from database after each command (CONN_MAX_AGE: 0) to avoid stale connections

### 6. Enhanced Database Settings
**File**: [schoolmgmt_project/settings/prod.py](schoolmgmt_project/settings/prod.py)
- Added connection timeout settings (10 seconds)
- Set CONN_MAX_AGE to 0 to prevent connection pooling issues on Render
- Better handling of ephemeral connections

### 7. Added Health Check Endpoint
**File**: [schoolmgmt_project/urls.py](schoolmgmt_project/urls.py)
- Added `/health/` endpoint that doesn't access database
- Allows Render to verify deployment status without triggering database queries
- Can be used for monitoring and health checks

### 8. Updated Deployment Scripts
**Files**: [Procfile](Procfile), [startup.sh](startup.sh)
- Updated to include `ensure_default_school` command
- Better error handling in bash script

## Templates Already Handle None School
**Files**: 
- [SchoolNowMgt/templates/SchoolNowMgt/home.html](SchoolNowMgt/templates/SchoolNowMgt/home.html)
- Registration templates and others

All templates already use `{% if school %}` checks, so they gracefully handle `None` values.

## Deployment Process
The new startup sequence is:
1. ✓ Build phase: Install dependencies, collect static files, create staticfiles dir
2. ✓ Migration phase: Run `python manage.py migrate --no-input`
3. ✓ Initialization: Run `python manage.py ensure_default_school`
4. ✓ Data loading: Load `data.json` if available
5. ✓ Server startup: Start Gunicorn with 120-second timeout

## Testing Locally
To test the fixes locally:

```bash
# Create a fresh database
python manage.py migrate --no-input

# Create default school
python manage.py ensure_default_school

# Run the server
python manage.py runserver
```

## Next Deployment Steps
1. Commit all changes
2. Push to your git repository
3. Render will automatically rebuild and deploy
4. Monitor the deployment logs at https://dashboard.render.com
5. Once deployed, visit https://schoolnowmgt.onrender.com/health/ to verify
6. Then visit https://schoolnowmgt.onrender.com to see the homepage

## Additional Notes
- The health check endpoint (`/health/`) is useful for monitoring
- All defensive error handling allows the app to fail gracefully if database isn't available
- The default school is created with registration_number `DEFAULT-001`
- No data is lost when redeploying - the database persists on Render

## Static Files Fix (Phase 2)

After fixing the database issue, static files were returning 404 errors. This was due to storage backend incompatibility with Render's ephemeral filesystem.

### Changes Made:

**File**: [schoolmgmt_project/settings/base.py](schoolmgmt_project/settings/base.py)
- Changed from `CompressedManifestStaticFilesStorage` to standard `StaticFilesStorage`
- Added `STATICFILES_FINDERS` configuration
- Manifest-based storage doesn't work well on ephemeral filesystems

**File**: [schoolmgmt_project/settings/prod.py](schoolmgmt_project/settings/prod.py)
- Added WhiteNoise configuration:
  - `WHITENOISE_AUTOREFRESH = False` (disabled for production)
  - `WHITENOISE_USE_FINDERS = True` (uses Django's static file finders)
  - WhiteNoise handles compression on-the-fly

**File**: [render.yaml](render.yaml)
- Improved build process with better logging
- Removed pre-creating staticfiles directory (let collectstatic handle it)
- Added verification step to confirm files were collected
- Better error handling and debugging output

### How It Works Now:

1. **Build Phase**: `python manage.py collectstatic --noinput --clear --verbosity 2` collects all Django static files
2. **Server Runtime**: WhiteNoise middleware serves the collected static files directly from disk
3. **Compression**: WhiteNoise compresses files on-the-fly (no need for manifest)
4. **Efficiency**: Much lighter than manifest-based storage

### Testing Locally:

The fix was validated by running collectstatic locally:
```bash
python manage.py collectstatic --noinput --clear --verbosity 2
# Result: 130 static files collected successfully
```

All admin CSS/JavaScript files are properly collected and will be served by WhiteNoise.
