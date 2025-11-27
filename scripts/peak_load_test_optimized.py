#!/usr/bin/env python3
# Optimized Peak Load Testing Script
# Addresses critical performance issues with improved connection management, database optimization, and realistic user simulation.

import asyncio
import aiohttp
import json
import time
import random
import statistics
import uuid
import psutil
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import argparse
import sys
from dataclasses import dataclass
from contextlib import asynccontextmanager
import logging

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_NUM_USERS = 50
DEFAULT_DURATION = 300
DEFAULT_RAMP_UP = 60

@dataclass
class OptimizedLoadTestConfig:
    # Optimized configuration for peak load testing.
    num_users: int
    duration: int
    ramp_up: int
    max_concurrent_connections: int = 200
    connection_timeout: int = 30
    request_timeout: int = 45  # Reduced from 60s
    retry_attempts: int = 2    # Reduced from 3
    retry_delay: float = 0.5   # Reduced from 1.0
    enable_connection_pooling: bool = True
    enable_keepalive: bool = True
    enable_compression: bool = True
    enable_dns_cache: bool = True
    max_requests_per_connection: int = 100
    connection_ttl: int = 300
    enable_cleanup_closed: bool = True
    user_behavior_variation: float = 0.3
    message_interval_min: float = 1.0
    message_interval_max: float = 3.0
    conversation_frequency: float = 0.15  # Reduced from 0.2
    enable_system_monitoring: bool = True
    monitoring_interval: int = 5

class SystemMonitor:
    # Enhanced system monitoring with resource optimization.
    
    def __init__(self):
        self.metrics = []
        self.start_time = None
        self.end_time = None
    
    def start_monitoring(self):
        # Start system monitoring.
        self.start_time = time.time()
        logger.info("🔍 System monitoring started")
    
    def stop_monitoring(self):
        # Stop system monitoring.
        self.end_time = time.time()
        logger.info("🔍 System monitoring stopped")
    
    def record_metrics(self):
        # Record current system metrics.
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            net_io = psutil.net_io_counters()

            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            
            metrics = {
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'process_memory_rss': process_memory.rss,
                'process_memory_vms': process_memory.vms
            }
            
            self.metrics.append(metrics)

            if cpu_percent > 80:
                logger.warning(f"⚠️  High CPU usage: {cpu_percent}%")
            if memory.percent > 85:
                logger.warning(f"⚠️  High memory usage: {memory.percent}%")
                
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        # Get monitoring summary.
        if not self.metrics:
            return {}
        
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_percent'] for m in self.metrics]
        
        return {
            'cpu_avg': statistics.mean(cpu_values),
            'cpu_max': max(cpu_values),
            'memory_avg': statistics.mean(memory_values),
            'memory_max': max(memory_values),
            'total_samples': len(self.metrics)
        }

class OptimizedUserSimulator:
    # Optimized user simulator with better resource management.
    
    def __init__(self, user_id: int, config: OptimizedLoadTestConfig):
        self.user_id = user_id
        self.config = config
        self.user_token = None
        self.conversation_id = None
        self.session_completed = False
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.start_time = None
        self.end_time = None

        self.behavior_pattern = random.choice(["active", "moderate", "passive"])
        self.message_count = 0
        self.max_messages = random.randint(3, 8)

        self.email = f"user_{user_id}_{uuid.uuid4().hex[:8]}@test.com"
        self.username = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
    
    async def run_session(self, session: aiohttp.ClientSession) -> bool:
        # Run optimized user session.
        self.start_time = time.time()
        
        try:
            if not await self._signup(session):
                logger.error(f"❌ User {self.user_id} signup failed")
                return False
            
            if not await self._create_conversation(session):
                logger.error(f"❌ User {self.user_id} conversation creation failed")
                return False
            
            await self._send_messages(session)
            
            if random.random() < self.config.conversation_frequency:
                await self._get_conversations(session)
            
            self.session_completed = True
            self.end_time = time.time()
            
            behavior_emoji = {"active": "🏃", "moderate": "🚶", "passive": "🐌"}
            logger.info(f"✅ User {self.user_id} session completed ({behavior_emoji[self.behavior_pattern]} {self.behavior_pattern} behavior)")
            return True
            
        except Exception as e:
            logger.error(f"❌ User {self.user_id} session error: {e}")
            return False
    
    async def _signup(self, session: aiohttp.ClientSession) -> bool:
        # Optimized signup with better error handling.
        url = f"{BASE_URL}/auth/signup"
        data = {
            "email": self.email,
            "username": self.username,
            "password": "TestPassword123!",
            "full_name": f"Test User {self.user_id}"
        }
        
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                async with session.post(url, json=data) as response:
                    response_time = time.time() - start_time
                    self._record_request(response_time, response.status in [200, 201])
                    
                    if response.status in [200, 201]:
                        result = await response.json()
                        self.user_token = result.get("access_token")
                        logger.info(f"✅ User {self.user_id} signed up successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️  User {self.user_id} signup attempt {attempt + 1} failed: {response.status} - {error_text}")
                        
            except Exception as e:
                logger.warning(f"⚠️  User {self.user_id} signup attempt {attempt + 1} error: {e}")
            
            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return False
    
    async def _create_conversation(self, session: aiohttp.ClientSession) -> bool:
        # Optimized conversation creation.
        if not self.user_token:
            return False
        
        url = f"{BASE_URL}/conversations/"
        headers = {"Authorization": f"Bearer {self.user_token}"}
        data = {"title": f"Test Conversation {self.user_id}"}
        
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                async with session.post(url, json=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    self._record_request(response_time, response.status in [200, 201])
                    
                    if response.status in [200, 201]:
                        result = await response.json()
                        self.conversation_id = result.get("id")
                        logger.info(f"✅ User {self.user_id} created conversation")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️  User {self.user_id} conversation creation attempt {attempt + 1} failed: {response.status} - {error_text}")
                        
            except Exception as e:
                logger.warning(f"⚠️  User {self.user_id} conversation creation attempt {attempt + 1} error: {e}")
            
            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return False
    
    async def _send_messages(self, session: aiohttp.ClientSession):
        # Optimized message sending with varied intervals.
        if not self.user_token or not self.conversation_id:
            return
        
        url = f"{BASE_URL}/chat/"
        headers = {"Authorization": f"Bearer {self.user_token}"}

        if self.behavior_pattern == "active":
            interval_min = self.config.message_interval_min * 0.7
            interval_max = self.config.message_interval_max * 0.8
        elif self.behavior_pattern == "moderate":
            interval_min = self.config.message_interval_min
            interval_max = self.config.message_interval_max
        else:
            interval_min = self.config.message_interval_min * 1.5
            interval_max = self.config.message_interval_max * 1.8
        
        messages = [
            "I want to plan a vacation to Europe",
            "What are some good destinations for summer?",
            "Tell me about Paris",
            "What's the best time to visit?",
            "How much should I budget?",
            "Any recommendations for hotels?",
            "What about transportation?",
            "Thanks for the help!"
        ]
        
        for i in range(min(self.max_messages, len(messages))):
            if self.message_count >= self.max_messages:
                break
                
            data = {
                "conversation_id": self.conversation_id,
                "message": messages[i]
            }
            
            success = False
            for attempt in range(self.config.retry_attempts):
                try:
                    start_time = time.time()
                    async with session.post(url, json=data, headers=headers) as response:
                        response_time = time.time() - start_time
                        self._record_request(response_time, response.status in [200, 201])
                        
                        if response.status in [200, 201]:
                            logger.info(f"✅ User {self.user_id} sent message {i + 1}")
                            success = True
                            self.message_count += 1
                            break
                        else:
                            error_text = await response.text()
                            logger.warning(f"⚠️  User {self.user_id} message attempt {attempt + 1} failed: {response.status} - {error_text}")
                            
                except Exception as e:
                    logger.warning(f"⚠️  User {self.user_id} message attempt {attempt + 1} error: {e}")
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
            
            if not success:
                logger.error(f"❌ User {self.user_id} failed to send message after {self.config.retry_attempts} attempts")

            interval = random.uniform(interval_min, interval_max)
            await asyncio.sleep(interval)
    
    async def _get_conversations(self, session: aiohttp.ClientSession):
        # Optimized conversation retrieval.
        if not self.user_token:
            return
        
        url = f"{BASE_URL}/conversations/"
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                async with session.get(url, headers=headers) as response:
                    response_time = time.time() - start_time
                    self._record_request(response_time, response.status in [200, 201])
                    
                    if response.status in [200, 201]:
                        logger.info(f"✅ User {self.user_id} retrieved conversations")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️  User {self.user_id} get conversations attempt {attempt + 1} failed: {response.status} - {error_text}")
                        
            except Exception as e:
                logger.warning(f"⚠️  User {self.user_id} get conversations attempt {attempt + 1} error: {e}")
            
            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return False
    
    def _record_request(self, response_time: float, success: bool):
        # Record request metrics.
        self.total_requests += 1
        self.response_times.append(response_time)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        # Get user statistics.
        return {
            "user_id": self.user_id,
            "behavior_pattern": self.behavior_pattern,
            "session_completed": self.session_completed,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times) if self.response_times else 0,
            "min_response_time": min(self.response_times) if self.response_times else 0,
            "max_response_time": max(self.response_times) if self.response_times else 0,
            "message_count": self.message_count,
            "session_duration": self.end_time - self.start_time if self.end_time and self.start_time else 0
        }

class OptimizedLoadTestRunner:
    # Optimized load test runner with enhanced performance.
    
    def __init__(self, config: OptimizedLoadTestConfig):
        self.config = config
        self.users: List[OptimizedUserSimulator] = []
        self.system_monitor = SystemMonitor()
        self.results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0,
            "response_times": [],
            "start_time": None,
            "end_time": None,
            "system_metrics": {},
            "user_statistics": {},
            "performance_assessment": {}
        }
    
    @asynccontextmanager
    async def create_optimized_session(self):
        # Create highly optimized HTTP session.

        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_connections,
            limit_per_host=min(100, self.config.max_concurrent_connections // 2),
            ttl_dns_cache=300,
            use_dns_cache=self.config.enable_dns_cache,
            keepalive_timeout=30 if self.config.enable_keepalive else 0,
            enable_cleanup_closed=self.config.enable_cleanup_closed
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.request_timeout,
            connect=self.config.connection_timeout,
            sock_read=45,
            sock_connect=30
        )

        session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "OptimizedPeakLoadTest/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate" if self.config.enable_compression else "identity",
                "Connection": "keep-alive" if self.config.enable_keepalive else "close"
            }
        )
        
        try:
            yield session
        finally:
            await session.close()
    
    async def run_test(self):
        # Run the optimized peak load test.
        logger.info("🚀 Starting optimized peak load test...")
        logger.info(f"📋 Configuration: {self.config.num_users} users, {self.config.duration}s duration, {self.config.ramp_up}s ramp-up")

        self.users = [OptimizedUserSimulator(i, self.config) for i in range(self.config.num_users)]

        if self.config.enable_system_monitoring:
            self.system_monitor.start_monitoring()
        
        self.results["start_time"] = time.time()
        
        async with self.create_optimized_session() as session:

            logger.info(f"📈 Starting ramp-up phase ({self.config.ramp_up}s)...")
            ramp_up_tasks = []
            
            for i, user in enumerate(self.users):

                start_delay = (i / len(self.users)) * self.config.ramp_up
                task = asyncio.create_task(self._run_user_with_delay(user, session, start_delay))
                ramp_up_tasks.append(task)

            if self.config.enable_system_monitoring:
                monitoring_task = asyncio.create_task(self._monitor_system())

            await asyncio.sleep(self.config.ramp_up)
            logger.info("✅ Ramp-up phase completed")

            logger.info(f"🔥 Starting main test phase ({self.config.duration - self.config.ramp_up}s)...")
            await asyncio.sleep(self.config.duration - self.config.ramp_up)

            logger.info("⏳ Waiting for users to complete...")
            await asyncio.gather(*ramp_up_tasks, return_exceptions=True)

            if self.config.enable_system_monitoring:
                monitoring_task.cancel()
                self.system_monitor.stop_monitoring()
        
        self.results["end_time"] = time.time()
        await self._analyze_results()
    
    async def _run_user_with_delay(self, user: OptimizedUserSimulator, session: aiohttp.ClientSession, delay: float):
        # Run user session with delay.
        if delay > 0:
            await asyncio.sleep(delay)
        await user.run_session(session)
    
    async def _monitor_system(self):
        # Monitor system resources during test.
        while True:
            self.system_monitor.record_metrics()
            await asyncio.sleep(self.config.monitoring_interval)
    
    async def _analyze_results(self):
        # Analyze and display test results.

        for user in self.users:
            stats = user.get_statistics()
            self.results["user_statistics"][user.user_id] = stats
            
            self.results["total_requests"] += stats["total_requests"]
            self.results["successful_requests"] += stats["successful_requests"]
            self.results["failed_requests"] += stats["failed_requests"]
            self.results["response_times"].extend(user.response_times)

        total_time = self.results["end_time"] - self.results["start_time"]
        success_rate = (self.results["successful_requests"] / self.results["total_requests"] * 100) if self.results["total_requests"] > 0 else 0
        
        avg_response_time = statistics.mean(self.results["response_times"]) if self.results["response_times"] else 0
        median_response_time = statistics.median(self.results["response_times"]) if self.results["response_times"] else 0
        min_response_time = min(self.results["response_times"]) if self.results["response_times"] else 0
        max_response_time = max(self.results["response_times"]) if self.results["response_times"] else 0

        system_summary = self.system_monitor.get_summary()

        performance_assessment = self._assess_performance(success_rate, avg_response_time, system_summary)

        self._display_results(
            total_time, success_rate, avg_response_time, median_response_time,
            min_response_time, max_response_time, system_summary, performance_assessment
        )

        self._save_results()
    
    def _assess_performance(self, success_rate: float, avg_response_time: float, system_summary: Dict[str, Any]) -> Dict[str, str]:
        # Assess overall performance.
        assessment = {}

        if success_rate >= 95:
            assessment["success_rate"] = "EXCELLENT"
        elif success_rate >= 90:
            assessment["success_rate"] = "GOOD"
        elif success_rate >= 80:
            assessment["success_rate"] = "FAIR"
        else:
            assessment["success_rate"] = "POOR"

        if avg_response_time <= 2:
            assessment["response_time"] = "EXCELLENT"
        elif avg_response_time <= 5:
            assessment["response_time"] = "GOOD"
        elif avg_response_time <= 10:
            assessment["response_time"] = "FAIR"
        else:
            assessment["response_time"] = "POOR"

        if system_summary.get("cpu_max", 0) <= 70 and system_summary.get("memory_max", 0) <= 80:
            assessment["system_resources"] = "EXCELLENT"
        elif system_summary.get("cpu_max", 0) <= 85 and system_summary.get("memory_max", 0) <= 90:
            assessment["system_resources"] = "GOOD"
        else:
            assessment["system_resources"] = "POOR"
        
        return assessment
    
    def _display_results(self, total_time: float, success_rate: float, avg_response_time: float,
                        median_response_time: float, min_response_time: float, max_response_time: float,
                        system_summary: Dict[str, Any], performance_assessment: Dict[str, str]):
        # Display comprehensive test results.
        print("\n" + "="*80)
        print("📊 OPTIMIZED PEAK LOAD TEST RESULTS")
        print("="*80)
        print(f"⏱️  Test Duration: {total_time:.2f} seconds")
        print(f"👥 Number of Users: {self.config.num_users}")
        print(f"📈 Ramp-up Period: {self.config.ramp_up} seconds")
        print()
        
        print("📊 OVERALL STATISTICS:")
        print(f"   Total Requests: {self.results['total_requests']}")
        print(f"   Successful: {self.results['successful_requests']}")
        print(f"   Failed: {self.results['failed_requests']}")
        print(f"   Success Rate: {success_rate:.2f}%")
        print()
        
        print("⏱️  RESPONSE TIME STATISTICS:")
        print(f"   Average: {avg_response_time:.3f}s")
        print(f"   Median: {median_response_time:.3f}s")
        print(f"   Min: {min_response_time:.3f}s")
        print(f"   Max: {max_response_time:.3f}s")
        if self.results["response_times"]:
            std_dev = statistics.stdev(self.results["response_times"])
            print(f"   Standard Deviation: {std_dev:.3f}s")
            print(f"   95th Percentile: {sorted(self.results['response_times'])[int(len(self.results['response_times'])*0.95)]:.3f}s")
            print(f"   99th Percentile: {sorted(self.results['response_times'])[int(len(self.results['response_times'])*0.99)]:.3f}s")
        print()
        
        print("📈 PERFORMANCE METRICS:")
        requests_per_second = self.results["total_requests"] / total_time if total_time > 0 else 0
        successful_rps = self.results["successful_requests"] / total_time if total_time > 0 else 0
        print(f"   Requests per second: {requests_per_second:.2f}")
        print(f"   Successful requests per second: {successful_rps:.2f}")
        print(f"   Average response time: {avg_response_time:.3f}s")
        print()
        
        if system_summary:
            print("💻 SYSTEM METRICS:")
            print(f"   CPU Usage (avg/max): {system_summary.get('cpu_avg', 0):.1f}% / {system_summary.get('cpu_max', 0):.1f}%")
            print(f"   Memory Usage (avg/max): {system_summary.get('memory_avg', 0):.1f}% / {system_summary.get('memory_max', 0):.1f}%")
            print()
        
        print("🎯 PERFORMANCE ASSESSMENT:")
        for metric, rating in performance_assessment.items():
            emoji = {"EXCELLENT": "🟢", "GOOD": "🟡", "FAIR": "🟠", "POOR": "🔴"}
            print(f"   {metric.replace('_', ' ').title()}: {emoji.get(rating, '⚪')} {rating}")
        print("="*80)
    
    def _save_results(self):
        # Save test results to file.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"peak_load_test_results_optimized_{timestamp}.json"
        
        results_data = {
            "test_config": {
                "num_users": self.config.num_users,
                "duration": self.config.duration,
                "ramp_up": self.config.ramp_up,
                "max_concurrent_connections": self.config.max_concurrent_connections,
                "request_timeout": self.config.request_timeout,
                "retry_attempts": self.config.retry_attempts
            },
            "results": self.results,
            "system_metrics": self.system_monitor.get_summary(),
            "timestamp": timestamp
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            print(f"\n💾 Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def check_server_health():
    # Check if server is running and healthy.
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=10) as response:
                if response.status == 200:
                    logger.info("✅ Server is running and healthy")
                    return True
                else:
                    logger.error(f"❌ Server health check failed: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Server health check error: {e}")
        return False

def main():
    # Main function.
    parser = argparse.ArgumentParser(description="Optimized Peak Load Test")
    parser.add_argument("--users", type=int, default=DEFAULT_NUM_USERS, help="Number of users")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION, help="Test duration in seconds")
    parser.add_argument("--ramp-up", type=int, default=DEFAULT_RAMP_UP, help="Ramp-up period in seconds")
    parser.add_argument("--max-connections", type=int, default=200, help="Maximum concurrent connections")
    parser.add_argument("--timeout", type=int, default=45, help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=2, help="Number of retry attempts")
    
    args = parser.parse_args()

    config = OptimizedLoadTestConfig(
        num_users=args.users,
        duration=args.duration,
        ramp_up=args.ramp_up,
        max_concurrent_connections=args.max_connections,
        request_timeout=args.timeout,
        retry_attempts=args.retries
    )

    if not asyncio.run(check_server_health()):
        print("❌ Server is not running or unhealthy. Please start the server first.")
        sys.exit(1)

    runner = OptimizedLoadTestRunner(config)
    asyncio.run(runner.run_test())

if __name__ == "__main__":
    main() 