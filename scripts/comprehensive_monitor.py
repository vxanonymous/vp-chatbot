#!/usr/bin/env python3
# Comprehensive System Monitor
# Monitors endpoints, database queries, and provides optimization recommendations.

import asyncio
import aiohttp
import time
import statistics
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import sys
import os
import logging
from collections import defaultdict

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our monitoring modules
from scripts.endpoint_monitor import EndpointMonitor
from scripts.database_optimizer import DatabaseOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveMonitor:
    # Comprehensive system monitoring and optimization.
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 database_url: str = "mongodb://localhost:27017"):
        self.base_url = base_url
        self.database_url = database_url
        self.endpoint_monitor = EndpointMonitor(base_url)
        self.database_optimizer = DatabaseOptimizer(database_url)
        self.results = {}
        
    async def run_comprehensive_analysis(self, duration: int = 300, 
                                       interval: int = 30) -> Dict[str, Any]:
        # Run comprehensive system analysis.
        print("🚀 Starting comprehensive system analysis...")

        print("🔍 Phase 1: Endpoint Performance Monitoring")
        endpoint_results = await self.endpoint_monitor.monitor_all_endpoints(duration, interval)
        endpoint_analysis = self.endpoint_monitor.analyze_performance(endpoint_results)

        print("🔍 Phase 2: Database Performance Analysis")
        db_performance = await self.database_optimizer.analyze_database_performance()
        db_profile = await self.database_optimizer.profile_query_performance(50)

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "database_url": self.database_url,
            "endpoint_monitoring": endpoint_results,
            "endpoint_analysis": endpoint_analysis,
            "database_performance": db_performance,
            "database_profile": db_profile
        }
        
        return self.results
    
    def generate_comprehensive_report(self) -> str:
        # Generate a comprehensive optimization report.
        endpoint_analysis = self.results.get("endpoint_analysis", {})
        db_performance = self.results.get("database_performance", {})
        db_profile = self.results.get("database_profile", {})
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMPREHENSIVE SYSTEM OPTIMIZATION REPORT                  ║
║                              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 SYSTEM OVERVIEW:
   Base URL: {self.base_url}
   Database URL: {self.database_url}
   Analysis Duration: {len(self.results.get('endpoint_monitoring', {}).get('/health', [])) * 30}s
"""

        if endpoint_analysis.get("performance_summary"):
            report += f"""
🌐 ENDPOINT PERFORMANCE SUMMARY:
"""
            slow_endpoints = len(endpoint_analysis.get("slow_endpoints", []))
            unreliable_endpoints = len(endpoint_analysis.get("unreliable_endpoints", []))
            
            report += f"""
   Total Endpoints Monitored: {len(endpoint_analysis.get("performance_summary", {}))}
   Slow Endpoints: {slow_endpoints}
   Unreliable Endpoints: {unreliable_endpoints}
   Overall Health: {'🟢 Good' if slow_endpoints == 0 and unreliable_endpoints == 0 else '🟡 Fair' if slow_endpoints < 2 else '🔴 Poor'}
"""

            if endpoint_analysis.get("slow_endpoints"):
                report += f"""
🚨 SLOWEST ENDPOINTS:
"""
                for endpoint in sorted(endpoint_analysis["slow_endpoints"], 
                                     key=lambda x: x["avg_response_time"], reverse=True)[:3]:
                    report += f"""
   • {endpoint['endpoint']}: {endpoint['avg_response_time']:.3f}s avg
"""

        if db_performance:
            report += f"""
🗄️ DATABASE PERFORMANCE SUMMARY:
"""
            slow_queries = len([q for q in db_performance.values() if q.get("is_slow", False)])
            critical_queries = len([q for q in db_performance.values() if q.get("is_critical", False)])
            
            report += f"""
   Total Queries Analyzed: {len(db_performance)}
   Slow Queries: {slow_queries}
   Critical Queries: {critical_queries}
   Database Health: {'🟢 Good' if slow_queries == 0 else '🟡 Fair' if critical_queries == 0 else '🔴 Poor'}
"""

            if slow_queries > 0:
                report += f"""
🚨 SLOWEST DATABASE QUERIES:
"""
                slow_queries_list = [(name, data) for name, data in db_performance.items() 
                                   if data.get("is_slow", False)]
                slow_queries_list.sort(key=lambda x: x[1]["execution_time"], reverse=True)
                
                for name, data in slow_queries_list[:3]:
                    report += f"""
   • {name}: {data['execution_time']:.3f}s ({data['complexity']})
"""

        if db_profile:
            report += f"""
📊 QUERY PROFILE SUMMARY:
"""
            excellent_queries = len([q for q in db_profile.values() 
                                   if q.get("performance_rating") == "Excellent"])
            good_queries = len([q for q in db_profile.values() 
                              if q.get("performance_rating") == "Good"])
            poor_queries = len([q for q in db_profile.values() 
                              if q.get("performance_rating") in ["Poor", "Critical"]])
            
            report += f"""
   Excellent Performance: {excellent_queries} queries
   Good Performance: {good_queries} queries
   Poor Performance: {poor_queries} queries
   Overall Query Health: {'🟢 Good' if poor_queries == 0 else '🟡 Fair' if poor_queries < 2 else '🔴 Poor'}
"""

        critical_issues = []
        
        if endpoint_analysis.get("slow_endpoints"):
            critical_issues.append(f"• {len(endpoint_analysis['slow_endpoints'])} slow endpoints detected")
        
        if endpoint_analysis.get("unreliable_endpoints"):
            critical_issues.append(f"• {len(endpoint_analysis['unreliable_endpoints'])} unreliable endpoints detected")
        
        if db_performance:
            critical_queries = len([q for q in db_performance.values() if q.get("is_critical", False)])
            if critical_queries > 0:
                critical_issues.append(f"• {critical_queries} critical database queries detected")
        
        if critical_issues:
            report += f"""
🚨 CRITICAL ISSUES DETECTED:
"""
            for issue in critical_issues:
                report += f"   {issue}\n"

        recommendations = self._generate_comprehensive_recommendations()
        
        if recommendations:
            report += f"""
💡 COMPREHENSIVE OPTIMIZATION RECOMMENDATIONS:
"""
            for category, recs in recommendations.items():
                if recs:
                    report += f"""
   {category.upper()}:
"""
                    for rec in recs:
                        report += f"      {rec}\n"

        report += f"""
🔧 IMPLEMENTATION PRIORITY:
   1. Fix critical database queries (immediate)
   2. Optimize slow endpoints (high priority)
   3. Implement database indexes (high priority)
   4. Add connection pooling (medium priority)
   5. Implement caching strategy (medium priority)
   6. Set up monitoring and alerting (ongoing)

╔══════════════════════════════════════════════════════════════════════════════╗
║                              END OF REPORT                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        return report
    
    def _generate_comprehensive_recommendations(self) -> Dict[str, List[str]]:
        # Generate comprehensive optimization recommendations.
        recommendations = {
            "immediate_actions": [],
            "performance_optimizations": [],
            "infrastructure_improvements": [],
            "monitoring_setup": []
        }
        
        endpoint_analysis = self.results.get("endpoint_analysis", {})
        db_performance = self.results.get("database_performance", {})
        db_profile = self.results.get("database_profile", {})

        if endpoint_analysis.get("unreliable_endpoints"):
            recommendations["immediate_actions"].append("• Add retry logic for unreliable endpoints")
            recommendations["immediate_actions"].append("• Implement circuit breakers")
        
        if db_performance:
            critical_queries = len([q for q in db_performance.values() if q.get("is_critical", False)])
            if critical_queries > 0:
                recommendations["immediate_actions"].append("• Optimize critical database queries")
                recommendations["immediate_actions"].append("• Add query timeout handling")

        if endpoint_analysis.get("slow_endpoints"):
            recommendations["performance_optimizations"].append("• Implement response caching")
            recommendations["performance_optimizations"].append("• Optimize database queries in slow endpoints")
            recommendations["performance_optimizations"].append("• Consider async processing for heavy operations")
        
        if db_performance:
            slow_queries = len([q for q in db_performance.values() if q.get("is_slow", False)])
            if slow_queries > 0:
                recommendations["performance_optimizations"].append("• Add database indexes for slow queries")
                recommendations["performance_optimizations"].append("• Implement query result caching")
                recommendations["performance_optimizations"].append("• Consider read replicas for heavy read operations")

        recommendations["infrastructure_improvements"].extend([
            "• Implement database connection pooling",
            "• Add load balancing for high-traffic endpoints",
            "• Consider horizontal scaling",
            "• Implement rate limiting",
            "• Add CDN for static content"
        ])

        recommendations["monitoring_setup"].extend([
            "• Set up real-time endpoint monitoring",
            "• Implement database query monitoring",
            "• Add performance alerting",
            "• Create automated performance testing",
            "• Set up log aggregation and analysis"
        ])
        
        return recommendations
    
    def save_comprehensive_results(self, filename: str = "comprehensive_analysis.json"):
        # Save comprehensive analysis results.
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Comprehensive analysis results saved to {filename}")
    
    async def run_quick_health_check(self) -> Dict[str, Any]:
        # Run a quick health check of the system.
        print("🔍 Running quick health check...")
        
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "endpoint_health": {},
            "database_health": {},
            "overall_health": "unknown"
        }

        try:
            endpoint_result = await self.endpoint_monitor.test_endpoint("/health")
            health_results["endpoint_health"] = {
                "status": "healthy" if endpoint_result["success"] else "unhealthy",
                "response_time": endpoint_result["response_time"],
                "status_code": endpoint_result["status_code"]
            }
        except Exception as e:
            health_results["endpoint_health"] = {
                "status": "error",
                "error": str(e)
            }

        try:
            db_performance = await self.database_optimizer.analyze_database_performance()
            slow_queries = len([q for q in db_performance.values() if q.get("is_slow", False)])
            critical_queries = len([q for q in db_performance.values() if q.get("is_critical", False)])
            
            health_results["database_health"] = {
                "status": "healthy" if critical_queries == 0 else "degraded" if slow_queries == 0 else "unhealthy",
                "slow_queries": slow_queries,
                "critical_queries": critical_queries
            }
        except Exception as e:
            health_results["database_health"] = {
                "status": "error",
                "error": str(e)
            }

        endpoint_healthy = health_results["endpoint_health"].get("status") == "healthy"
        db_healthy = health_results["database_health"].get("status") in ["healthy", "degraded"]
        
        if endpoint_healthy and db_healthy:
            health_results["overall_health"] = "healthy"
        elif endpoint_healthy or db_healthy:
            health_results["overall_health"] = "degraded"
        else:
            health_results["overall_health"] = "unhealthy"
        
        return health_results

async def main():
    # Main function.
    parser = argparse.ArgumentParser(description="Comprehensive System Monitor")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL to monitor")
    parser.add_argument("--database-url", default="mongodb://localhost:27017", 
                       help="Database connection URL")
    parser.add_argument("--duration", type=int, default=300, 
                       help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=int, default=30, 
                       help="Monitoring interval in seconds")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick health check only")
    parser.add_argument("--output", default="comprehensive_analysis.json", 
                       help="Output file")
    
    args = parser.parse_args()
    
    monitor = ComprehensiveMonitor(args.url, args.database_url)
    
    if args.quick:

        health_results = await monitor.run_quick_health_check()
        print(json.dumps(health_results, indent=2))

        status_emoji = {
            "healthy": "🟢",
            "degraded": "🟡", 
            "unhealthy": "🔴",
            "unknown": "⚪"
        }
        
        print(f"\n📊 QUICK HEALTH CHECK SUMMARY:")
        print(f"{status_emoji.get(health_results['overall_health'], '⚪')} Overall: {health_results['overall_health']}")
        print(f"{status_emoji.get(health_results['endpoint_health'].get('status', 'unknown'), '⚪')} Endpoints: {health_results['endpoint_health'].get('status', 'unknown')}")
        print(f"{status_emoji.get(health_results['database_health'].get('status', 'unknown'), '⚪')} Database: {health_results['database_health'].get('status', 'unknown')}")
        
    else:

        results = await monitor.run_comprehensive_analysis(args.duration, args.interval)
        report = monitor.generate_comprehensive_report()
        print(report)
        monitor.save_comprehensive_results(args.output)

if __name__ == "__main__":
    asyncio.run(main()) 