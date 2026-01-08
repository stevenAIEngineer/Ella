# Revised Plan: The "Zero-Cost" SQLite Strategy

## Is Railway Postgres Free?
**Not exactly.** Running a dedicated PostgreSQL service on Railway consumes "Compute Credits" (CPU/RAM). While small, it will eat into your $5.00/month trial or verified entitlement.

## The Alternative: SQLite on a Volume (Recommended)
To keep costs at **$0 extra**, we should use **SQLite** combined with a **Railway Volume**.

### How it works
1.  **SQLite:** This is a full SQL database that lives in a **single file** (e.g., `studio.db`). It doesn't need a server; it's built into Python.
2.  **Railway Volume:** We tell Railway "Please don't delete the `/data` folder when I redeploy."
3.  **Result:** You get a persistent Account system (SQL tables, Users, Passwords) without paying for a separate database service.

### Technical Changes
1.  **Database File:** We switch from `json` files to `sqlite3`.
    *   `roster.json` -> `TABLE roster`
    *   `gallery.json` -> `TABLE gallery`
    *   `users.json` -> `TABLE users` (New)
2.  **Authentication:** Same logic (bcrypt), just storing in `studio.db`.

### Why this is best for Ella Studio
*   **Cost:** Free (uses existing app resources).
*   **Speed:** Extremely fast (no network latency).
*   **Simplicity:** No connection strings or external secrets to manage.
*   **Migration:** If you ever get huge, moving SQLite to Postgres is easy.

## Action Plan
1.  **Create `db_manager.py`:** A module to handle the SQLite connection and table creation automatically.
2.  **Update `app.py`:** replace `load_data` / `save_data` with `db.get_gallery()` calls.
3.  **Add Auth:** Implement simple `register` and `login` UI using the DB.
