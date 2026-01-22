<!-- <research-document-template> -->
<!-- markdownlint-disable-file -->
# Task Research Documents: {{task_name}}

{{continually_updated_full_description_of_task_being_researched}}

## Task Implementation Requests
<!-- <per_tasks_for_implementation> -->
* {{first_task_for_implementation}}
* {{second_task_for_implementation}}
<!-- <per_tasks_for_implementation> -->

## Scope and Success Criteria
* Scope: {{what_this_research_covers_and_excludes}}
* Assumptions: {{enumerated_assumptions}}
* Success Criteria:
  * {{criterion_1}}
  * {{criterion_2}}

## Outline
{{continually_updated_outline_of_this_research_document}}

### Potential Next Research
<!-- <per_relevant_next_research> -->
* {{potential_next_item_to_research}}
  * **Reasoning**: {{reasoning_for_researching_this_next_item}}
  * **Reference**: {{reference_where_item_was_identified_to_research}}
<!-- </per_relevant_next_research> -->

## Research Executed

### Testing Infrastructure Research
* **Framework**: {{test_framework_name_and_version}}
  * Location: {{test_directory_structure}}
  * Naming: {{test_file_naming_pattern}}
  * Runner: {{test_runner_command}}
  * Coverage: {{coverage_tool_and_configuration}}

### Test Patterns Found
* **File**: {{path_to_example_test}} (Lines {{X-Y}})
  * {{test_pattern_description}}
  * {{assertion_pattern_description}}
  * {{mock_stub_strategy}}
  * {{fixture_and_setup_patterns}}

### Coverage Standards
* **Unit Tests**: {{X}}% minimum
* **Integration Tests**: {{X}}% minimum
* **Critical Paths**: {{coverage_requirement}}

### Testing Approach Recommendation
* **{{Component_1}}**: {{TDD | Code-First}} ({{rationale}})
* **{{Component_2}}**: {{TDD | Code-First}} ({{rationale}})

**Rationale**: {{overall_testing_approach_justification}}

### File Analysis
* {{file_path}}
  * {{findings_summary_with_line_numbers_e.g._L10-L42}}

### Code Search Results
* {{relevant_search_term}}
  * {{actual_matches_found_with_paths_and_line_numbers}}
* {{relevant_search_pattern}}
  * {{files_discovered}}

### External Research (Evidence Log)
<!-- <per_relevant_external_research> -->
* {{external_tool_used}}: `{{query_or_url_used}}`
  * {{key_findings_with_quotes_or_summaries_and_date_accessed}}
    * Source: [{{helpful_source_name}}]({{source_url}})
    * Source: {{key_information_from_tool}}
<!-- </per_relevant_external_research> -->

### Project Conventions
* Standards referenced: {{conventions_applied}}
* Instructions followed: {{guidelines_used}}

## Key Discoveries

### Project Structure
{{project_organization_findings}}

### Implementation Patterns
{{code_patterns_and_conventions}}

### Complete Examples
```{{language}}
{{full_code_example_with_source}}
```

### API and Schema Documentation
{{complete_specifications_found_with_proper_links}}

### Configuration Examples
```{{format}}
{{configuration_examples_discovered}}
```

## Technical Scenarios

<!-- <per_technical_scenario> -->
### 1. {{identified_technical_scenario_title}}
{{description_of_technical_scenario}}

**Requirements:**
* {{identified_technical_scenario_requirements}}

**Preferred Approach:**
* {{detailed_overview_of_preferred_approach_with_rationale}}

```text
{{updates_or_new_files_folders_in_tree_format}} # {{describe_change}}
```

{{mermaid_diagram_explaining_flow_for_approach}}

**Implementation Details:**

<!-- <per_detail> -->
{{implementation_details}}

```{{format}}
{{implementation_snippets_or_config}}
```
<!-- </per_detail> -->

#### Considered Alternatives (Removed After Selection)
{{reason_for_not_selecting_alternative}}
{{concise_summary_of_non_selected_alternatives_and_tradeoffs}}

<!-- </per_technical_scenario> -->
<!-- </research-document-template> -->
