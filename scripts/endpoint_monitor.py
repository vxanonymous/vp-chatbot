#!/usr/bin/env python3
# Endpoint Performance Monitor
# Monitors API endpoints and database queries for performance issues.

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
from collections import defaultdict

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EndpointMonitor:
    # Monitors endpoint performance and identifies bottlenecks.
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.endpoints = [
            "/health",
            "/api/v1/auth/signup",
            "/api/v1/auth/login", 
            "/api/v1/conversations/",
            "/api/v1/chat/",
            "/api/v1/conversations/{id}",
            "/api/v1/users/profile"
        ]
        self.results = defaultdict(list)
        self.slow_threshold = 1.0
        self.critical_threshold = 5.0
        
    async def test_endpoint(self, endpoint: str, method: str = "GET", 
                          data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        # Test a single endpoint and measure performance.
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=headers, timeout=30) as response:
                        response_time = time.time() - start_time
                        return {
                            "endpoint": endpoint,
                            "method": method,
                            "status_code": response.status,
                            "response_time": response_time,
                            "success": response.status < 400,
                            "timestamp": datetime.now().isoformat()
                        }
                elif method == "POST":
                    async with session.post(url, json=data, headers=headers, timeout=30) as response:
                        response_time = time.time() - start_time
                        return {
                            "endpoint": endpoint,
                            "method": method,
                            "status_code": response.status,
                            "response_time": response_time,
                            "success": response.status < 400,
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def load_test_endpoint(self, endpoint: str, num_requests: int = 10, 
                               concurrent: int = 5) -> Dict[str, Any]:
        # Load test a specific endpoint.
        print(f"🔍 Load testing {endpoint} with {num_requests} requests ({concurrent} concurrent)")
        
        semaphore = asyncio.Semaphore(concurrent)
        
        async def make_request():
            async with semaphore:
                return await self.test_endpoint(endpoint)
        
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        if not valid_results:
            return {"error": "All requests failed"}
        
        response_times = [r["response_time"] for r in valid_results]
        successful = [r for r in valid_results if r["success"]]
        
        return {
            "endpoint": endpoint,
            "total_requests": len(valid_results),
            "successful_requests": len(successful),
            "failed_requests": len(valid_results) - len(successful),
            "success_rate": (len(successful) / len(valid_results)) * 100,
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
            "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)],
            "slow_requests": len([rt for rt in response_times if rt > self.slow_threshold]),
            "critical_requests": len([rt for rt in response_times if rt > self.critical_threshold]),
            "results": valid_results
        }
    
    async def monitor_all_endpoints(self, duration: int = 300, interval: int = 30) -> Dict[str, Any]:
        # Monitor all endpoints continuously.
        print(f"🔍 Starting continuous monitoring for {duration} seconds (interval: {interval}s)")
        
        start_time = time.time()
        monitoring_results = defaultdict(list)
        
        while time.time() - start_time < duration:
            print(f"📊 Monitoring cycle at {datetime.now().strftime('%H:%M:%S')}")
            
            for endpoint in self.endpoints:
                if "{id}" in endpoint:

                    continue
                
                result = await self.test_endpoint(endpoint)
                monitoring_results[endpoint].append(result)

                if result["response_time"] > self.critical_threshold:
                    print(f"🚨 CRITICAL: {endpoint} took {result['response_time']:.2f}s")
                elif result["response_time"] > self.slow_threshold:
                    print(f"⚠️  SLOW: {endpoint} took {result['response_time']:.2f}s")
            
            await asyncio.sleep(interval)
        
        return dict(monitoring_results)
    
    def analyze_performance(self, results: Dict[str, List[Dict]]) -> Dict[str, Any]:
        # Analyze performance data and identify issues.
        analysis = {
            "slow_endpoints": [],
            "unreliable_endpoints": [],
            "recommendations": [],
            "performance_summary": {}
        }
        
        for endpoint, endpoint_results in results.items():
            if not endpoint_results:
                continue
                
            response_times = [r["response_time"] for r in endpoint_results if r["success"]]
            success_rate = len([r for r in endpoint_results if r["success"]]) / len(endpoint_results)
            
            if response_times:
                avg_time = statistics.mean(response_times)
                max_time = max(response_times)
                p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
                
                analysis["performance_summary"][endpoint] = {
                    "avg_response_time": avg_time,
                    "max_response_time": max_time,
                    "p95_response_time": p95_time,
                    "success_rate": success_rate * 100,
                    "total_requests": len(endpoint_results)
                }

                if avg_time > self.slow_threshold:
                    analysis["slow_endpoints"].append({
                        "endpoint": endpoint,
                        "avg_response_time": avg_time,
                        "max_response_time": max_time,
                        "p95_response_time": p95_time
                    })

                if success_rate < 0.95:
                    analysis["unreliable_endpoints"].append({
                        "endpoint": endpoint,
                        "success_rate": success_rate * 100,
                        "avg_response_time": avg_time
                    })

        if analysis["slow_endpoints"]:
            analysis["recommendations"].append("• Implement caching for slow endpoints")
            analysis["recommendations"].append("• Optimize database queries")
            analysis["recommendations"].append("• Consider async processing for heavy operations")
        
        if analysis["unreliable_endpoints"]:
            analysis["recommendations"].append("• Add retry logic for unreliable endpoints")
            analysis["recommendations"].append("• Implement circuit breakers")
            analysis["recommendations"].append("• Add better error handling")
        
        return analysis
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        # Generate a performance report.
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ENDPOINT PERFORMANCE REPORT                          ║
║                              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 PERFORMANCE SUMMARY:
"""
        
        for endpoint, stats in analysis["performance_summary"].items():
            status = "✅" if stats["avg_response_time"] < self.slow_threshold else "⚠️"
            report += f"""
{status} {endpoint}:
   Average Response Time: {stats['avg_response_time']:.3f}s
   Max Response Time: {stats['max_response_time']:.3f}s
   P95 Response Time: {stats['p95_response_time']:.3f}s
   Success Rate: {stats['success_rate']:.1f}%
   Total Requests: {stats['total_requests']}
"""
        
        if analysis["slow_endpoints"]:
            report += f"""
🚨 SLOW ENDPOINTS:
"""
            for endpoint in analysis["slow_endpoints"]:
                report += f"""
   • {endpoint['endpoint']}:
     - Average: {endpoint['avg_response_time']:.3f}s
     - Max: {endpoint['max_response_time']:.3f}s
     - P95: {endpoint['p95_response_time']:.3f}s
"""
        
        if analysis["unreliable_endpoints"]:
            report += f"""
⚠️  UNRELIABLE ENDPOINTS:
"""
            for endpoint in analysis["unreliable_endpoints"]:
                report += f"""
   • {endpoint['endpoint']}:
     - Success Rate: {endpoint['success_rate']:.1f}%
     - Average Response Time: {endpoint['avg_response_time']:.3f}s
"""
        
        if analysis["recommendations"]:
            report += f"""
💡 RECOMMENDATIONS:
"""
            for rec in analysis["recommendations"]:
                report += f"   {rec}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              END OF REPORT                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        return report
    
    def save_results(self, results: Dict[str, Any], filename: str = "endpoint_monitoring.json"):
        # Save monitoring results to file.
        data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "results": results
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results saved to {filename}")

async def main():
    # Main function.
    parser = argparse.ArgumentParser(description="Endpoint Performance Monitor")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL to monitor")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    parser.add_argument("--load-test", help="Load test specific endpoint")
    parser.add_argument("--requests", type=int, default=50, help="Number of requests for load test")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests for load test")
    parser.add_argument("--output", default="endpoint_monitoring.json", help="Output file")
    
    args = parser.parse_args()
    
    monitor = EndpointMonitor(args.url)
    
    if args.load_test:

        result = await monitor.load_test_endpoint(args.load_test, args.requests, args.concurrent)
        print(json.dumps(result, indent=2))
    else:

        results = await monitor.monitor_all_endpoints(args.duration, args.interval)
        analysis = monitor.analyze_performance(results)
        report = monitor.generate_report(analysis)
        print(report)
        monitor.save_results(results, args.output)

if __name__ == "__main__":
    asyncio.run(main()) 