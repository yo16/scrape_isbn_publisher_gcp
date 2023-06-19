from get_one_publisher import get_one_publisher
import sqlite3
import time
import random


def get_publishers():
    pub_no_list = (
        {
            "keta": 2,
            "start": 0,
            "end": 19
        },
        {
            "keta": 3,
            "start": 250,
            "end": 699
        },
        {
            "keta": 4,
            "start": 7500,
            "end": 8499
        },
        {
            "keta": 5,
            "start": 86000,
            "end": 89999
        },
        {
            "keta": 6,
            "start": 900000,
            "end": 949999
            #"end": 916227   # 2023/6/8時点の最大
        },
        {
            "keta": 7,
            "start": 9900000,
            "end": 9999999
            #"end": 9913188      # 2023/6/8時点の最大
        }
    )

    # DB接続
    with sqlite3.connect("pub_code.db", isolation_level=None) as conn:  # 自動commit
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS pub(pub_code VARCHAR(10) NOT NULL PRIMARY KEY, pub_name VARCHAR(100))")

        for kse in pub_no_list:
            keta = kse["keta"]
            start = kse["start"]
            end = kse["end"]

            for n in range(start, end+1):   # endの最後の数字も使うから+1
                cur_pub_no = f"{n:0{keta}}"

                # DBにあるか確認
                cur.execute(
                    f"SELECT pub_code, pub_name FROM pub WHERE pub_code='{cur_pub_no}'"
                )
                rec = cur.fetchone()

                # なければ取得
                if rec is None:
                    # ランダムで5～15秒待つ
                    time.sleep(
                        5.0 + 10*random.random()
                    )

                    # cur_pub_noに対応するpublisher名を取得
                    pub_info = get_one_publisher(cur_pub_no)
                    
                    # DBへ格納
                    # 複数一気に入れられるけど、Noneがあるとできないので
                    # １行ずつ入れる
                    for i in pub_info:
                        if i[1] is None:
                            cur.execute(
                                f"INSERT INTO pub values({i[0]}, NULL)"
                            )
                        else:
                            try:
                                cur.execute(
                                    "INSERT INTO pub values(?,?)",
                                    i
                                )
                            except sqlite3.IntegrityError:
                                # 複数の記号が登録されているときについでに登録した場合、
                                # 登録済みのことがあるので、スルーする
                                print(f"already exists pub_code:{i[0]}, pub_name:{i[1]}")
                
                else:
                    # あるなら表示
                    print(f"{rec[0]}: {rec[1]} (already exists)")

    return pub_no_list

