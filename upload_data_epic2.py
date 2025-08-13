import os
import sys
import pandas as pd
from sqlalchemy import create_engine

# === 配置 ===
CSV_PATH = os.path.expanduser("~/Desktop/FIT5120/TA47 On-boarding project/merged_all.csv")
DB_URL   = "postgresql+psycopg2://postgres:eSyUrNgzoGjZybYhxZRwLKaSbAxkQmIQ@trolley.proxy.rlwy.net:13392/railway"
TABLE    = "parking_merged_all"   # 目标表名
IF_EXISTS_MODE = "replace"         # "replace" 或 "append"
CHUNK_SIZE = 100_000               # 分块上传（大文件更稳）

def main():
    if not os.path.exists(CSV_PATH):
        print(f"❌ 找不到 CSV：{CSV_PATH}")
        sys.exit(1)

    # 连接（Railway 需要 SSL）
    print("[1/3] 连接 Postgres ...")
    engine = create_engine(
        DB_URL,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True,
        future=True,
    )

    # 分块读取并写入（不做任何清洗/类型转换）
    print(f"[2/3] 开始上传到表 `{TABLE}`（模式: {IF_EXISTS_MODE}，块: {CHUNK_SIZE} 行）...")
    total = 0
    first = True

    with engine.begin() as conn:
        for chunk in pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE, low_memory=False):
            mode = IF_EXISTS_MODE if first else "append"
            first = False
            chunk.to_sql(
                TABLE,
                con=conn,
                if_exists=mode,
                index=False,
                method="multi",
                chunksize=10_000,   # 批内再分组，提高插入效率
            )
            total += len(chunk)
            print(f"  - 已写入 {total} 行")

    print(f"[3/3] ✅ 完成：{total} 行写入 `{TABLE}`")

if __name__ == "__main__":
    main()
