#!/usr/bin/env python3
# Comprehensive Load Testing Script
# Addresses specific performance issues and provides detailed analysis.

import asyncio
import aiohttp
import json
import time
import random
import statistics
import uuid
import psutil
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import argparse
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_NUM_USERS = 10
DEFAULT_DURATION = 60
DEFAULT_RAMP_UP = 10

@dataclass
class LoadTestScenario:
    # Load test scenario configuration.
    name: str
    num_users: int
    duration: int
    ramp_up: int
    max_concurrent_connections: int
    request_timeout: int
    description: str

class ComprehensiveUserSimulator:
    # Comprehensive user simulator with realistic behavior patterns.
    
    def __init__(self, user_id: int, session: aiohttp.ClientSession, config: LoadTestScenario):
        self.user_id = user_id
        self.session = session
        self.config = config

        unique_id = str(uuid.uuid4())[:8]
        self.email = f"loadtest{user_id}_{unique_id}@example.com"
        self.password = f"Password{user_id}_{unique_id}123!"
        self.full_name = f"Load Test User {user_id}_{unique_id}"
        self.access_token: Optional[str] = None
        self.conversation_id: Optional[str] = None
        
        self.stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0,
            "response_times": [],
            "errors": [],
            "operations": []
        }
    
    async def make_request(self, method: str, url: str, operation_name: str, **kwargs) -> Tuple[bool, float, Optional[Dict]]:
        # Make HTTP request with comprehensive error handling.
        start_time = time.time()

        if 'timeout' not in kwargs:
            kwargs['timeout'] = aiohttp.ClientTimeout(total=self.config.request_timeout)
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time
                response_data = None
                
                try:
                    response_data = await response.json()
                except:
                    response_data = {"status": response.status}
                
                success = 200 <= response.status < 300

                self.stats["operations"].append({
                    "operation": operation_name,
                    "method": method,
                    "url": url,
                    "response_time": response_time,
                    "success": success,
                    "status_code": response.status,
                    "timestamp": time.time()
                })
                
                return success, response_time, response_data
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            error_msg = f"Timeout after {response_time:.2f}s"
            self.stats["errors"].append(error_msg)
            
            self.stats["operations"].append({
                "operation": operation_name,
                "method": method,
                "url": url,
                "response_time": response_time,
                "success": False,
                "error": error_msg,
                "timestamp": time.time()
            })
            
            return False, response_time, None
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            self.stats["errors"].append(error_msg)
            
            self.stats["operations"].append({
                "operation": operation_name,
                "method": method,
                "url": url,
                "response_time": response_time,
                "success": False,
                "error": error_msg,
                "timestamp": time.time()
            })
            
            return False, response_time, None
    
    async def signup(self) -> bool:
        # Sign up the user with comprehensive retry logic.
        max_retries = 3
        for attempt in range(max_retries):
            success, response_time, data = await self.make_request(
                'POST',
                f"{BASE_URL}/auth/signup",
                "signup",
                json={
                    "email": self.email,
                    "password": self.password,
                    "full_name": self.full_name
                }
            )
            
            self.stats["requests_made"] += 1
            self.stats["total_response_time"] += response_time
            self.stats["response_times"].append(response_time)
            
            if success:
                self.access_token = data.get("access_token")
                self.stats["successful_requests"] += 1
                print(f"✅ User {self.user_id} signed up successfully")
                return True
            elif data and data.get("status") == 422:

                print(f"⚠️  User {self.user_id} already exists, trying login")
                return await self.login()
            else:
                self.stats["failed_requests"] += 1
                print(f"❌ User {self.user_id} signup failed (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
        
        return False
    
    async def login(self) -> bool:
        # Login the user with comprehensive retry logic.
        max_retries = 3
        for attempt in range(max_retries):
            success, response_time, data = await self.make_request(
                'POST',
                f"{BASE_URL}/auth/login",
                "login",
                data={
                    "username": self.email,
                    "password": self.password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            self.stats["requests_made"] += 1
            self.stats["total_response_time"] += response_time
            self.stats["response_times"].append(response_time)
            
            if success:
                self.access_token = data.get("access_token")
                self.stats["successful_requests"] += 1
                print(f"✅ User {self.user_id} logged in successfully")
                return True
            else:
                self.stats["failed_requests"] += 1
                print(f"❌ User {self.user_id} login failed (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
        
        return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        # Get authentication headers.
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    async def create_conversation(self) -> bool:
        # Create a new conversation with comprehensive retry logic.
        if not self.access_token:
            return False
            
        max_retries = 3
        for attempt in range(max_retries):
            success, response_time, data = await self.make_request(
                'POST',
                f"{BASE_URL}/conversations/",
                "create_conversation",
                params={"title": f"User {self.user_id} Vacation Plan"},
                headers=self.get_auth_headers()
            )
            
            self.stats["requests_made"] += 1
            self.stats["total_response_time"] += response_time
            self.stats["response_times"].append(response_time)
            
            if success:
                self.conversation_id = data.get("id")
                self.stats["successful_requests"] += 1
                print(f"✅ User {self.user_id} created conversation")
                return True
            else:
                self.stats["failed_requests"] += 1
                print(f"❌ User {self.user_id} conversation creation failed (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
        
        return False
    
    async def send_chat_message(self, message: str) -> bool:
        # Send a chat message with comprehensive retry logic.
        if not self.access_token:
            return False
            
        max_retries = 3
        for attempt in range(max_retries):
            success, response_time, data = await self.make_request(
                'POST',
                f"{BASE_URL}/chat/",
                "send_message",
                json={
                    "message": message,
                    "conversation_id": self.conversation_id
                },
                headers=self.get_auth_headers()
            )
            
            self.stats["requests_made"] += 1
            self.stats["total_response_time"] += response_time
            self.stats["response_times"].append(response_time)
            
            if success:
                self.stats["successful_requests"] += 1
                print(f"✅ User {self.user_id} sent message")
                return True
            else:
                self.stats["failed_requests"] += 1
                print(f"❌ User {self.user_id} message failed (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
        
        return False
    
    async def get_conversations(self) -> bool:
        # Get user conversations with comprehensive retry logic.
        if not self.access_token:
            return False
            
        max_retries = 3
        for attempt in range(max_retries):
            success, response_time, data = await self.make_request(
                'GET',
                f"{BASE_URL}/conversations/",
                "get_conversations",
                headers=self.get_auth_headers()
            )
            
            self.stats["requests_made"] += 1
            self.stats["total_response_time"] += response_time
            self.stats["response_times"].append(response_time)
            
            if success:
                self.stats["successful_requests"] += 1
                print(f"✅ User {self.user_id} retrieved conversations")
                return True
            else:
                self.stats["failed_requests"] += 1
                print(f"❌ User {self.user_id} get conversations failed (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
        
        return False
    
    async def simulate_realistic_user_session(self, duration: int):
        # Simulate a realistic user session with varied behavior patterns.
        session_start = time.time()

        if not await self.signup():
            print(f"❌ User {self.user_id} authentication failed")
            return

        if not await self.create_conversation():
            print(f"❌ User {self.user_id} conversation creation failed")
            return

        vacation_messages = [
            "I want to plan a vacation to Paris",
            "What are the best attractions to visit?",
            "How much should I budget for a week?",
            "What's the best time of year to visit?",
            "Can you suggest a 5-day itinerary?",
            "What about accommodation recommendations?",
            "How's the public transportation?",
            "Any tips for first-time visitors?",
            "What about food and restaurants?",
            "Is it safe for solo travelers?"
        ]

        behavior_pattern = random.choice(["active", "moderate", "passive"])
        
        if behavior_pattern == "active":
            message_interval = (2, 4)
            conversation_frequency = 0.4
        elif behavior_pattern == "moderate":
            message_interval = (4, 8)
            conversation_frequency = 0.2
        else:
            message_interval = (8, 15)
            conversation_frequency = 0.1
        
        message_index = 0
        last_conversation_check = 0
        
        while time.time() - session_start < duration:

            if message_index < len(vacation_messages):
                await self.send_chat_message(vacation_messages[message_index])
                message_index += 1

            current_time = time.time()
            if current_time - last_conversation_check > 30:
                if random.random() < conversation_frequency:
                    await self.get_conversations()
                    last_conversation_check = current_time

            delay = random.uniform(*message_interval)
            await asyncio.sleep(delay)
        
        print(f"✅ User {self.user_id} session completed ({behavior_pattern} behavior)")

class ComprehensiveLoadTestRunner:
    # Comprehensive load test runner with detailed monitoring and analysis.
    
    def __init__(self, scenario: LoadTestScenario):
        self.scenario = scenario
        self.users: List[ComprehensiveUserSimulator] = []
        self.system_monitor = SystemMonitor()
        self.results = {
            "scenario": scenario.name,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0,
            "response_times": [],
            "start_time": None,
            "end_time": None,
            "system_metrics": {},
            "user_statistics": {},
            "operation_breakdown": {},
            "error_analysis": {}
        }
    
    @asynccontextmanager
    async def create_optimized_session(self):
        # Create optimized HTTP session with connection pooling.

        connector = aiohttp.TCPConnector(
            limit=self.scenario.max_concurrent_connections,
            limit_per_host=min(50, self.scenario.max_concurrent_connections // 2),
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        timeout = aiohttp.ClientTimeout(
            total=self.scenario.request_timeout,
            connect=30,
            sock_read=60
        )
        
        session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "ComprehensiveLoadTest/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate"
            }
        )
        
        try:
            yield session
        finally:
            await session.close()
    
    async def run_load_test(self):
        # Run the comprehensive load test.
        print(f"🚀 Starting comprehensive load test: {self.scenario.name}")
        print(f"📋 Description: {self.scenario.description}")
        print(f"👥 Users: {self.scenario.num_users}")
        print(f"⏱️  Duration: {self.scenario.duration} seconds")
        print(f"📈 Ramp-up: {self.scenario.ramp_up} seconds")
        print(f"🔧 Max Connections: {self.scenario.max_concurrent_connections}")
        print(f"⏰ Timeout: {self.scenario.request_timeout} seconds")
        
        self.results["start_time"] = datetime.now()

        monitoring_task = asyncio.create_task(self._monitor_system())
        
        async with self.create_optimized_session() as session:

            self.users = [ComprehensiveUserSimulator(i, session, self.scenario) for i in range(self.scenario.num_users)]

            tasks = []
            for i, user in enumerate(self.users):
                delay = (i / self.scenario.num_users) * self.scenario.ramp_up
                task = asyncio.create_task(self._start_user_with_delay(user, delay))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ User {i} session failed with exception: {result}")

        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        
        self.results["end_time"] = datetime.now()
        self.results["system_metrics"] = self.system_monitor.get_summary()
        self._calculate_comprehensive_results()
        self._print_comprehensive_results()
    
    async def _monitor_system(self):
        # Monitor system resources during the test.
        while True:
            self.system_monitor.record_metrics()
            await asyncio.sleep(5)
    
    async def _start_user_with_delay(self, user: ComprehensiveUserSimulator, delay: float):
        # Start a user session after a delay.
        await asyncio.sleep(delay)
        try:
            await user.simulate_realistic_user_session(self.scenario.duration)
        except Exception as e:
            print(f"❌ User {user.user_id} session error: {e}")
    
    def _calculate_comprehensive_results(self):
        # Calculate comprehensive test results with detailed analysis.

        for i, user in enumerate(self.users):
            self.results["total_requests"] += user.stats["requests_made"]
            self.results["successful_requests"] += user.stats["successful_requests"]
            self.results["failed_requests"] += user.stats["failed_requests"]
            self.results["total_response_time"] += user.stats["total_response_time"]
            self.results["response_times"].extend(user.stats["response_times"])

            self.results["user_statistics"][f"user_{i}"] = {
                "requests_made": user.stats["requests_made"],
                "successful_requests": user.stats["successful_requests"],
                "failed_requests": user.stats["failed_requests"],
                "success_rate": (user.stats["successful_requests"] / user.stats["requests_made"]) * 100 if user.stats["requests_made"] > 0 else 0,
                "avg_response_time": statistics.mean(user.stats["response_times"]) if user.stats["response_times"] else 0,
                "errors": user.stats["errors"]
            }

        all_operations = []
        for user in self.users:
            all_operations.extend(user.stats["operations"])
        
        operation_types = {}
        for op in all_operations:
            op_type = op["operation"]
            if op_type not in operation_types:
                operation_types[op_type] = {
                    "count": 0,
                    "successful": 0,
                    "failed": 0,
                    "response_times": [],
                    "errors": []
                }
            
            operation_types[op_type]["count"] += 1
            operation_types[op_type]["response_times"].append(op["response_time"])
            
            if op["success"]:
                operation_types[op_type]["successful"] += 1
            else:
                operation_types[op_type]["failed"] += 1
                if "error" in op:
                    operation_types[op_type]["errors"].append(op["error"])

        for op_type, data in operation_types.items():
            data["success_rate"] = (data["successful"] / data["count"]) * 100 if data["count"] > 0 else 0
            data["avg_response_time"] = statistics.mean(data["response_times"]) if data["response_times"] else 0
            data["max_response_time"] = max(data["response_times"]) if data["response_times"] else 0
            data["min_response_time"] = min(data["response_times"]) if data["response_times"] else 0
        
        self.results["operation_breakdown"] = operation_types

        all_errors = []
        for user in self.users:
            all_errors.extend(user.stats["errors"])
        
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        self.results["error_analysis"] = error_counts
    
    def _print_comprehensive_results(self):
        # Print comprehensive load test results.
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE LOAD TEST RESULTS")
        print("="*80)
        
        duration = (self.results["end_time"] - self.results["start_time"]).total_seconds()
        
        print(f"🎯 Scenario: {self.results['scenario']}")
        print(f"⏱️  Test Duration: {duration:.2f} seconds")
        print(f"👥 Number of Users: {self.scenario.num_users}")
        print(f"📈 Ramp-up Period: {self.scenario.ramp_up} seconds")
        print()
        
        print("📊 OVERALL STATISTICS:")
        print(f"   Total Requests: {self.results['total_requests']}")
        print(f"   Successful: {self.results['successful_requests']}")
        print(f"   Failed: {self.results['failed_requests']}")
        
        if self.results["total_requests"] > 0:
            success_rate = (self.results["successful_requests"] / self.results["total_requests"]) * 100
            print(f"   Success Rate: {success_rate:.2f}%")
        
        print()
        
        if self.results["response_times"]:
            print("⏱️  RESPONSE TIME STATISTICS:")
            print(f"   Average: {statistics.mean(self.results['response_times']):.3f}s")
            print(f"   Median: {statistics.median(self.results['response_times']):.3f}s")
            print(f"   Min: {min(self.results['response_times']):.3f}s")
            print(f"   Max: {max(self.results['response_times']):.3f}s")
            
            if len(self.results["response_times"]) > 1:
                print(f"   Standard Deviation: {statistics.stdev(self.results['response_times']):.3f}s")

            sorted_times = sorted(self.results["response_times"])
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            
            if p95_index < len(sorted_times):
                print(f"   95th Percentile: {sorted_times[p95_index]:.3f}s")
            if p99_index < len(sorted_times):
                print(f"   99th Percentile: {sorted_times[p99_index]:.3f}s")
        
        print()
        
        print("📈 PERFORMANCE METRICS:")
        print(f"   Requests per second: {self.results['total_requests'] / duration:.2f}")
        print(f"   Successful requests per second: {self.results['successful_requests'] / duration:.2f}")
        print(f"   Average response time: {self.results['total_response_time'] / self.results['total_requests']:.3f}s")
        
        print()

        print("🔍 OPERATION BREAKDOWN:")
        for op_type, data in self.results["operation_breakdown"].items():
            status = "✅" if data["success_rate"] > 90 else "⚠️" if data["success_rate"] > 80 else "❌"
            print(f"   {status} {op_type}: {data['count']} requests, {data['success_rate']:.1f}% success, {data['avg_response_time']:.3f}s avg")
        
        print()

        if self.results["error_analysis"]:
            print("❌ ERROR ANALYSIS:")
            for error, count in sorted(self.results["error_analysis"].items(), key=lambda x: x[1], reverse=True):
                print(f"   {error}: {count} occurrences")
        
        print()

        if self.results["system_metrics"]:
            print("💻 SYSTEM METRICS:")
            metrics = self.results["system_metrics"]
            print(f"   CPU Usage (avg/max): {metrics.get('cpu_avg', 0):.1f}% / {metrics.get('cpu_max', 0):.1f}%")
            print(f"   Memory Usage (avg/max): {metrics.get('memory_avg', 0):.1f}% / {metrics.get('memory_max', 0):.1f}%")
        
        print("="*80)

        success_rate = (self.results["successful_requests"] / self.results["total_requests"]) * 100 if self.results["total_requests"] > 0 else 0
        avg_response_time = statistics.mean(self.results["response_times"]) if self.results["response_times"] else 0
        
        print("🎯 PERFORMANCE ASSESSMENT:")
        if success_rate >= 95:
            print("   ✅ Success Rate: EXCELLENT")
        elif success_rate >= 90:
            print("   ⚠️  Success Rate: GOOD")
        elif success_rate >= 80:
            print("   ⚠️  Success Rate: FAIR")
        else:
            print("   ❌ Success Rate: POOR")
        
        if avg_response_time <= 1:
            print("   ✅ Response Time: EXCELLENT")
        elif avg_response_time <= 3:
            print("   ⚠️  Response Time: GOOD")
        elif avg_response_time <= 5:
            print("   ⚠️  Response Time: FAIR")
        else:
            print("   ❌ Response Time: POOR")
        
        print("="*80)

class SystemMonitor:
    # Monitor system resources during load testing.
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = []
    
    def record_metrics(self):
        # Record current system metrics.
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.metrics.append({
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_percent': disk.percent,
                'disk_free': disk.free
            })
        except Exception as e:
            print(f"⚠️  System monitoring error: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        # Get system metrics summary.
        if not self.metrics:
            return {}
        
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_percent'] for m in self.metrics]
        
        return {
            'cpu_avg': statistics.mean(cpu_values),
            'cpu_max': max(cpu_values),
            'memory_avg': statistics.mean(memory_values),
            'memory_max': max(memory_values),
            'duration': time.time() - self.start_time
        }

# Predefined test scenarios
TEST_SCENARIOS = {
    "smoke": LoadTestScenario(
        name="Smoke Test",
        num_users=5,
        duration=30,
        ramp_up=5,
        max_concurrent_connections=20,
        request_timeout=30,
        description="Quick validation test"
    ),
    "baseline": LoadTestScenario(
        name="Baseline Test",
        num_users=10,
        duration=60,
        ramp_up=10,
        max_concurrent_connections=50,
        request_timeout=60,
        description="Performance baseline test"
    ),
    "normal": LoadTestScenario(
        name="Normal Load",
        num_users=20,
        duration=120,
        ramp_up=30,
        max_concurrent_connections=100,
        request_timeout=60,
        description="Typical production load"
    ),
    "peak": LoadTestScenario(
        name="Peak Load",
        num_users=50,
        duration=300,
        ramp_up=60,
        max_concurrent_connections=200,
        request_timeout=60,
        description="Maximum expected load"
    ),
    "stress": LoadTestScenario(
        name="Stress Test",
        num_users=100,
        duration=600,
        ramp_up=120,
        max_concurrent_connections=300,
        request_timeout=90,
        description="System capacity testing"
    )
}

async def run_comprehensive_load_test(scenario: LoadTestScenario):
    # Run comprehensive load test with the given scenario.
    runner = ComprehensiveLoadTestRunner(scenario)
    await runner.run_load_test()
    return runner.results

def main():
    # Main function to run comprehensive load tests.
    parser = argparse.ArgumentParser(description="Comprehensive Multi-User Load Testing Script")
    parser.add_argument("--scenario", choices=list(TEST_SCENARIOS.keys()), default="baseline",
                       help="Test scenario to run")
    parser.add_argument("--users", type=int, help="Override number of users")
    parser.add_argument("--duration", type=int, help="Override test duration")
    parser.add_argument("--ramp-up", type=int, help="Override ramp-up period")
    parser.add_argument("--max-connections", type=int, help="Override max concurrent connections")
    parser.add_argument("--timeout", type=int, help="Override request timeout")
    
    args = parser.parse_args()

    scenario = TEST_SCENARIOS[args.scenario]

    if args.users:
        scenario.num_users = args.users
    if args.duration:
        scenario.duration = args.duration
    if args.ramp_up:
        scenario.ramp_up = args.ramp_up
    if args.max_connections:
        scenario.max_concurrent_connections = args.max_connections
    if args.timeout:
        scenario.request_timeout = args.timeout
    
    print("🛡️  Vacation Planning System - Comprehensive Multi-User Load Testing")
    print("="*80)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🎯 Scenario: {scenario.name}")
    print(f"📋 Description: {scenario.description}")
    print(f"👥 Users: {scenario.num_users}")
    print(f"⏱️  Duration: {scenario.duration} seconds")
    print(f"📈 Ramp-up: {scenario.ramp_up} seconds")
    print(f"🔧 Max Connections: {scenario.max_concurrent_connections}")
    print(f"⏰ Timeout: {scenario.request_timeout} seconds")
    print("="*80)

    print("🔍 Checking if server is running...")
    
    async def check_server():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL.replace('/api/v1', '')}/health") as response:
                    if response.status == 200:
                        print("✅ Server is running")
                        return True
                    else:
                        print(f"❌ Server returned status {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return False

    async def main_async():
        if await check_server():
            results = await run_comprehensive_load_test(scenario)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{scenario.name.lower().replace(' ', '_')}_{timestamp}.json"

            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj

            json_results = json.loads(json.dumps(results, default=convert_datetime))
            
            with open(filename, 'w') as f:
                json.dump(json_results, f, indent=2)
            
            print(f"\n💾 Results saved to {filename}")
        else:
            print("❌ Please start the server before running load tests")
            print("   Run: python -m uvicorn app.main:app --reload")
            sys.exit(1)
    
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 