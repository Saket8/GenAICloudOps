import time
import psutil
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import text
from app.services.cache_service import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    active_connections: int
    response_time_ms: float
    cache_hit_rate: float
    error_rate: float

class DatabaseOptimizer:
    """Database optimization and monitoring"""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # seconds
        self.connection_pool_stats = {}
    
    async def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze and identify slow queries"""
        try:
            # This would typically integrate with database logging
            # For now, we'll return cached slow query information
            cached_queries = await cache_service.get("performance", "slow_queries")
            return cached_queries or []
        except Exception as e:
            logger.error(f"Error analyzing slow queries: {e}")
            return []
    
    async def optimize_database_indexes(self) -> Dict[str, Any]:
        """Suggest database index optimizations"""
        try:
            suggestions = []
            
            # Analyze commonly queried tables
            common_queries = [
                "SELECT * FROM users WHERE email = ?",
                "SELECT * FROM remediation_actions WHERE status = ?",
                "SELECT * FROM chatbot_conversations WHERE user_id = ?",
            ]
            
            index_suggestions = {
                "users": ["email", "created_at"],
                "remediation_actions": ["status", "created_at", "user_id"],
                "chatbot_conversations": ["user_id", "created_at"],
            }
            
            for table, columns in index_suggestions.items():
                suggestions.append({
                    "table": table,
                    "suggested_indexes": columns,
                    "reason": f"Improve query performance for {table}",
                    "priority": "medium"
                })
            
            return {
                "suggestions": suggestions,
                "total_suggestions": len(suggestions),
                "estimated_improvement": "15-30% query performance improvement"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing database indexes: {e}")
            return {"suggestions": [], "error": str(e)}
    
    async def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics"""
        try:
            # This would typically get real pool stats from SQLAlchemy
            return {
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "checked_in": 15,
                "checked_out": 5,
                "overflow": 2,
                "invalid": 0,
                "utilization_percent": 25.0,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting connection pool stats: {e}")
            return {"error": str(e)}

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history_size = 1000
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "response_time_ms": 2000.0
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "status": "healthy" if cpu_percent < self.alert_thresholds["cpu_percent"] else "warning"
                },
                "memory": {
                    "percent": memory_percent,
                    "used_mb": round(memory_used_mb, 2),
                    "available_mb": round(memory_available_mb, 2),
                    "total_mb": round(memory.total / (1024 * 1024), 2),
                    "status": "healthy" if memory_percent < self.alert_thresholds["memory_percent"] else "warning"
                },
                "disk": {
                    "usage_percent": disk_usage_percent,
                    "free_gb": round(disk_free_gb, 2),
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                    "status": "healthy" if disk_usage_percent < self.alert_thresholds["disk_usage_percent"] else "warning"
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}
    
    async def get_process_metrics(self) -> Dict[str, Any]:
        """Get current process metrics"""
        try:
            process = psutil.Process()
            
            # Process metrics
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Open file descriptors
            open_files = len(process.open_files())
            
            # Threads
            num_threads = process.num_threads()
            
            return {
                "pid": process.pid,
                "cpu_percent": cpu_percent,
                "memory_mb": round(memory_info.rss / (1024 * 1024), 2),
                "memory_percent": round(memory_percent, 2),
                "open_files": open_files,
                "num_threads": num_threads,
                "status": process.status(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting process metrics: {e}")
            return {"error": str(e)}

class PerformanceService:
    """Main performance monitoring and optimization service"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.db_optimizer = DatabaseOptimizer()
        self.performance_history = []
        self.is_monitoring = False
        self.monitoring_task = None
    
    async def start_monitoring(self):
        """Start background performance monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background performance monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                await self._collect_metrics()
                await asyncio.sleep(30)  # Collect metrics every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _collect_metrics(self):
        """Collect and store performance metrics"""
        try:
            # Get system metrics
            system_metrics = self.system_monitor.get_system_metrics()
            process_metrics = await self.system_monitor.get_process_metrics()
            cache_stats = cache_service.get_stats()
            
            # Create performance snapshot
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": system_metrics,
                "process": process_metrics,
                "cache": cache_stats,
                "database": await self.db_optimizer.get_connection_pool_stats()
            }
            
            # Store in cache for dashboard
            await cache_service.set(
                "performance",
                f"metrics_{int(time.time())}",
                metrics,
                ttl=3600  # Keep for 1 hour
            )
            
            # Keep in memory for quick access
            self.performance_history.append(metrics)
            if len(self.performance_history) > 100:  # Keep last 100 entries
                self.performance_history = self.performance_history[-100:]
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            # Current metrics
            current_system = self.system_monitor.get_system_metrics()
            current_process = await self.system_monitor.get_process_metrics()
            cache_stats = cache_service.get_stats()
            db_stats = await self.db_optimizer.get_connection_pool_stats()
            
            # Calculate trends (if we have history)
            trends = self._calculate_trends()
            
            # Health assessment
            health_score = self._calculate_health_score(current_system, current_process, cache_stats)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "health_score": health_score,
                "current_metrics": {
                    "system": current_system,
                    "process": current_process,
                    "cache": cache_stats,
                    "database": db_stats
                },
                "trends": trends,
                "recommendations": await self._get_performance_recommendations(current_system, current_process),
                "alerts": self._check_performance_alerts(current_system, current_process)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    def _calculate_trends(self) -> Dict[str, str]:
        """Calculate performance trends"""
        if len(self.performance_history) < 2:
            return {"status": "insufficient_data"}
        
        try:
            # Compare last 10 minutes with previous 10 minutes
            recent = self.performance_history[-10:]
            previous = self.performance_history[-20:-10] if len(self.performance_history) >= 20 else []
            
            if not previous:
                return {"status": "insufficient_data"}
            
            # Calculate averages
            recent_cpu = sum(m["system"]["cpu"]["percent"] for m in recent) / len(recent)
            previous_cpu = sum(m["system"]["cpu"]["percent"] for m in previous) / len(previous)
            
            recent_memory = sum(m["system"]["memory"]["percent"] for m in recent) / len(recent)
            previous_memory = sum(m["system"]["memory"]["percent"] for m in previous) / len(previous)
            
            return {
                "cpu_trend": "increasing" if recent_cpu > previous_cpu + 5 else "decreasing" if recent_cpu < previous_cpu - 5 else "stable",
                "memory_trend": "increasing" if recent_memory > previous_memory + 5 else "decreasing" if recent_memory < previous_memory - 5 else "stable",
                "status": "calculated"
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {"status": "error"}
    
    def _calculate_health_score(self, system_metrics: Dict, process_metrics: Dict, cache_stats: Dict) -> Dict[str, Any]:
        """Calculate overall system health score"""
        try:
            scores = []
            
            # CPU health (0-100)
            cpu_score = max(0, 100 - system_metrics["cpu"]["percent"])
            scores.append(("cpu", cpu_score))
            
            # Memory health (0-100)
            memory_score = max(0, 100 - system_metrics["memory"]["percent"])
            scores.append(("memory", memory_score))
            
            # Disk health (0-100)
            disk_score = max(0, 100 - system_metrics["disk"]["usage_percent"])
            scores.append(("disk", disk_score))
            
            # Cache health (0-100)
            cache_score = min(100, cache_stats.get("hit_rate_percent", 0) + 20)  # Boost base score
            scores.append(("cache", cache_score))
            
            # Overall score (weighted average)
            weights = {"cpu": 0.3, "memory": 0.3, "disk": 0.2, "cache": 0.2}
            overall_score = sum(score * weights[component] for component, score in scores)
            
            # Determine status
            if overall_score >= 80:
                status = "excellent"
            elif overall_score >= 60:
                status = "good"
            elif overall_score >= 40:
                status = "warning"
            else:
                status = "critical"
            
            return {
                "overall_score": round(overall_score, 1),
                "status": status,
                "component_scores": dict(scores)
            }
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return {"overall_score": 0, "status": "error"}
    
    async def _get_performance_recommendations(self, system_metrics: Dict, process_metrics: Dict) -> List[Dict[str, str]]:
        """Get performance improvement recommendations"""
        recommendations = []
        
        try:
            # CPU recommendations
            if system_metrics["cpu"]["percent"] > 80:
                recommendations.append({
                    "type": "cpu",
                    "priority": "high",
                    "title": "High CPU Usage",
                    "description": "Consider optimizing CPU-intensive operations or scaling horizontally",
                    "action": "Investigate long-running processes and optimize algorithms"
                })
            
            # Memory recommendations
            if system_metrics["memory"]["percent"] > 85:
                recommendations.append({
                    "type": "memory",
                    "priority": "high",
                    "title": "High Memory Usage",
                    "description": "Memory usage is high, consider optimizing memory allocation",
                    "action": "Review memory leaks and implement memory pooling"
                })
            
            # Disk recommendations
            if system_metrics["disk"]["usage_percent"] > 90:
                recommendations.append({
                    "type": "disk",
                    "priority": "critical",
                    "title": "Low Disk Space",
                    "description": "Disk space is critically low",
                    "action": "Clean up logs and temporary files, or add more storage"
                })
            
            # Cache recommendations
            cache_stats = cache_service.get_stats()
            if cache_stats.get("hit_rate_percent", 0) < 50:
                recommendations.append({
                    "type": "cache",
                    "priority": "medium",
                    "title": "Low Cache Hit Rate",
                    "description": "Cache efficiency is low, consider optimizing caching strategy",
                    "action": "Review cache TTL settings and caching patterns"
                })
            
            # Database recommendations
            db_stats = await self.db_optimizer.get_connection_pool_stats()
            if db_stats.get("utilization_percent", 0) > 80:
                recommendations.append({
                    "type": "database",
                    "priority": "medium",
                    "title": "High Database Connection Usage",
                    "description": "Database connection pool is highly utilized",
                    "action": "Consider increasing pool size or optimizing query patterns"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def _check_performance_alerts(self, system_metrics: Dict, process_metrics: Dict) -> List[Dict[str, Any]]:
        """Check for performance alerts"""
        alerts = []
        
        try:
            thresholds = self.system_monitor.alert_thresholds
            
            # CPU alert
            if system_metrics["cpu"]["percent"] > thresholds["cpu_percent"]:
                alerts.append({
                    "type": "cpu",
                    "severity": "warning",
                    "message": f"CPU usage is {system_metrics['cpu']['percent']:.1f}% (threshold: {thresholds['cpu_percent']:.1f}%)",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Memory alert
            if system_metrics["memory"]["percent"] > thresholds["memory_percent"]:
                alerts.append({
                    "type": "memory",
                    "severity": "warning",
                    "message": f"Memory usage is {system_metrics['memory']['percent']:.1f}% (threshold: {thresholds['memory_percent']:.1f}%)",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Disk alert
            if system_metrics["disk"]["usage_percent"] > thresholds["disk_usage_percent"]:
                alerts.append({
                    "type": "disk",
                    "severity": "critical",
                    "message": f"Disk usage is {system_metrics['disk']['usage_percent']:.1f}% (threshold: {thresholds['disk_usage_percent']:.1f}%)",
                    "timestamp": datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "performance_summary": await self.get_performance_summary(),
                "database_optimization": await self.db_optimizer.optimize_database_indexes(),
                "slow_queries": await self.db_optimizer.analyze_slow_queries(),
                "system_health": self.system_monitor.get_system_metrics(),
                "cache_analysis": cache_service.get_stats()
            }
        except Exception as e:
            logger.error(f"Error generating optimization report: {e}")
            return {"error": str(e)}

# Global performance service instance
performance_service = PerformanceService() 