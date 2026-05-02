# AI Usage Disclosure

**Course:** CS 348 — Introduction to Databases  
**Project:** Clinic Patient Management System  

---

## AI Tools Used

- **Antigravity (Google DeepMind)** — AI coding assistant used during development

## Tasks AI Assisted With

1. **Code scaffolding** — Generating initial boilerplate for Flask routes, HTML templates, and JavaScript event handlers.
2. **SQL query writing** — Drafting complex JOIN queries for reports and dropdown endpoints.
3. **CSS styling** — Creating the visual design system (color variables, layout, responsive breakpoints).
4. **Database index design** — Suggesting which indexes to create (B+tree vs Hash) based on query patterns.
5. **PostgreSQL migration** — Converting from SQLite to PostgreSQL (SERIAL keys, %s placeholders, psycopg2 driver, EXTRACT/AGE functions).
6. **Transaction implementation** — Adding explicit COMMIT/ROLLBACK blocks and SERIALIZABLE isolation for the transfer appointments feature.
7. **Documentation** — Writing code comments explaining SQL injection protection, index justifications, and isolation level choices.

## How AI Output Was Verified and Modified

1. **Code review** — All AI-generated code was reviewed line-by-line before inclusion.
2. **Testing** — The application was tested locally by running the Flask dev server, performing CRUD operations, generating reports, and verifying the transfer appointments feature.
3. **Cross-referencing documentation** — AI suggestions were verified against:
   - [PostgreSQL documentation](https://www.postgresql.org/docs/) for index types (HASH vs BTREE), isolation levels, and transaction control
   - [psycopg2 documentation](https://www.psycopg.org/docs/) for connection parameters, cursor factories, and parameterized queries
   - [Flask documentation](https://flask.palletsprojects.com/) for route definitions and request handling
   - Course slides (Indexes_slides.pdf, SQLInCode_slides.pdf, TransactionsConcurrency_slides.pdf) for correct application of database concepts
4. **Bug fixes** — Several AI-generated queries and error handling paths were manually corrected during development.
5. **Design decisions** — The choice of B+tree vs Hash indexes, isolation levels, and the migration from SQLite to PostgreSQL were guided by course material and verified against official documentation.
