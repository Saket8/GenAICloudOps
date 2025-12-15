# 👤 User Guide

Complete guide for using the GenAI CloudOps Dashboard to monitor, analyze, and manage your Oracle Cloud Infrastructure.

## Table of Contents

- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Monitoring & Alerts](#monitoring--alerts)
- [AI Assistant](#ai-assistant)
- [Cost Analysis](#cost-analysis)
- [Security Analysis](#security-analysis)
- [Kubernetes Management](#kubernetes-management)
- [Auto-Remediation](#auto-remediation)
- [Notifications](#notifications)
- [Settings & Preferences](#settings--preferences)

## Getting Started

### First Login

1. **Access the Dashboard**
   - Open your web browser and navigate to the dashboard URL
   - For development: `http://localhost:3000`
   - For production: `https://your-domain.com`

2. **Login Process**
   - Enter your email address and password
   - Click "Sign In" to authenticate
   - You'll be redirected to the main dashboard

3. **Initial Setup**
   - Complete your profile information
   - Set notification preferences
   - Configure OCI compartment access

### Navigation Overview

The dashboard uses a sidebar navigation with the following main sections:

- **🏠 Dashboard** - Overview and key metrics
- **📊 Monitoring** - Resource monitoring and alerts
- **💬 AI Assistant** - Chat with AI about your infrastructure
- **💰 Cost Analysis** - Cost tracking and optimization
- **🔐 Access Analyzer** - Security and RBAC analysis
- **☸️ Kubernetes** - Pod health and cluster management
- **🔧 Remediation** - Automated issue resolution
- **🔔 Notifications** - Alert management and settings

## Dashboard Overview

### Main Dashboard

The main dashboard provides a high-level overview of your infrastructure health and key metrics.

#### Key Widgets

1. **Infrastructure Health Score**
   - Overall health percentage
   - Color-coded status (Green: Healthy, Yellow: Warning, Red: Critical)
   - Trend indicator showing improvement or degradation

2. **Resource Summary**
   - Total resource count by type
   - Status breakdown (Running, Stopped, Warning, Error)
   - Quick access to detailed views

3. **Recent Alerts**
   - Latest critical and high-priority alerts
   - One-click access to alert details
   - Quick acknowledgment options

4. **Cost Overview**
   - Current month spending
   - Budget status and remaining allocation
   - Top cost drivers

5. **AI Insights**
   - Latest AI-generated recommendations
   - Proactive issue identification
   - Optimization suggestions

#### Customization

- **Widget Layout**: Drag and drop widgets to customize layout
- **Refresh Rate**: Set automatic refresh intervals (30s, 1m, 5m, 15m)
- **Time Range**: Filter data by time period (1h, 6h, 24h, 7d, 30d)
- **Compartment Filter**: Focus on specific OCI compartments

### Quick Actions

Located in the top-right corner of the dashboard:

- **🔄 Refresh Data** - Manually refresh all widgets
- **📋 Export Report** - Generate PDF/Excel reports
- **⚙️ Settings** - Access user preferences
- **❓ Help** - Access documentation and support

## Monitoring & Alerts

### Resource Monitoring

#### Resource List View

Navigate to **📊 Monitoring** → **Resources** to view all monitored resources.

**Filter Options:**
- **Compartment**: Select specific OCI compartments
- **Resource Type**: Filter by Compute, Database, Network, Storage
- **Status**: Show only healthy, warning, or critical resources
- **Search**: Find resources by name or ID

**Resource Information:**
- Resource name and type
- Current status and health score
- Key metrics (CPU, Memory, Network)
- Last update timestamp
- Quick action buttons

#### Resource Details

Click on any resource to view detailed information:

1. **Overview Tab**
   - Resource configuration
   - Current status and health metrics
   - Recent activity timeline

2. **Metrics Tab**
   - Real-time performance charts
   - Historical trend analysis
   - Customizable time ranges

3. **Alerts Tab**
   - Active alerts for this resource
   - Alert history and resolution
   - Alert configuration

4. **Logs Tab**
   - Recent log entries
   - Log filtering and search
   - Download log exports

### Alert Management

#### Alert Dashboard

Access alerts through **📊 Monitoring** → **Alerts**.

**Alert Categories:**
- **🔴 Critical**: Immediate attention required
- **🟡 High**: Important issues to address
- **🔵 Medium**: Monitor closely
- **⚪ Low**: Informational alerts

**Alert Actions:**
- **Acknowledge**: Mark as seen but not resolved
- **Resolve**: Mark as fixed
- **Snooze**: Temporarily suppress notifications
- **Escalate**: Forward to higher-level support

#### Alert Details

Click on any alert to view:
- Detailed description and impact
- Affected resources
- Recommended actions
- Resolution history
- Related alerts and patterns

### Creating Custom Alerts

1. Navigate to **📊 Monitoring** → **Alert Rules**
2. Click **+ Create Alert Rule**
3. Configure alert parameters:
   - **Resource Type**: What to monitor
   - **Metric**: Which metric to track
   - **Threshold**: When to trigger alert
   - **Severity**: Alert importance level
   - **Recipients**: Who to notify

## AI Assistant

### Chat Interface

The AI Assistant provides conversational access to your infrastructure insights.

#### Accessing the AI Chat

- Click the **💬** icon in the sidebar
- Or use the chat widget on the main dashboard
- The chat panel will open on the right side

#### Example Conversations

**Infrastructure Status Queries:**
```
User: "What's the current status of my infrastructure?"
AI: "Your infrastructure is 92% healthy with 45 resources monitored. There are 2 warning alerts on compute instances and 1 critical database issue requiring attention..."

User: "Show me pods with high memory usage"
AI: "I found 3 pods with memory usage above 80%:
1. frontend-app-xyz (85% - 1.7GB/2GB)
2. data-processor-abc (92% - 3.7GB/4GB)
3. cache-service-def (88% - 1.8GB/2GB)
Would you like me to suggest optimization steps?"
```

**Cost Optimization:**
```
User: "How can I reduce my monthly costs?"
AI: "Based on your usage patterns, here are 3 cost optimization opportunities:
1. Resize 2 underutilized compute instances (save ~$245/month)
2. Enable auto-scaling for database (save ~$180/month)
3. Optimize storage classes (save ~$95/month)
Total potential savings: $520/month"
```

**Troubleshooting:**
```
User: "My web application is running slowly"
AI: "I've analyzed your web application stack and found:
- Database response time increased 40% in the last hour
- CPU usage on app servers is normal (35%)
- Database connections are at 85% of limit
Recommended actions:
1. Check for long-running queries
2. Consider connection pooling optimization
3. Monitor database locks and waits"
```

#### AI Features

1. **Context Awareness**
   - Understands your current view/page
   - Remembers conversation history
   - Considers recent alerts and issues

2. **Natural Language Processing**
   - Ask questions in plain English
   - No need for technical syntax
   - Supports follow-up questions

3. **Actionable Insights**
   - Provides specific recommendations
   - Includes CLI commands when helpful
   - Links to relevant dashboard sections

4. **Multi-turn Conversations**
   - Maintains context across messages
   - Can clarify and expand on previous responses
   - Learns from your preferences

### Chat Features

#### Message Types

- **📝 Text Messages**: Standard questions and responses
- **📊 Data Insights**: Charts and metrics embedded in chat
- **🔗 Quick Links**: Direct navigation to relevant sections
- **📋 Action Items**: Suggested next steps with buttons

#### Chat Controls

- **🔄 Regenerate**: Get alternative AI response
- **👍/👎 Feedback**: Rate response quality
- **📑 Copy**: Copy AI response to clipboard
- **🔗 Share**: Share conversation with team members

#### Conversation Management

- **History**: Access previous conversations
- **Bookmarks**: Save important AI insights
- **Export**: Download conversation transcripts
- **Clear**: Start fresh conversation

## Cost Analysis

### Cost Dashboard

Navigate to **💰 Cost Analysis** to access cost monitoring features.

#### Overview Widgets

1. **Current Month Spending**
   - Total costs and trend
   - Budget comparison
   - Projection for month-end

2. **Cost Breakdown**
   - By service (Compute, Database, Network, etc.)
   - By compartment/project
   - By resource tags

3. **Top Cost Drivers**
   - Most expensive resources
   - Highest growth areas
   - Optimization opportunities

#### Time Range Analysis

- **Daily**: Detailed daily spending patterns
- **Weekly**: Week-over-week comparisons
- **Monthly**: Monthly trends and budgets
- **Quarterly**: Seasonal patterns and planning

### Cost Optimization

#### Automated Recommendations

The system automatically identifies cost optimization opportunities:

1. **Right-sizing Recommendations**
   - Overprovisioned compute instances
   - Underutilized databases
   - Storage optimization opportunities

2. **Reserved Instance Opportunities**
   - Consistent usage patterns suitable for reservations
   - Potential savings calculations
   - Purchase recommendations

3. **Storage Optimization**
   - Unused storage volumes
   - Archive opportunities for old data
   - Storage tier optimization

#### Custom Cost Alerts

Set up alerts for:
- **Budget Thresholds**: Alert when approaching budget limits
- **Anomaly Detection**: Unusual spending patterns
- **Service Limits**: Spending caps on specific services
- **Resource Waste**: Idle or unused resources

### Cost Reports

#### Generating Reports

1. Click **📊 Generate Report**
2. Select report parameters:
   - Time period
   - Compartments to include
   - Report format (PDF, Excel, CSV)
   - Recipients for automatic delivery

#### Report Types

- **Executive Summary**: High-level cost overview
- **Detailed Breakdown**: Service and resource level analysis
- **Optimization Report**: Savings opportunities and recommendations
- **Budget vs. Actual**: Variance analysis and projections

## Security Analysis

### Access Analyzer Overview

Navigate to **🔐 Access Analyzer** to review security posture and access controls.

#### RBAC Analysis

1. **Kubernetes RBAC**
   - Visual representation of role bindings
   - Permission matrices
   - Overprivileged accounts identification
   - Security recommendations

2. **OCI IAM Analysis**
   - User and group permissions
   - Policy effectiveness review
   - Privilege escalation risks
   - Compliance checks

#### Security Score

The security score (0-100) is calculated based on:
- Permission appropriateness (40%)
- Policy compliance (30%)
- Access pattern analysis (20%)
- Security best practices (10%)

### Security Recommendations

#### Automated Recommendations

The system provides actionable security improvements:

1. **Permission Reduction**
   - Remove unnecessary privileges
   - Replace broad permissions with specific ones
   - Eliminate dormant accounts

2. **Policy Hardening**
   - Implement principle of least privilege
   - Add conditional access controls
   - Enable audit logging

3. **Access Review**
   - Regular access certification
   - Automated cleanup of stale permissions
   - Separation of duties enforcement

#### Remediation Actions

For each recommendation:
- **Risk Assessment**: Impact and likelihood scores
- **Remediation Steps**: Specific actions to take
- **CLI Commands**: Ready-to-use commands
- **Testing Guidelines**: How to verify changes

### Compliance Monitoring

#### Compliance Frameworks

Track compliance with:
- **CIS Benchmarks**: Center for Internet Security standards
- **NIST Framework**: National Institute of Standards guidelines
- **PCI DSS**: Payment Card Industry standards
- **SOX**: Sarbanes-Oxley compliance requirements

#### Compliance Reports

Generate reports showing:
- Current compliance status
- Failed compliance checks
- Remediation progress
- Historical compliance trends

## Kubernetes Management

### Cluster Overview

Navigate to **☸️ Kubernetes** to monitor and manage your OKE clusters.

#### Cluster Health Dashboard

1. **Cluster Status**
   - Overall cluster health score
   - Node availability and status
   - Resource utilization summary
   - Recent events and changes

2. **Pod Health Summary**
   - Total pods and status breakdown
   - Failed/CrashLoopBackOff pods
   - Resource usage patterns
   - Health trend analysis

#### Navigation Structure

- **Clusters**: List of all monitored clusters
- **Pods**: Detailed pod health and status
- **RBAC**: Security and access analysis
- **Logs**: Centralized log analysis

### Pod Health Monitoring

#### Pod Status Overview

View all pods with:
- **Status Indicators**: Running, Pending, Failed, Succeeded
- **Health Scores**: 0-100 based on multiple factors
- **Resource Usage**: CPU and memory consumption
- **Restart Counts**: Stability indicators

#### Pod Details

Click on any pod to see:

1. **Overview**
   - Pod specifications and status
   - Container information
   - Resource requests and limits
   - Scheduling information

2. **Metrics**
   - Real-time resource usage
   - Performance trends
   - Comparison with limits

3. **Logs**
   - Container logs with filtering
   - Error detection and highlighting
   - Log download and export

4. **Events**
   - Kubernetes events for the pod
   - Scheduling decisions
   - Error messages and warnings

### Troubleshooting Tools

#### Log Analysis

1. **Intelligent Log Parsing**
   - Automatic error detection
   - Pattern recognition
   - Anomaly identification

2. **Log Aggregation**
   - Multi-container log viewing
   - Timestamp correlation
   - Cross-pod log analysis

3. **Search and Filtering**
   - Keyword search across logs
   - Time-based filtering
   - Severity level filtering

#### Health Checks

- **Liveness Probes**: Container health monitoring
- **Readiness Probes**: Service availability checks
- **Startup Probes**: Application initialization tracking

### RBAC Management

#### Visual RBAC Analysis

- **Graph View**: Visual representation of permissions
- **Matrix View**: User/service account permission matrix
- **Tree View**: Hierarchical role structure

#### Security Recommendations

- Identify overprivileged accounts
- Suggest minimal permission sets
- Highlight security risks
- Provide remediation commands

## Auto-Remediation

### Remediation Overview

Navigate to **🔧 Remediation** to manage automated issue resolution.

#### Available Remediation Plans

1. **Infrastructure Remediation**
   - Restart unresponsive instances
   - Resize overloaded resources
   - Clean up disk space
   - Network connectivity fixes

2. **Kubernetes Remediation**
   - Restart failed pods
   - Scale applications
   - Clear resource constraints
   - Fix configuration issues

3. **Database Remediation**
   - Connection pool optimization
   - Query optimization
   - Index maintenance
   - Backup restoration

#### Risk Assessment

Each remediation action includes:
- **Risk Level**: Very Low, Low, Medium, High, Critical
- **Impact Analysis**: What will be affected
- **Success Probability**: Likelihood of successful resolution
- **Rollback Plan**: How to undo changes if needed

### Execution Process

#### Automated Execution

For low-risk actions:
1. Issue detected automatically
2. AI assesses remediation options
3. Risk evaluation performed
4. Action executed if risk is acceptable
5. Results monitored and reported

#### Approval Workflow

For higher-risk actions:
1. Remediation plan generated
2. Approval request sent to administrators
3. Plan review and approval/rejection
4. Execution upon approval
5. Progress monitoring and reporting

### Remediation History

#### Execution Log

Track all remediation activities:
- **Timestamp**: When action was taken
- **Action Type**: What was performed
- **Success/Failure**: Outcome status
- **Duration**: Time taken to complete
- **Impact**: Resources affected

#### Performance Metrics

Monitor remediation effectiveness:
- **Success Rate**: Percentage of successful remediations
- **Average Resolution Time**: How quickly issues are resolved
- **Recurrence Rate**: How often issues repeat
- **User Satisfaction**: Feedback on remediation quality

## Notifications

### Notification Channels

Configure how you receive alerts and updates:

#### Email Notifications

1. **Configuration**
   - Add email addresses
   - Set notification frequency
   - Choose alert severities
   - Configure digest options

2. **Templates**
   - Alert notifications
   - Daily/weekly summaries
   - Remediation reports
   - Cost alerts

#### Slack Integration

1. **Setup**
   - Connect Slack workspace
   - Configure channels
   - Set up bot permissions
   - Test integration

2. **Features**
   - Real-time alert posting
   - Interactive message buttons
   - Thread-based discussions
   - Status updates

### Notification Rules

#### Alert Filtering

Create rules to control notifications:
- **Severity Thresholds**: Only critical/high alerts
- **Resource Filters**: Specific compartments or services
- **Time-based Rules**: Business hours only
- **Frequency Limits**: Avoid notification fatigue

#### Escalation Policies

Set up automatic escalation:
1. **Initial Notification**: Send to primary contacts
2. **First Escalation**: After 15 minutes if unacknowledged
3. **Second Escalation**: After 30 minutes to management
4. **Final Escalation**: After 1 hour to executive team

### Notification History

#### Message Tracking

View all sent notifications:
- **Delivery Status**: Sent, delivered, failed
- **Response Tracking**: Acknowledged, resolved
- **Escalation Log**: When and to whom escalated
- **Effectiveness Metrics**: Response times and outcomes

## Settings & Preferences

### User Profile

Access via **⚙️ Settings** → **Profile**

#### Personal Information
- Display name and contact details
- Time zone and language preferences
- Profile picture and bio

#### Notification Preferences
- Email notification settings
- Slack integration preferences
- Mobile push notifications (future)
- Digest frequency and format

### Dashboard Customization

#### Layout Options
- Widget arrangement and sizing
- Color themes (light/dark mode)
- Default time ranges
- Auto-refresh intervals

#### Data Preferences
- Default compartment filters
- Preferred metric units
- Chart types and visualizations
- Export formats

### Security Settings

#### Authentication
- Password change
- Two-factor authentication setup
- Session management
- Login history review

#### API Access
- Generate API keys
- Configure access permissions
- Monitor API usage
- Revoke access tokens

### System Configuration

#### OCI Integration
- Compartment access configuration
- Credential management
- Regional settings
- Service enablement

#### AI Assistant Settings
- Conversation preferences
- Response detail level
- Language and tone settings
- Feature enablement

### Team Management

*Available for admin users*

#### User Administration
- Add/remove team members
- Assign roles and permissions
- Monitor user activity
- Configure access policies

#### Organization Settings
- Company information
- Branding customization
- Feature enablement
- Billing and subscription management

## Tips and Best Practices

### Effective Monitoring

1. **Set Appropriate Thresholds**
   - Start with conservative thresholds
   - Adjust based on false positive rates
   - Consider seasonal patterns
   - Regular threshold reviews

2. **Use Compartment Filtering**
   - Organize resources logically
   - Set environment-specific views
   - Create team-based access
   - Implement cost allocation

3. **Monitor Trends**
   - Focus on trend analysis, not just current values
   - Set up baseline monitoring
   - Watch for gradual degradation
   - Identify growth patterns

### AI Assistant Usage

1. **Be Specific**
   - Include context in your questions
   - Specify time ranges when relevant
   - Mention specific resources or services
   - Ask follow-up questions for clarity

2. **Use Natural Language**
   - Ask questions as you would to a colleague
   - Don't worry about technical syntax
   - The AI understands context and intent
   - Iterate and refine your questions

### Cost Optimization

1. **Regular Reviews**
   - Weekly cost analysis
   - Monthly budget reviews
   - Quarterly optimization assessments
   - Annual planning sessions

2. **Automation**
   - Set up cost alerts
   - Enable auto-scaling where appropriate
   - Use reserved instances for predictable workloads
   - Implement lifecycle policies for storage

### Security Best Practices

1. **Regular Access Reviews**
   - Monthly permission audits
   - Quarterly access certification
   - Annual policy reviews
   - Continuous monitoring

2. **Principle of Least Privilege**
   - Grant minimum necessary permissions
   - Use role-based access control
   - Implement time-bound access
   - Regular cleanup of unused accounts

## Getting Help

### Documentation
- Complete user guides and tutorials
- API documentation and examples
- Troubleshooting guides and FAQs
- Video tutorials and walkthroughs

### Support Channels
- **In-app Help**: Built-in help system and tooltips
- **Email Support**: support@genai-cloudops.com
- **Community Forum**: GitHub Discussions
- **Bug Reports**: GitHub Issues

### Training Resources
- Getting started tutorials
- Advanced feature training
- Best practices workshops
- Certification programs

Remember: The AI Assistant is always available to help with questions about using the platform or understanding your infrastructure! 