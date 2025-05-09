## Email Filtering & Manipulation Rules

Your rules file must be a JSON-serializable object matching the top-level Pydantic model:

```yaml
Rules:
  rules: FilterRule[]
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

| Property    | Type                                        | Description                                                                                                          |
| ----------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `field`     | `string`                                    | Name of an `Email` model attribute: e.g. `subject`, `from_email`, `date`, etc.                                       |
| `predicate` | `StringFilters` \| `DatetimeFilters`        | Which comparison to perform (see below).                                                                              |
| `value`     | `string`                                    | The literal to compare against. For dates, use ISO-8601 format.                                                      |

##### Allowed `StringFilters`
- `Contains`  
- `DoesNotContain`  
- `Equals`  
- `DoesNotEqual`  

##### Allowed `DatetimeFilters`
- `GreaterThan`  
- `LessThan`  

### 4. `FilterAction`

| Property | Type                | Description                                                                                               |
| -------- | ------------------- | --------------------------------------------------------------------------------------------------------- |
| `type`   | `EmailAction`       | What action to perform: `MarkAsRead`, `MarkAsUnread`, `MoveMessage`                                       |
| `folder` | `MailBox` (optional) | Required only when `type: MoveMessage`. One of: `Inbox`, `Trash`, `Spam`, `Sent`, `Draft`.                 |

### 5. Examples

```json
{
  "rules": [
    {
      "name": "Archive old newsletters",
      "conditions": {
        "operator": "ALL",
        "rules": [
          { "field": "from_email", "predicate": "Equals", "value": "newsletter@example.com" },
          { "field": "date",       "predicate": "LessThan", "value": "2025-01-01T00:00:00" }
        ]
      },
      "actions": [
        { "type": "MoveMessage", "folder": "Trash" },
        { "type": "MarkAsRead" }
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
        { "type": "MarkAsUnread" }
      ]
    }
  ]
}
```
