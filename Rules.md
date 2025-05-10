## Email Filtering & Manipulation Rules

Your rules file must be a JSON-serializable object matching the top-level Pydantic model:

```json
  {"rules": FilterRule[]}
```

### 1. Top-Level: `Rules`

| Property | Type           | Description                                       |
| -------- | -------------- | ------------------------------------------------- |
| `rules`  | `FilterRule[]` | List of named filtering rules to apply in order.  |

### 2. `FilterRule`

| Property      | Type               | Description                                                                                   |
| ------------- | ------------------ | --------------------------------------------------------------------------------------------- |
| `name`        | `string`           | A unique identifier for this rule.                                                           |
| `conditions`  | `FilterCondition`  | The matching logic (one or many sub-conditions).                                             |
| `actions`     | `FilterAction[]`   | What to do when `conditions` evaluates to true.                                              |

### 3. `FilterCondition`

| Property    | Type                     | Description                                                                                                                           |
| ----------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `operator`  | `"ANY"` \| `"ALL"`       | `"ANY"` → match if _any_ sub-rule fires; `"ALL"` → match only if _all_ sub-rules fire.                                                 |
| `rules`     | `FilterCondition.Rule[]` | List of atomic field-predicate comparisons.                                                                                           |

#### 3.1. `FilterCondition.Rule`

| Property    | Type                                          | Description                                                                                                                                       |
| ----------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `field`     | `string`                                      | The name of an `Email` model attribute to filter on. (see below)                            |
| `predicate` | `StringFilters` \| `DatetimeFilters`          | The comparison operator to use. (see below)


##### Allowed StringFilters `predicate`
- `"Contains"`  
- `"DoesNotContain"`  
- `"Equals"`  
- `"DoesNotEqual"`

The literal value to compare against.
- **For string**:
  - any text (e.g. `"Invoice"`, `"alerts@example.com"`)

##### Supported `fields` for StringFilters
- **`from_name`:** The Name of the Sender *(May/May Not be available)*
- **`from_email`:** The Email Id of the Sender
- **`to_name`:** The Name of the Reciever *(May/May Not be available)*
- **`to_email`:** The Email Id of the Reciever
- **`subject`:** Subject of the Email
- **`body`:** Body of the Email

##### Allowed `DatetimeFilters` predicate
- `GreaterThan`  
- `LessThan`  
The literal value to compare against.  
- **For dates**: one of:  
  - Relative days: `"7d"` or `"7 days"`  
  - Relative months: `"2m"` or `"2 months"`  
  - Exact datetime string: `"2025-05-10T14:30:00"` (ISO 8601)
##### Supported `fields` for DatetimeFilters
- **`date`:** Date at which the mail was receieved (inboxes) / last updated (sent or drafts)

### 4. `FilterAction`

| Property | Type                | Description                                                                                               |
| -------- | ------------------- | --------------------------------------------------------------------------------------------------------- |
| `type`   | `EmailAction`       | What action to perform: `"mark_as_read"`, `"mark_as_unread"`, `"move_message"`                                       |
| `folder` | `MailBox` (optional) | Required only when `type: move_message`. One of: `"INBOX"`, `"TRASH"`, `"SPAM"`. Sent Items or Drafts can only be moved to trash. Emails from Inbox can be marked as spam               |

### 5. Examples

```json
{
  "rules": [
    {
      "name": "Archive old newsletters Older than 1 month",
      "conditions": {
        "operator": "ALL",
        "rules": [
          { "field": "from_email", "predicate": "Equals", "value": "newsletter@example.com" },
          { "field": "date",       "predicate": "LessThan", "value": "1m" }
        ]
      },
      "actions": [
        { "type": "move_message", "folder": "TRASH" },
      ]
    },
    {
      "name": "Keep important emails unread",
      "conditions": {
        "operator": "ANY",
        "rules": [
          { "field": "subject", "predicate": "Contains", "value": "[URGENT]" },
          { "field": "subject", "predicate": "Contains", "value": "Invoice" }
        ]
      },
      "actions": [
        { "type": "mark_as_unread" }
      ]
    }
  ]
}
```
