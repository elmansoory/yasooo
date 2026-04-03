"""
نظام إدارة التخزين المؤقت
Cache Management System for Performance Optimization
"""

import functools
import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Optional
from datetime import datetime, timedelta
import threading

class CacheManager:
    """مدير التخزين المؤقت المتقدم"""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0
        }
        self.lock = threading.Lock()

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """توليد مفتاح فريد للتخزين المؤقت"""
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str, max_age: Optional[int] = None) -> Optional[Any]:
        """الحصول على قيمة من الذاكرة المؤقتة"""
        with self.lock:
            # التحقق من الذاكرة أولاً
            if key in self.memory_cache:
                data, timestamp = self.memory_cache[key]

                # التحقق من صلاحية الوقت
                if max_age is None or (time.time() - timestamp) < max_age:
                    self.cache_stats['hits'] += 1
                    return data
                else:
                    # حذف البيانات المنتهية الصلاحية
                    del self.memory_cache[key]

            # التحقق من القرص
            cache_file = self.cache_dir / f"{key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        data, timestamp = pickle.load(f)

                    # التحقق من صلاحية الوقت
                    if max_age is None or (time.time() - timestamp) < max_age:
                        # تخزين في الذاكرة للوصول السريع
                        self.memory_cache[key] = (data, timestamp)
                        self.cache_stats['hits'] += 1
                        return data
                    else:
                        # حذف الملف المنتهي الصلاحية
                        cache_file.unlink()
                except Exception:
                    pass

            self.cache_stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """تخزين قيمة في الذاكرة المؤقتة"""
        with self.lock:
            timestamp = time.time()
            self.memory_cache[key] = (value, timestamp)
            self.cache_stats['sets'] += 1

            # التخزين على القرص
            if persist:
                cache_file = self.cache_dir / f"{key}.pkl"
                try:
                    with open(cache_file, 'wb') as f:
                        pickle.dump((value, timestamp), f)
                except Exception:
                    pass

    def clear(self, pattern: Optional[str] = None) -> int:
        """مسح الذاكرة المؤقتة"""
        with self.lock:
            count = 0

            if pattern is None:
                # مسح كل شيء
                count = len(self.memory_cache)
                self.memory_cache.clear()

                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                    count += 1
            else:
                # مسح بناءً على نمط معين
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    count += 1

                    cache_file = self.cache_dir / f"{key}.pkl"
                    if cache_file.exists():
                        cache_file.unlink()

            return count

    def get_stats(self) -> dict:
        """الحصول على إحصائيات الأداء"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0

        return {
            **self.cache_stats,
            'total_requests': total,
            'hit_rate': f"{hit_rate:.2f}%",
            'memory_items': len(self.memory_cache),
            'disk_items': len(list(self.cache_dir.glob("*.pkl")))
        }


# مدير التخزين المؤقت العام
global_cache = CacheManager()


def cached(max_age: int = 3600, persist: bool = True):
    """
    ديكوريتر للتخزين المؤقت

    Args:
        max_age: مدة الصلاحية بالثواني (افتراضي: ساعة واحدة)
        persist: تخزين على القرص (افتراضي: نعم)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # توليد المفتاح
            key = global_cache._generate_key(func.__name__, args, kwargs)

            # محاولة الحصول من الذاكرة المؤقتة
            cached_result = global_cache.get(key, max_age=max_age)
            if cached_result is not None:
                return cached_result

            # تنفيذ الدالة وتخزين النتيجة
            result = func(*args, **kwargs)
            global_cache.set(key, result, persist=persist)

            return result

        return wrapper
    return decorator


def timed_cache(seconds: int):
    """
    تخزين مؤقت مع وقت محدد

    Args:
        seconds: مدة الصلاحية بالثواني
    """
    return cached(max_age=seconds, persist=False)


def clear_cache(pattern: Optional[str] = None) -> int:
    """مسح الذاكرة المؤقتة"""
    return global_cache.clear(pattern=pattern)


def cache_stats() -> dict:
    """الحصول على إحصائيات الأداء"""
    return global_cache.get_stats()


class QueryOptimizer:
    """محسن استعلامات قاعدة البيانات"""

    @staticmethod
    def batch_queries(queries: list, connection) -> list:
        """تنفيذ عدة استعلامات دفعة واحدة"""
        results = []
        cursor = connection.cursor()

        try:
            for query in queries:
                cursor.execute(query)
                results.append(cursor.fetchall())
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()

        return results

    @staticmethod
    def optimize_query(query: str) -> str:
        """تحسين استعلام SQL"""
        # إزالة المسافات الزائدة
        query = ' '.join(query.split())

        # إضافة LIMIT إذا لم يكن موجوداً
        if 'LIMIT' not in query.upper() and 'SELECT' in query.upper():
            # تحذير: قد لا تحتاج كل الاستعلامات إلى LIMIT
            pass

        return query

    @staticmethod
    @cached(max_age=300)  # 5 دقائق
    def cached_query(query: str, connection) -> Any:
        """تنفيذ استعلام مع التخزين المؤقت"""
        import pandas as pd
        return pd.read_sql_query(query, connection)


class PerformanceMonitor:
    """مراقب الأداء"""

    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()

    def record(self, operation: str, duration: float) -> None:
        """تسجيل وقت عملية"""
        with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0
                }

            self.metrics[operation]['count'] += 1
            self.metrics[operation]['total_time'] += duration
            self.metrics[operation]['min_time'] = min(
                self.metrics[operation]['min_time'], duration
            )
            self.metrics[operation]['max_time'] = max(
                self.metrics[operation]['max_time'], duration
            )

    def get_report(self) -> dict:
        """الحصول على تقرير الأداء"""
        with self.lock:
            report = {}
            for operation, data in self.metrics.items():
                avg_time = data['total_time'] / data['count']
                report[operation] = {
                    'calls': data['count'],
                    'avg_time': f"{avg_time:.4f}s",
                    'min_time': f"{data['min_time']:.4f}s",
                    'max_time': f"{data['max_time']:.4f}s",
                    'total_time': f"{data['total_time']:.2f}s"
                }
            return report

    def clear(self) -> None:
        """مسح الإحصائيات"""
        with self.lock:
            self.metrics.clear()


# مراقب الأداء العام
global_monitor = PerformanceMonitor()


def monitor_performance(operation_name: str):
    """ديكوريتر لمراقبة الأداء"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                global_monitor.record(operation_name, duration)
        return wrapper
    return decorator


def performance_report() -> dict:
    """الحصول على تقرير الأداء"""
    return global_monitor.get_report()
