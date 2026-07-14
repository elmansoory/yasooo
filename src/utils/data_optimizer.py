"""
نظام تحسين البيانات
Data Optimization System
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from functools import lru_cache
import sqlite3


class DataOptimizer:
    """محسن البيانات"""

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """تحسين استخدام الذاكرة لـ DataFrame"""
        optimized_df = df.copy()

        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype

            # تحسين الأعداد الصحيحة
            if col_type != 'object':
                if col_type == 'int64':
                    optimized_df[col] = pd.to_numeric(
                        optimized_df[col], downcast='integer'
                    )
                elif col_type == 'float64':
                    optimized_df[col] = pd.to_numeric(
                        optimized_df[col], downcast='float'
                    )

            # تحسين النصوص
            else:
                num_unique = optimized_df[col].nunique()
                num_total = len(optimized_df[col])

                if num_unique / num_total < 0.5:
                    optimized_df[col] = optimized_df[col].astype('category')

        return optimized_df

    @staticmethod
    def chunk_reader(file_path: str, chunksize: int = 10000) -> pd.DataFrame:
        """قراءة ملف كبير على دفعات"""
        chunks = []
        for chunk in pd.read_csv(file_path, chunksize=chunksize):
            chunks.append(DataOptimizer.optimize_dataframe(chunk))

        return pd.concat(chunks, ignore_index=True)

    @staticmethod
    def lazy_load_database(
        db_path: str,
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """تحميل كسول من قاعدة البيانات"""
        query = f"SELECT "

        if columns:
            query += ", ".join(columns)
        else:
            query += "*"

        query += f" FROM {table}"

        if where:
            query += f" WHERE {where}"

        if limit:
            query += f" LIMIT {limit}"

        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()

        return DataOptimizer.optimize_dataframe(df)

    @staticmethod
    def create_indices(conn: sqlite3.Connection, table: str, columns: List[str]) -> None:
        """إنشاء فهارس لتسريع الاستعلامات"""
        cursor = conn.cursor()

        for col in columns:
            index_name = f"idx_{table}_{col}"
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table}({col})
                """)
            except Exception:
                pass

        conn.commit()

    @staticmethod
    def vacuum_database(db_path: str) -> None:
        """تحسين وتنظيف قاعدة البيانات"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # تحليل قاعدة البيانات
        cursor.execute("ANALYZE")

        # تنظيف المساحة غير المستخدمة
        cursor.execute("VACUUM")

        conn.commit()
        conn.close()


class StreamlitOptimizer:
    """محسن تطبيقات Streamlit"""

    @staticmethod
    def optimize_page_config() -> dict:
        """إعدادات محسنة للصفحة"""
        return {
            'page_title': "نظام التزلج",
            'page_icon': "🎿",
            'layout': "wide",
            'initial_sidebar_state': "collapsed",  # تحميل أسرع
        }

    @staticmethod
    def lazy_import(module_name: str):
        """استيراد كسول للمكتبات الثقيلة"""
        import importlib
        return importlib.import_module(module_name)

    @staticmethod
    def chunk_video_processing(
        video_path: str,
        frame_skip: int = 5
    ) -> List[np.ndarray]:
        """معالجة الفيديو على دفعات"""
        cv2 = StreamlitOptimizer.lazy_import('cv2')

        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_skip == 0:
                # تقليل حجم الإطار
                small_frame = cv2.resize(frame, (640, 480))
                frames.append(small_frame)

            frame_count += 1

        cap.release()
        return frames


class DatabaseConnectionPool:
    """مجمع اتصالات قاعدة البيانات"""

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = []
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """تهيئة مجمع الاتصالات"""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            # تفعيل الأداء الأمثل
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")
            self.connections.append(conn)

    def get_connection(self) -> sqlite3.Connection:
        """الحصول على اتصال من المجمع"""
        if self.connections:
            return self.connections.pop()
        else:
            # إنشاء اتصال جديد إذا نفد المجمع
            return sqlite3.connect(self.db_path, check_same_thread=False)

    def return_connection(self, conn: sqlite3.Connection) -> None:
        """إرجاع اتصال إلى المجمع"""
        if len(self.connections) < self.pool_size:
            self.connections.append(conn)
        else:
            conn.close()

    def close_all(self) -> None:
        """إغلاق جميع الاتصالات"""
        for conn in self.connections:
            conn.close()
        self.connections.clear()


class QueryBuilder:
    """بناء استعلامات محسنة"""

    @staticmethod
    def build_paginated_query(
        table: str,
        page: int,
        page_size: int,
        columns: Optional[List[str]] = None,
        where: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> str:
        """بناء استعلام مع ترقيم الصفحات"""
        select_clause = ", ".join(columns) if columns else "*"
        query = f"SELECT {select_clause} FROM {table}"

        if where:
            query += f" WHERE {where}"

        if order_by:
            query += f" ORDER BY {order_by}"

        offset = (page - 1) * page_size
        query += f" LIMIT {page_size} OFFSET {offset}"

        return query

    @staticmethod
    def build_count_query(
        table: str,
        where: Optional[str] = None
    ) -> str:
        """بناء استعلام للعد"""
        query = f"SELECT COUNT(*) FROM {table}"

        if where:
            query += f" WHERE {where}"

        return query

    @staticmethod
    def build_aggregation_query(
        table: str,
        group_by: str,
        aggregations: Dict[str, str],
        where: Optional[str] = None
    ) -> str:
        """بناء استعلام تجميعي"""
        agg_clauses = []
        for col, func in aggregations.items():
            agg_clauses.append(f"{func}({col}) as {col}_{func.lower()}")

        query = f"SELECT {group_by}, {', '.join(agg_clauses)} FROM {table}"

        if where:
            query += f" WHERE {where}"

        query += f" GROUP BY {group_by}"

        return query


class MemoryOptimizer:
    """محسن استخدام الذاكرة"""

    @staticmethod
    def get_dataframe_memory(df: pd.DataFrame) -> Dict[str, Any]:
        """الحصول على معلومات استخدام الذاكرة"""
        memory_usage = df.memory_usage(deep=True)

        return {
            'total_mb': memory_usage.sum() / 1024 / 1024,
            'by_column': {
                col: f"{memory_usage[col] / 1024:.2f} KB"
                for col in df.columns
            },
            'shape': df.shape,
            'dtypes': df.dtypes.to_dict()
        }

    @staticmethod
    def suggest_optimizations(df: pd.DataFrame) -> List[str]:
        """اقتراح تحسينات للذاكرة"""
        suggestions = []

        for col in df.columns:
            col_type = df[col].dtype

            # اقتراحات للأعداد الصحيحة
            if col_type == 'int64':
                max_val = df[col].max()
                if max_val < 2**15:
                    suggestions.append(f"يمكن تحويل {col} إلى int16")
                elif max_val < 2**31:
                    suggestions.append(f"يمكن تحويل {col} إلى int32")

            # اقتراحات للنصوص
            elif col_type == 'object':
                num_unique = df[col].nunique()
                if num_unique / len(df) < 0.5:
                    suggestions.append(f"يمكن تحويل {col} إلى category")

        return suggestions


# مثال على الاستخدام
if __name__ == "__main__":
    # اختبار التحسينات
    optimizer = DataOptimizer()

    # إنشاء بيانات تجريبية
    df = pd.DataFrame({
        'id': range(10000),
        'name': ['Player'] * 10000,
        'score': np.random.rand(10000) * 100
    })

    print("قبل التحسين:")
    print(MemoryOptimizer.get_dataframe_memory(df))

    df_optimized = optimizer.optimize_dataframe(df)

    print("\nبعد التحسين:")
    print(MemoryOptimizer.get_dataframe_memory(df_optimized))

    print("\nاقتراحات إضافية:")
    for suggestion in MemoryOptimizer.suggest_optimizations(df):
        print(f"  - {suggestion}")
