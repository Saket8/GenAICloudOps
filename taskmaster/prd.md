
# 🧠 GenAI CloudOps Dashboard - Product Requirements Document (PRD)

## 🌐 Project Name:
**GenAI CloudOps Dashboard**

## 🧩 Objective:
A web application that monitors OCI resources (VMs, Databases, Kubernetes, Load Balancers, etc.) in a selected compartment, shows live stats and alerts, uses a GenAI model to recommend remediations, and applies the fixes with user approval.

---

## 📦 Functional Requirements

### 1. Dashboard Page
- List of OCI services in a selected compartment:
  - VMs
  - Databases
  - OKE clusters
  - API Gateway
  - Load Balancer
- Real-time metrics:
  - CPU
  - Memory
  - Network
  - Health status
- Toggle for compartment/project filter

### 2. Alerts & Insights Page
- Summary of alerts from OCI Monitoring
- Natural language explanation of issues
- Recommendations from GenAI model

### 3. Remediation Panel
- Display GenAI-recommended remediations
- "Approve & Apply" button
- Trigger OCI CLI or Terraform via backend
- Audit trail of all actions

### 4. Conversational Agent
- Chatbot UI to ask questions like:
  - "What's wrong with my web server?"
  - "How to fix high latency?"
- Chat powered by GenAI with context from OCI APIs

---

## 💻 Frontend Stack
- React + Tailwind CSS + Axios
- UI components for stats cards, charts, tables
- React Query for live data
- Chatbot interface (side panel or floating bot)

## ⚙️ Backend Stack
- Python (FastAPI) or Node.js
- OCI SDK for pulling resource info and metrics
- OCI Logging API and Monitoring API
- OpenAI or OCI GenAI APIs (pass issue data, get remediation suggestions)
- OCI CLI or Terraform runner to apply fixes
- Use WebSocket or polling to show action status

## ☁️ Deployment
- All components containerized using Docker
- Deploy on OCI OKE
- Use Helm charts for deployment
- OCI Vault for secrets and API key storage
- Ingress Controller for frontend exposure
- Use OCI Function or Job to run remediations with approval logic

## 🔐 Auth
- Basic RBAC (Admin, Viewer, Operator)
- Optional: Integrate OCI IAM authentication

## 📈 Optional Enhancements
- Integrate with Prometheus + Grafana
- Email/Slack notifications for critical issues
- Auto-remediation toggle for low-risk issues

## 📄 Deliverables
- Source code for frontend and backend
- Helm chart for deployment
- Sample Terraform/OCI CLI scripts for remediation
- Example prompt templates for LLM
- README with setup instructions

---

## 🔐 Unified Access Analyzer Module (RBAC + IAM)

### 🧩 Goal:
Integrate Kubernetes RBAC and Oracle Cloud IAM policy analysis into a single module that visualizes access control and provides GenAI-based recommendations for hardening.

---

### ⚙️ Functional Requirements

#### 1. Backend
- Endpoint: `/access/rbac`, `/access/iam`, `/access/analyze`
- Use Kubernetes Python client to fetch RBAC roles and bindings
- Use OCI Python SDK to fetch IAM policies
- Parse and structure RBAC and IAM data
- POST to `/access/analyze` sends combined access data to GenAI for insights
- Risk scoring function for both RBAC and IAM (high, medium, low)
- Support optional remediation execution (`kubectl edit role`, OCI CLI patch)

#### 2. Frontend
- New "Access Analyzer" tab
- Graph view of Kubernetes RoleBindings (nodes = subjects, roles)
- Table view of IAM policies with:
  - Policy name
  - Compartment
  - Summary
  - Risk score (color-coded)
  - AI Recommendations
  - “Approve Fix” button
- Search, filter, and export capabilities

#### 3. GenAI Integration
- Use LLM to:
  - Translate RBAC and IAM policies to natural language
  - Highlight security risks
  - Recommend refactored, safer access configurations
- Prompt engineering with real-world access control scenarios
- Cache results in backend for faster access

---

### 👁️ UI/UX Hints
- Use `react-flow` or `cytoscape.js` for RBAC graph
- Table with expandable rows to show raw IAM policy JSON
- Tooltip for scoring logic
- “Analyze All” button to batch send policies to GenAI
- Export report button (PDF/CSV)

---

## 🔍 Pod Health & Log Analyzer (OKE)

### 🧩 Goal:
Monitor deployed application pod status in the OKE cluster, detect issues, extract erroneous log content, and auto-summarize problems using GenAI.

### ⚙️ Functional Requirements:

#### 1. Backend
- Endpoint: `/oke/pods/status`, `/oke/pods/logs`, `/oke/pods/analyze`
- Use Kubernetes Python client to fetch pod status and logs
- Detect pods in CrashLoopBackOff, Pending, or Error state
- Extract recent logs and identify error patterns
- Send logs and status to GenAI for summarization and root cause analysis

#### 2. Frontend
- New "Pod Analyzer" tab
- Table view of all pods with:
  - Namespace
  - Pod name
  - Status
  - Restart count
  - Error summary
- AI Insight panel with:
  - Log summary
  - Suggested fixes
  - “Approve Fix” button

#### 3. GenAI Integration
- Summarize logs and pod issues
- Recommend remediation steps
- Highlight recurring patterns or misconfigurations

---

## 💰 Cost Analyzer & Optimization Module

### 🧩 Goal:
Identify top 3 costly OCI resources this month and provide GenAI-based recommendations for cost optimization.

### ⚙️ Functional Requirements:

#### 1. Backend
- Endpoint: `/cost/top`, `/cost/analyze`
- Use OCI SDK to fetch cost reports and usage data
- Identify top 3 costly resources by compartment or tenancy
- Send cost data to GenAI for optimization suggestions

#### 2. Frontend
- New "Cost Analyzer" tab
- Chart view of monthly cost trends
- Table of top costly resources with:
  - Resource type
  - Cost
  - Compartment
  - AI Recommendations
- “Download Report” button (PDF/CSV)

#### 3. GenAI Integration
- Summarize recent cost trends
- Recommend actions like:
  - Rightsizing VMs
  - Removing idle resources
  - Switching to reserved instances
- Highlight anomalies or spikes in usage

---

## 🧩 Unified Architecture & Integration Strategy

### 🧠 Goal:
Ensure all modules and features — including dashboard, alerts, remediation, chatbot, access analyzer, pod health/log analyzer, and cost optimization — are seamlessly integrated into a single unified application. All services will be rendered from a centralized frontend dashboard/UI.

### 🧱 Integration Strategy:

- **Single Frontend Application**:
  - All modules (Dashboard, Alerts, Remediation, Chatbot, Access Analyzer, Pod Analyzer, Cost Analyzer) are accessible via tabs or panels within one React-based UI.
  - Shared layout and navigation for consistent user experience.

- **Backend Microservices**:
  - Modular FastAPI services for each functional domain (monitoring, remediation, access control, pod analysis, cost analysis).
  - Unified API gateway to route requests to appropriate services.

- **Data Flow**:
  - Real-time data fetched using React Query and WebSockets.
  - Backend services use OCI SDK, Kubernetes client, and GenAI APIs to gather insights and perform actions.

- **GenAI Integration**:
  - Centralized GenAI service handles prompt engineering and response generation for all modules.
  - Caching and batching supported for performance optimization.

- **Security & Auth**:
  - Unified RBAC and IAM enforcement across modules.
  - Role-based access to tabs and actions (Admin, Viewer, Operator).

- **Deployment**:
  - All services containerized and deployed via Helm on OCI OKE.
  - Shared ingress and OCI Vault integration for secrets and keys.

### 🔍 UI/UX Notes:
- Unified dashboard with tabbed navigation for each module.
- Consistent design system using Tailwind CSS.
- AI insights and approval actions embedded contextually across modules.

---

