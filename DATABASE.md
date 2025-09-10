# Database Management

This document describes how to manage the database for the MrNoble application.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/mrnoble"
```

### 3. Initialize Alembic (First Time Only)

```bash
python migrate.py init
```

## Migration Commands

### Create a New Migration

```bash
python migrate.py create "Add new feature"
```

This will:
- Analyze the current models
- Generate a migration file with the changes
- Place it in `alembic/versions/`

### Apply Migrations

```bash
python migrate.py upgrade
```

This will apply all pending migrations to the database.

### Rollback Migrations

```bash
python migrate.py downgrade
```

This will rollback the last migration.

### View Migration History

```bash
python migrate.py history
```

### Check Current Revision

```bash
python migrate.py current
```

## Development Workflow

1. **Make model changes** in `app/models.py`
2. **Create migration**: `python migrate.py create "Description of changes"`
3. **Review the generated migration** in `alembic/versions/`
4. **Apply migration**: `python migrate.py upgrade`
5. **Test your changes**

## Production Deployment

1. **Set production DATABASE_URL**
2. **Run migrations**: `python migrate.py upgrade`
3. **Verify**: `python migrate.py current`

## Migration Best Practices

- Always review auto-generated migrations before applying
- Test migrations on a copy of production data
- Keep migrations small and focused
- Use descriptive migration messages
- Never edit applied migrations

## Troubleshooting

### Migration Conflicts

If you have migration conflicts:

1. Check current state: `python migrate.py current`
2. View history: `python migrate.py history`
3. Resolve conflicts manually in migration files
4. Apply: `python migrate.py upgrade`

### Database Connection Issues

- Verify DATABASE_URL is correct
- Check database server is running
- Ensure user has proper permissions
- Test connection: `python -c "from app.db import engine; print(engine.url)"`

## Schema Documentation

The database schema includes the following main tables:

- `admins` - Admin users
- `candidates` - Job candidates
- `jobs` - Job postings
- `applications` - Candidate applications
- `interview_links` - Interview scheduling
- `emails` - Email logs
- `availability_options` - Candidate availability
- `interviews` - Interview sessions
- `scores` - Interview scores
