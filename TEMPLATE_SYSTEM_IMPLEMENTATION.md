# Template System Implementation

## Overview
This document describes the complete implementation of the template system for the case management application. The system allows risk officers to assign cases with optional templates to "others" users, who can then fill out the templates and submit them for supervisor approval.

## Database Schema

### 1. Templates Table
```sql
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    questions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Unique identifier for the template
- `name`: Human-readable name of the template
- `description`: Detailed description of what the template is for
- `questions`: JSON array containing all questions and their configurations
- `is_active`: Whether the template is available for use
- `created_at`/`updated_at`: Timestamps for audit trail

### 2. Template Responses Table
```sql
CREATE TABLE template_responses (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES case_main(case_id) ON DELETE CASCADE,
    template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    assigned_to VARCHAR(50) NOT NULL,
    responses JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending_approval',
    department VARCHAR(100),
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Unique identifier for the response
- `case_id`: Reference to the case this response belongs to
- `template_id`: Reference to the template used
- `assigned_to`: Username of the user who filled the template
- `responses`: JSON object containing all question responses
- `status`: Current status (pending_approval, approved, rejected)
- `department`: Department for approval workflow
- `approved_by`: Username of supervisor who approved/rejected
- `approved_at`: Timestamp of approval/rejection
- `rejection_reason`: Reason if rejected
- `created_at`/`updated_at`: Timestamps for audit trail

### 3. Updated Assignment Table
```sql
ALTER TABLE assignment ADD COLUMN template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL;
```

**New Field:**
- `template_id`: Optional reference to a template when assigning a case

## Question Types Supported

### 1. Radio Buttons
```json
{
    "id": "visit_verification",
    "type": "radio",
    "question": "Did you visit the customer's house?",
    "required": true,
    "options": ["Yes", "No"],
    "help_text": "Please confirm if you physically visited the customer's residence"
}
```

### 2. Text Input
```json
{
    "id": "customer_name",
    "type": "text",
    "question": "What is the customer's name?",
    "required": true,
    "help_text": "Enter the full name as it appears on official documents"
}
```

### 3. Textarea
```json
{
    "id": "details",
    "type": "textarea",
    "question": "Provide additional details",
    "required": false,
    "max_length": 500,
    "help_text": "Describe any additional information relevant to this case"
}
```

### 4. Number Input
```json
{
    "id": "income_amount",
    "type": "number",
    "question": "What is the monthly income?",
    "required": false,
    "min_value": 0,
    "max_value": 1000000,
    "help_text": "Enter the monthly income amount in INR"
}
```

### 5. Date Input
```json
{
    "id": "visit_date",
    "type": "date",
    "question": "When did you visit?",
    "required": true,
    "help_text": "Select the date of your visit"
}
```

### 6. File Upload
```json
{
    "id": "supporting_documents",
    "type": "file_upload",
    "question": "Upload supporting documents",
    "required": false,
    "allowed_types": ["image/*", "application/pdf"],
    "max_size_mb": 10,
    "help_text": "Upload photos, receipts, or other relevant documents"
}
```

## API Endpoints

### 1. Template Management
- `GET /api/templates` - Get all active templates
- `GET /api/templates/{template_id}` - Get specific template
- `POST /api/templates` - Create new template

### 2. Template Responses
- `POST /api/template-responses` - Create template response
- `GET /api/case/{case_id}/template-responses` - Get all responses for a case
- `PUT /api/template-responses/{response_id}/approve` - Approve response (supervisor only)
- `PUT /api/template-responses/{response_id}/reject` - Reject response (supervisor only)

### 3. Updated Assignment Endpoint
- `POST /api/case/{ack_no}/assign` - Now supports optional template_id parameter

## Frontend Implementation

### 1. Template Selection in Assignment
Risk officers can now select an optional template when assigning cases:
- Template dropdown appears in the assignment section
- Template description is displayed when selected
- Template ID is sent with the assignment request

### 2. Template Display for "Others" Users
When a user with role "others" accesses a case with an assigned template:
- Template questions are displayed in the analysis section
- Different input types are rendered appropriately
- Users can fill out responses and save them
- File uploads are supported for file_upload questions

### 3. Template Response Management
- Responses are saved to the database
- Status tracking (pending_approval, approved, rejected)
- Integration with existing approval workflow

## Workflow Integration

### 1. Assignment Flow
1. Risk officer assigns case to user with optional template
2. Assignment record includes template_id if provided
3. "Others" user sees template questions when accessing the case

### 2. Response Flow
1. "Others" user fills out template and saves responses
2. Template responses are stored with status "pending_approval"
3. When user sends back case, template responses are marked pending

### 3. Approval Flow
1. Supervisor receives case for approval
2. Can approve/reject both case changes and template responses
3. If approved: case routes back to risk officer with approved changes
4. If rejected: case routes back to "others" user for revision

### 4. Review Flow
1. Risk officer can view approved template responses
2. Template responses are integrated into case data
3. Risk officer can see all completed template information

## Sample Templates

The system includes three sample templates:

1. **Customer Visit Verification** - For verifying customer visit details
2. **Financial Assessment** - For assessing customer's financial situation
3. **Document Verification** - For verifying customer documents and identity

## Security and Access Control

- Only authenticated users can access templates
- Template responses are tied to specific cases and users
- Only supervisors can approve/reject template responses
- Template responses follow the same approval workflow as other case changes

## Future Enhancements

The system is designed to be flexible and extensible:
- New question types can be easily added
- Template validation rules can be enhanced
- Template versioning can be implemented
- Template analytics and reporting can be added
- Template sharing across departments can be enabled

## Usage Examples

### Creating a Template Assignment
```javascript
// Risk officer assigning case with template
const assignmentData = {
  assigned_to_employee: "user123",
  comment: "Please complete the customer verification template",
  template_id: 1
};

await axios.post('/api/case/ACK123/assign', assignmentData);
```

### Filling Template Responses
```javascript
// "Others" user filling template
const responses = {
  visit_verification: "Yes",
  visit_date: "2024-01-15",
  customer_present: "Yes",
  financial_platform: "Yes",
  platform_details: "Customer was very supportive of the platform"
};

await axios.post('/api/template-responses', {
  case_id: 123,
  template_id: 1,
  responses: responses,
  department: "operations"
});
```

### Approving Template Responses
```javascript
// Supervisor approving responses
await axios.put('/api/template-responses/456/approve');
```

## Testing

To test the template system:

1. Run the sample templates creation script:
   ```bash
   cd backend
   python create_sample_templates.py
   ```

2. Start the backend server and test the API endpoints

3. Test the frontend by assigning cases with templates and filling out responses

4. Test the approval workflow with supervisor accounts

## Conclusion

The template system provides a flexible and extensible way to collect structured information from "others" users while maintaining the existing approval workflow. The system integrates seamlessly with the current case management functionality and provides a foundation for future enhancements.
