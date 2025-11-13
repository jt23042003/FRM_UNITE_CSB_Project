# Generic Department Setup Guide

## Overview

The system is now **fully generic** and works for any department/branch without hardcoded names. The design follows:

- **1 Supervisor per Department/Branch**
- **Multiple Branch Users (2-3) per Department**
- **When branch users send back, only their department's supervisor receives the case**
- **No hardcoded department names** - works for Finance, Compliance, and any future departments

---

## How It Works

### Current Architecture

```
Department/Branch Structure:
├── Finance Department
│   ├── Supervisor: finance_supervisor (user_type='supervisor', dept='Finance')
│   ├── Branch User 1: finance_user1 (user_type='others', dept='Finance')
│   ├── Branch User 2: finance_user2 (user_type='others', dept='Finance')
│   └── Branch User 3: finance_user3 (user_type='others', dept='Finance')
│
├── Compliance Department
│   ├── Supervisor: compliance_supervisor (user_type='supervisor', dept='Compliance')
│   ├── Branch User 1: compliance_user1 (user_type='others', dept='Compliance')
│   └── Branch User 2: compliance_user2 (user_type='others', dept='Compliance')
│
└── New Department (e.g., Operations)
    ├── Supervisor: ops_supervisor (user_type='supervisor', dept='Operations')
    └── Branch Users: ops_user1, ops_user2, etc.
```

### Workflow

1. **Risk Officer** assigns case to **Branch User** (e.g., `finance_user1`)
2. **Branch User** works on case and clicks "Send Back"
3. **System automatically finds** the supervisor for that branch user's department (`Finance`)
4. **Only that department's supervisor** receives the case (`finance_supervisor`)
5. **Supervisor** approves/rejects and routes back to **Risk Officer**

---

## Adding New Departments/Branches

### Step 1: Add Supervisor

```sql
INSERT INTO user_table (user_id, user_name, user_type, dept) 
VALUES ('sup_ops_001', 'ops_supervisor', 'supervisor', 'Operations');
```

### Step 2: Add Branch Users

```sql
INSERT INTO user_table (user_id, user_name, user_type, dept) 
VALUES 
    ('ops_user_001', 'ops_user1', 'others', 'Operations'),
    ('ops_user_002', 'ops_user2', 'others', 'Operations'),
    ('ops_user_003', 'ops_user3', 'others', 'Operations');
```

### Step 3: That's It!

The system automatically:
- ✅ Routes cases from `ops_user1`, `ops_user2`, `ops_user3` to `ops_supervisor`
- ✅ Uses generic threshold (3 days) for delayed cases
- ✅ Works exactly like Finance and Compliance departments
- ✅ **No code changes needed**

---

## Key Features

### ✅ Generic Department Handling

- **No hardcoded department names** in code
- All departments use the same logic
- Adding new departments requires only database inserts

### ✅ 1 Supervisor Per Department

- Each department has exactly 1 supervisor
- Supervisor lookup is automatic based on `dept` column
- Works generically for any department name

### ✅ Automatic Supervisor Assignment

When a branch user sends back a case:
1. System gets the branch user's `dept` from `user_table`
2. Finds supervisor where `user_type='supervisor'` AND `dept` matches
3. Routes case to that supervisor
4. **Only that department's supervisor** receives it

---

## Example: Adding "Legal" Department

```sql
-- 1. Add Legal Supervisor
INSERT INTO user_table (user_id, user_name, user_type, dept) 
VALUES ('legal_sup_001', 'legal_supervisor', 'supervisor', 'Legal');

-- 2. Add Legal Branch Users
INSERT INTO user_table (user_id, user_name, user_type, dept) 
VALUES 
    ('legal_user_001', 'legal_user1', 'others', 'Legal'),
    ('legal_user_002', 'legal_user2', 'others', 'Legal');

-- 3. Done! System automatically works for Legal department
```

**Result**:
- Risk Officer assigns case to `legal_user1`
- `legal_user1` sends back → goes to `legal_supervisor`
- `legal_supervisor` approves/rejects → goes back to Risk Officer
- **No code changes needed!**

---

## Configuration

### Default Thresholds

All departments use the same default threshold:
- **Delayed Cases Threshold**: 3 days (for supervisors)
- **Risk Officer Threshold**: 5 days (for super users)

These are configurable in `backend/config.py` but apply generically to all departments.

---

## Verification

### Check Supervisor Assignment

```sql
-- Verify supervisor exists for department
SELECT user_name, user_type, dept 
FROM user_table 
WHERE user_type = 'supervisor' AND dept = 'Finance';
```

### Check Branch Users

```sql
-- Verify branch users exist for department
SELECT user_name, user_type, dept 
FROM user_table 
WHERE user_type = 'others' AND dept = 'Finance';
```

### Test Workflow

1. Risk Officer assigns case to branch user
2. Branch user sends back
3. Check assignment table - should show supervisor as `assigned_to`
4. Supervisor approves/rejects
5. Check assignment table - should show risk officer as `assigned_to`

---

## Troubleshooting

### Issue: "No supervisor found for department X"

**Solution**: Ensure supervisor exists with correct `dept` value:
```sql
SELECT * FROM user_table 
WHERE user_type = 'supervisor' AND dept = 'X';
```

### Issue: Case not routing to supervisor

**Solution**: Check branch user's department:
```sql
SELECT dept FROM user_table WHERE user_name = 'branch_user_name';
```

### Issue: Multiple supervisors for same department

**Solution**: System uses `ORDER BY user_id LIMIT 1`, so it will pick one. 
**Best Practice**: Ensure only 1 supervisor per department (as per design).

---

## Summary

✅ **System is fully generic** - no hardcoded department names
✅ **1 supervisor per department** - correctly implemented
✅ **Works for any department** - just add users to database
✅ **No code changes needed** - when adding new departments
✅ **Scalable** - handles unlimited departments and users

The system is ready for production use with Finance, Compliance, and any future departments!

