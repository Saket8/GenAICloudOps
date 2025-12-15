# GenAI Prompt Engineering Best Practices Guide

## Overview

This guide provides comprehensive best practices for creating, optimizing, and managing GenAI prompts within the GenAI CloudOps Dashboard. It covers prompt design principles, optimization techniques, quality metrics, and maintenance strategies.

## Table of Contents

1. [Prompt Design Principles](#prompt-design-principles)
2. [Template Structure Guidelines](#template-structure-guidelines)
3. [Parameter Management](#parameter-management)
4. [Quality Optimization](#quality-optimization)
5. [A/B Testing Framework](#ab-testing-framework)
6. [Performance Considerations](#performance-considerations)
7. [Security and Privacy](#security-and-privacy)
8. [Maintenance and Versioning](#maintenance-and-versioning)

## Prompt Design Principles

### 1. Clarity and Specificity

**Best Practice**: Be explicit about what you want the AI to do
```
❌ Bad: "Analyze this data"
✅ Good: "Analyze the following OCI resource metrics and provide a health assessment with specific recommendations for optimization"
```

**Best Practice**: Use structured formats for complex requests
```
❌ Bad: "Look at these logs and tell me what's wrong"
✅ Good: 
**Log Analysis Request:**
- Time Range: {time_range}
- Log Sources: {log_sources}
- Focus Area: Error patterns and performance issues

Provide:
1. Error frequency analysis
2. Performance bottlenecks
3. Recommended actions
```

### 2. Context Provision

**Best Practice**: Always provide relevant context
- Environment details (production, staging, development)
- Time constraints and urgency levels
- Business impact and stakeholder information
- Technical constraints and dependencies

### 3. Output Structure

**Best Practice**: Define clear output expectations
```python
# Good prompt structure
"""
Provide your analysis in the following format:
1. **Executive Summary**: High-level findings
2. **Detailed Analysis**: Technical deep-dive
3. **Recommendations**: Prioritized action items
4. **Implementation**: Step-by-step instructions
5. **Monitoring**: Follow-up metrics to track
"""
```

### 4. Domain Expertise Framing

**Best Practice**: Frame the AI as a domain expert
```python
# Example for infrastructure monitoring
"""
You are a senior cloud infrastructure specialist with 10+ years of experience in OCI environments. 
You have deep expertise in performance optimization, cost management, and security best practices.
"""
```

## Template Structure Guidelines

### Standard Template Components

1. **Role Definition**: Establish AI expertise and perspective
2. **Context Section**: Provide all relevant background information
3. **Data Inputs**: Clearly labeled data sections with formatting
4. **Processing Instructions**: Specific analysis requirements
5. **Output Format**: Structured response format
6. **Quality Criteria**: Success metrics and validation points

### Example Template Structure

```python
INFRASTRUCTURE_MONITORING_TEMPLATE = """
You are an infrastructure monitoring specialist with expertise in {platform} environments.

**Analysis Context:**
- Environment: {environment_type}
- Time Range: {time_range}
- Baseline Metrics: {baseline_metrics}

**Resource Data:**
{resource_data}

**Performance Requirements:**
{performance_requirements}

**Analysis Instructions:**
1. Evaluate current performance against baselines
2. Identify anomalies and trends
3. Assess capacity and scaling needs
4. Provide specific optimization recommendations

**Output Format:**
1. **Health Score**: Overall system health (0-100)
2. **Performance Analysis**: Detailed metrics evaluation
3. **Anomaly Detection**: Unusual patterns or behaviors
4. **Recommendations**: Prioritized action items with implementation steps
5. **Monitoring**: Suggested alerts and thresholds

**Quality Criteria:**
- Include specific metric values and thresholds
- Provide actionable OCI CLI commands
- Reference relevant OCI documentation
- Estimate implementation effort and impact
"""
```

## Parameter Management

### Required vs Optional Parameters

**Best Practice**: Clearly distinguish between required and optional parameters

```python
# Template parameter validation
REQUIRED_PARAMS = [
    "resource_data", "environment_type", "time_range"
]

OPTIONAL_PARAMS = [
    "baseline_metrics", "performance_requirements", "custom_thresholds"
]
```

### Default Values and Fallbacks

**Best Practice**: Provide meaningful defaults for optional parameters

```python
def format_prompt_with_defaults(template, **kwargs):
    defaults = {
        "time_range": "24 hours",
        "environment_type": "production",
        "performance_requirements": "standard SLA requirements"
    }
    
    # Merge provided params with defaults
    params = {**defaults, **kwargs}
    return template.format(**params)
```

### Parameter Validation

**Best Practice**: Validate parameters before prompt generation

```python
def validate_parameters(prompt_type: PromptType, **kwargs):
    validation_rules = {
        PromptType.COST_ANALYSIS: {
            "required": ["cost_data", "billing_period"],
            "optional": ["budget_allocation", "previous_period"],
            "types": {
                "cost_data": str,
                "billing_period": str,
                "budget_allocation": (str, int, float)
            }
        }
    }
    
    rules = validation_rules.get(prompt_type, {})
    
    # Validate required parameters
    missing_required = [p for p in rules.get("required", []) if p not in kwargs]
    if missing_required:
        raise ValueError(f"Missing required parameters: {missing_required}")
    
    # Validate parameter types
    type_rules = rules.get("types", {})
    for param, expected_type in type_rules.items():
        if param in kwargs and not isinstance(kwargs[param], expected_type):
            raise TypeError(f"Parameter {param} must be of type {expected_type}")
    
    return True
```

## Quality Optimization

### Response Quality Metrics

**Quality Dimensions:**
1. **Relevance**: How well the response addresses the specific question
2. **Completeness**: Coverage of all requested elements
3. **Accuracy**: Technical correctness of information
4. **Actionability**: Presence of specific, implementable recommendations
5. **Structure**: Clear organization and formatting
6. **Context Awareness**: Integration of provided context

### Quality Scoring Implementation

```python
class PromptQualityAssessment:
    def assess_response_quality(self, response: str, expected_elements: List[str]) -> Dict[str, float]:
        scores = {}
        
        # Completeness: Check for expected elements
        scores["completeness"] = self._check_completeness(response, expected_elements)
        
        # Structure: Look for proper formatting
        scores["structure"] = self._assess_structure(response)
        
        # Actionability: Count specific recommendations
        scores["actionability"] = self._assess_actionability(response)
        
        # Technical depth: Evaluate technical content
        scores["technical_depth"] = self._assess_technical_depth(response)
        
        # Overall quality score (weighted average)
        weights = {"completeness": 0.3, "structure": 0.2, "actionability": 0.3, "technical_depth": 0.2}
        scores["overall"] = sum(scores[dim] * weight for dim, weight in weights.items())
        
        return scores
    
    def _check_completeness(self, response: str, expected_elements: List[str]) -> float:
        """Check if response contains all expected elements"""
        found_elements = sum(1 for element in expected_elements if element.lower() in response.lower())
        return found_elements / len(expected_elements) if expected_elements else 1.0
    
    def _assess_structure(self, response: str) -> float:
        """Assess response structure quality"""
        structure_indicators = [
            ("numbered_lists", r'\d+\.'),
            ("headers", r'\*\*.*\*\*'),
            ("bullet_points", r'[•\-\*]\s'),
            ("sections", r'(provide:|include:|steps:|recommendations:)')
        ]
        
        score = 0.0
        for name, pattern in structure_indicators:
            if re.search(pattern, response, re.IGNORECASE):
                score += 0.25
        
        return min(score, 1.0)
    
    def _assess_actionability(self, response: str) -> float:
        """Assess presence of actionable recommendations"""
        actionable_keywords = [
            "oci", "kubectl", "configure", "enable", "disable", "create", 
            "modify", "update", "install", "command", "script"
        ]
        
        found_keywords = sum(1 for keyword in actionable_keywords 
                           if keyword in response.lower())
        
        return min(found_keywords / 5.0, 1.0)  # Normalize to 0-1 scale
```

## A/B Testing Framework

### Setting Up A/B Tests

**Best Practice**: Test one variable at a time

```python
# Example A/B test for prompt optimization
test_config = {
    "test_name": "cost_analysis_structure",
    "hypothesis": "Structured output format improves recommendation clarity",
    "variants": {
        "control": "Standard cost analysis prompt",
        "variant": "Cost analysis prompt with structured output sections"
    },
    "success_metrics": [
        "response_clarity_score",
        "user_satisfaction_rating",
        "action_implementation_rate"
    ],
    "traffic_split": 0.5,
    "minimum_sample_size": 100,
    "test_duration": "2 weeks"
}
```

### Test Implementation

```python
async def run_ab_test_prompt(test_id: str, user_id: str, prompt_type: PromptType, **kwargs):
    """Generate response using A/B testing framework"""
    
    # Get user's test assignment
    variant = prompt_optimization.get_prompt_variant(test_id, user_id)
    
    # Track test exposure
    analytics.track_event("prompt_ab_test_exposure", {
        "test_id": test_id,
        "user_id": user_id,
        "variant": variant,
        "prompt_type": prompt_type.value
    })
    
    # Generate response with assigned variant
    start_time = time.time()
    try:
        response = await genai_service.generate_with_ab_testing(
            test_id, user_id, prompt_type, **kwargs
        )
        
        # Track success metrics
        response_time = time.time() - start_time
        success = True
        
    except Exception as e:
        response_time = time.time() - start_time
        success = False
        raise e
    
    finally:
        # Record test result
        prompt_optimization.record_test_result(
            test_id, variant, success, response_time
        )
    
    return response
```

### Analyzing Test Results

```python
def analyze_ab_test_results(test_id: str) -> Dict[str, Any]:
    """Analyze A/B test results for statistical significance"""
    test_data = prompt_optimization.get_ab_test_results(test_id)
    
    variant_a_metrics = test_data["metrics"]["variant_a"]
    variant_b_metrics = test_data["metrics"]["variant_b"]
    
    # Calculate statistical significance
    significance = calculate_statistical_significance(
        variant_a_metrics, variant_b_metrics
    )
    
    # Generate recommendations
    recommendations = []
    if significance["p_value"] < 0.05:
        winner = "variant_b" if variant_b_metrics["success_rate"] > variant_a_metrics["success_rate"] else "variant_a"
        recommendations.append(f"Implement {winner} as the default prompt")
    else:
        recommendations.append("No statistically significant difference found. Consider longer test duration or different variants.")
    
    return {
        "test_id": test_id,
        "statistical_significance": significance,
        "performance_comparison": {
            "variant_a": variant_a_metrics,
            "variant_b": variant_b_metrics
        },
        "recommendations": recommendations
    }
```

## Performance Considerations

### Response Time Optimization

**Best Practice**: Optimize for response speed without sacrificing quality

1. **Prompt Length**: Keep prompts concise while maintaining specificity
2. **Parameter Efficiency**: Only include necessary context
3. **Caching Strategy**: Cache responses for similar requests
4. **Model Selection**: Use appropriate model size for complexity

```python
# Performance optimization example
PERFORMANCE_OPTIMIZED_PROMPT = """
You are a cloud cost analyst. Analyze the cost data and provide 3 key recommendations.

**Cost Data:** {cost_data}
**Budget:** ${budget}

Provide:
1. Top cost driver
2. Best optimization opportunity  
3. Immediate action to take

Keep response under 200 words.
"""
```

### Caching Strategies

**Best Practice**: Implement intelligent caching based on context volatility

```python
def get_cache_ttl(prompt_type: PromptType, context: Dict[str, Any]) -> int:
    """Determine appropriate cache TTL based on prompt type and context"""
    
    cache_strategies = {
        PromptType.COST_ANALYSIS: {
            "base_ttl": 3600,  # 1 hour
            "factors": {
                "real_time_data": 0.5,    # Reduce TTL for real-time data
                "historical_data": 2.0,   # Increase TTL for historical data
                "trending_analysis": 0.3  # Short TTL for trending data
            }
        },
        PromptType.INFRASTRUCTURE_MONITORING: {
            "base_ttl": 300,   # 5 minutes
            "factors": {
                "alert_active": 0.1,      # Very short TTL during alerts
                "baseline_metrics": 2.0,  # Longer TTL for baseline analysis
                "performance_trending": 0.5
            }
        }
    }
    
    strategy = cache_strategies.get(prompt_type, {"base_ttl": 900, "factors": {}})
    ttl = strategy["base_ttl"]
    
    # Adjust TTL based on context factors
    for factor, multiplier in strategy["factors"].items():
        if factor in context:
            ttl = int(ttl * multiplier)
    
    return max(ttl, 60)  # Minimum 1 minute cache
```

## Security and Privacy

### Data Sanitization

**Best Practice**: Sanitize sensitive data before sending to AI services

```python
import re
from typing import Dict, Any

class DataSanitizer:
    """Sanitize sensitive data in prompts"""
    
    def __init__(self):
        self.patterns = {
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}-\d{3}-\d{4}\b',
            "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b'
        }
    
    def sanitize_prompt_data(self, data: str, context: Dict[str, Any] = None) -> str:
        """Sanitize sensitive data from prompt content"""
        sanitized = data
        
        for data_type, pattern in self.patterns.items():
            if self._should_sanitize(data_type, context):
                sanitized = re.sub(pattern, f'[REDACTED_{data_type.upper()}]', sanitized)
        
        return sanitized
    
    def _should_sanitize(self, data_type: str, context: Dict[str, Any]) -> bool:
        """Determine if data type should be sanitized based on context"""
        if not context:
            return True  # Default to sanitizing
        
        # Configuration-based sanitization rules
        sanitization_config = context.get('sanitization_rules', {})
        return sanitization_config.get(data_type, True)

# Usage example
sanitizer = DataSanitizer()
clean_prompt = sanitizer.sanitize_prompt_data(
    raw_prompt, 
    context={"sanitization_rules": {"ip_address": False}}  # Keep IP addresses
)
```

### Privacy-Preserving Analytics

**Best Practice**: Implement privacy-preserving prompt analytics

```python
def track_prompt_usage_privacy_safe(prompt_type: PromptType, user_id: str, metadata: Dict[str, Any]):
    """Track prompt usage without exposing sensitive data"""
    
    # Hash user ID for privacy
    user_hash = hashlib.sha256(f"{user_id}_{SALT}".encode()).hexdigest()[:16]
    
    # Aggregate metadata without personal information
    safe_metadata = {
        "prompt_type": prompt_type.value,
        "timestamp": datetime.utcnow().isoformat(),
        "user_hash": user_hash,
        "environment": metadata.get("environment", "unknown"),
        "complexity_level": metadata.get("complexity_level", "unknown"),
        "response_time_bucket": _get_response_time_bucket(metadata.get("response_time", 0))
    }
    
    # Store aggregated data only
    analytics_service.track_event("prompt_usage", safe_metadata)
```

## Maintenance and Versioning

### Version Control Strategy

**Best Practice**: Implement systematic prompt versioning

```python
class PromptVersionControl:
    """Manage prompt template versions with proper tracking"""
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
        self.version_history = {}
    
    def create_new_version(
        self, 
        prompt_type: PromptType, 
        template: str, 
        changes: str,
        author: str
    ) -> str:
        """Create a new version of a prompt template"""
        
        # Get current version
        current_version = self._get_latest_version(prompt_type)
        new_version = self._increment_version(current_version)
        
        # Create version metadata
        version_metadata = {
            "version": new_version,
            "prompt_type": prompt_type.value,
            "template": template,
            "changes": changes,
            "author": author,
            "created_at": datetime.utcnow().isoformat(),
            "previous_version": current_version,
            "status": "draft"
        }
        
        # Store version
        version_key = f"{prompt_type.value}_v{new_version}"
        self.storage.save_version(version_key, version_metadata)
        
        return new_version
    
    def promote_version(self, prompt_type: PromptType, version: str, environment: str):
        """Promote a version to an environment (staging, production)"""
        
        version_key = f"{prompt_type.value}_v{version}"
        version_data = self.storage.get_version(version_key)
        
        if not version_data:
            raise ValueError(f"Version {version} not found for {prompt_type.value}")
        
        # Update version status
        version_data["status"] = f"deployed_{environment}"
        version_data["deployed_at"] = datetime.utcnow().isoformat()
        
        # Update environment pointer
        env_key = f"{prompt_type.value}_{environment}"
        self.storage.set_environment_version(env_key, version)
        
        self.storage.save_version(version_key, version_data)
```

### Quality Gates

**Best Practice**: Implement quality gates for prompt deployments

```python
class PromptQualityGate:
    """Quality gate system for prompt template deployments"""
    
    def __init__(self, quality_metrics: PromptQualityMetrics):
        self.quality_metrics = quality_metrics
        self.minimum_scores = {
            "staging": {
                "overall_quality": 0.7,
                "completeness": 0.8,
                "structure": 0.6,
                "actionability": 0.7
            },
            "production": {
                "overall_quality": 0.85,
                "completeness": 0.9,
                "structure": 0.8,
                "actionability": 0.8
            }
        }
    
    async def evaluate_prompt_version(
        self, 
        prompt_type: PromptType, 
        version: str, 
        environment: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate prompt version against quality standards"""
        
        results = []
        
        for test_case in test_cases:
            # Generate response with test prompt
            prompt = self._generate_test_prompt(prompt_type, version, test_case["parameters"])
            response = await self._generate_test_response(prompt)
            
            # Calculate quality scores
            scores = self.quality_metrics.calculate_prompt_score(
                response.content,
                expected_elements=test_case.get("expected_elements", []),
                response_time=response.response_time
            )
            
            results.append({
                "test_case": test_case["name"],
                "scores": scores,
                "passed": self._check_quality_thresholds(scores, environment)
            })
        
        # Calculate overall pass rate
        pass_rate = sum(1 for r in results if r["passed"]) / len(results)
        
        return {
            "version": version,
            "environment": environment,
            "pass_rate": pass_rate,
            "test_results": results,
            "approved": pass_rate >= 0.8,  # 80% pass rate required
            "recommendations": self._generate_recommendations(results)
        }
    
    def _check_quality_thresholds(self, scores: Dict[str, float], environment: str) -> bool:
        """Check if scores meet minimum thresholds for environment"""
        thresholds = self.minimum_scores.get(environment, {})
        
        for metric, min_score in thresholds.items():
            if scores.get(metric, 0) < min_score:
                return False
        
        return True
```

### Monitoring and Alerting

**Best Practice**: Monitor prompt performance in production

```python
class PromptPerformanceMonitor:
    """Monitor prompt performance and quality in production"""
    
    def __init__(self, metrics_backend, alerting_service):
        self.metrics = metrics_backend
        self.alerts = alerting_service
        self.performance_thresholds = {
            "response_time_p95": 10.0,  # 95th percentile response time
            "error_rate": 0.05,         # 5% error rate
            "quality_score": 0.75       # Minimum quality score
        }
    
    def track_prompt_performance(
        self, 
        prompt_type: PromptType, 
        response: GenAIResponse, 
        quality_scores: Dict[str, float]
    ):
        """Track prompt performance metrics"""
        
        # Record metrics
        self.metrics.record("prompt_response_time", response.response_time, {
            "prompt_type": prompt_type.value,
            "model": response.model
        })
        
        self.metrics.record("prompt_quality_score", quality_scores.get("overall_quality", 0), {
            "prompt_type": prompt_type.value
        })
        
        # Check for performance issues
        self._check_performance_thresholds(prompt_type, response, quality_scores)
    
    def _check_performance_thresholds(
        self, 
        prompt_type: PromptType, 
        response: GenAIResponse, 
        quality_scores: Dict[str, float]
    ):
        """Check performance against thresholds and alert if needed"""
        
        # Check response time
        if response.response_time > self.performance_thresholds["response_time_p95"]:
            self.alerts.send_alert(
                severity="warning",
                title=f"High response time for {prompt_type.value}",
                description=f"Response time: {response.response_time:.2f}s exceeded threshold"
            )
        
        # Check quality score
        quality_score = quality_scores.get("overall_quality", 0)
        if quality_score < self.performance_thresholds["quality_score"]:
            self.alerts.send_alert(
                severity="warning",
                title=f"Low quality score for {prompt_type.value}",
                description=f"Quality score: {quality_score:.2f} below threshold"
            )
```

## Conclusion

This guide provides a comprehensive framework for creating, optimizing, and maintaining high-quality GenAI prompts. Following these best practices will ensure:

- **Consistent Quality**: Standardized prompt structures and validation
- **Performance Optimization**: Efficient caching and response time management
- **Continuous Improvement**: A/B testing and quality metrics
- **Security**: Data sanitization and privacy protection
- **Maintainability**: Version control and deployment strategies

Remember to regularly review and update your prompts based on user feedback, performance metrics, and changing requirements. The GenAI landscape evolves rapidly, and prompt engineering is both an art and a science that benefits from continuous refinement.

## Additional Resources

- [OCI GenAI Service Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [Prompt Engineering Research Papers](https://github.com/prompt-engineering/prompt-engineering)
- [A/B Testing Statistical Methods](https://docs.scipy.org/doc/scipy/reference/stats.html)
- [Cloud Security Best Practices](https://www.oracle.com/security/cloud-security/)

---

*This document is part of the GenAI CloudOps Dashboard Task 027 - Develop GenAI Prompt Templates and Examples* 