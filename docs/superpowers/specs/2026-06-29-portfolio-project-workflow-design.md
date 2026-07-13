# Portfolio Project Workflow Design

## Product Shift

The post-assessment flow should not promise that a beginner can submit strong resumes after seven days. The product should instead help the user turn a target JD into a concrete portfolio project they can understand, execute, package, and later use in resumes or interviews.

## Core Workflow

```text
Direction result
→ Role map
→ JD diagnosis
→ Portfolio project recommendations
→ Project breakdown workspace
```

## Page Responsibilities

### 1. Direction Result

Purpose: explain the recommended direction and push the user toward concrete target roles.

Shows:

- main direction and supporting directions
- fit reason
- risk notes
- suggested role families
- next action: choose target roles

Does not show:

- portfolio projects
- resume drafts
- detailed JD text

### 2. Role Map

Purpose: help the user choose real target roles, not just a broad direction.

Shows:

- filters for direction and practical constraints
- role cards backed by JD evidence
- high-frequency tasks
- hard requirements
- beginner suitability
- whether the role can be strengthened through a portfolio project

Does not show:

- project steps
- AI chat
- resume copy

### 3. JD Diagnosis

Purpose: explain what selected roles actually require.

Shows:

- selected JD or aggregated JD evidence
- task requirements
- capability requirements
- tool requirements
- hard requirements
- portfolio-buildable requirements
- the next sensible project goal

The page must clearly separate:

- requirements that cannot be solved through a project, such as city, weekly availability, and internship duration
- capabilities that can be demonstrated through a project, such as interview design, feedback synthesis, insight reporting, and solution framing

### 4. Portfolio Project Recommendations

Purpose: recommend project directions that can prove the selected JD requirements.

Each project card shows:

- project title
- suitable roles
- JD requirements it proves
- capabilities demonstrated
- required inputs
- expected outputs
- difficulty
- estimated cycle

The project library is an inspiration layer, not the source of truth. The source of truth is JD evidence mapped to capability modules and output templates.

This page only helps the user choose a project. It does not show execution steps.

### 5. Project Breakdown Workspace

Purpose: reduce the user's uncertainty when starting a portfolio project.

Workspace layout:

- left: project stages
- middle: current stage goal, tasks, output template, and completion action
- right: JD evidence, AI project coach prompts, and material destination

Stages:

1. Understand the JD requirement
2. Clarify the project topic
3. Collect evidence
4. Analyze the problem
5. Design the solution
6. Package the portfolio
7. Draft resume/interview expression

### Embedded AI Project Coach

Purpose: provide stage-specific help instead of open-ended chat. It should be embedded in the project workspace, not exposed as a separate main page.

Recommended prompt buttons:

- help me make this project topic more specific
- help me design interview questions
- help me analyze these user notes
- help me structure the portfolio page
- help me rewrite this as a resume bullet
- help me prepare an interview explanation

### Material Draft

Purpose: collect finished stage outputs into reusable material. It should be an output area inside the project workspace, not a standalone main page in V0.

Shows:

- portfolio title
- portfolio structure
- research method or execution method
- insight or solution summary
- resume bullet draft
- interview explanation outline

## V0 Boundary

V0 should implement the visual workflow and deterministic templates first:

- role/JD evidence summary
- 3-5 portfolio project recommendations per selected direction
- project breakdown stages
- output templates
- AI coach entry points as placeholders or prompt presets
- material draft output preview

V0 does not need:

- a large project library
- fully automatic project validation
- guaranteed resume readiness
- application tracking

## Desktop UI Model

The desktop prototype should use a workflow layout:

- top: current workflow tabs
- left: persistent stage sidebar
- center: the current decision or work area
- right: evidence, next action, or AI coach

Each page should answer one user question:

1. Direction Result: What direction should I start from?
2. Role Map: Which role should I prepare for?
3. JD Diagnosis: What does this role require, and what can I prove with a project?
4. Project Recommendations: Which project should I choose?
5. Project Workspace: What should I do now, what output should I produce, and how can AI help?

## Product Principle

Every recommended task must answer three questions:

- Which JD requirement does this prove?
- What concrete output will the user produce?
- How can that output later become resume, portfolio, or interview material?
