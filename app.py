import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="我的小说书单", page_icon="📚", layout="wide")

# 1. 连接 Google Sheets 数据库
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # 读取数据并清洗空行
        df = conn.read(ttl=0)
        return df.dropna(how="all")
    except Exception:
        # 若表格为空，返回默认数据结构
        return pd.DataFrame(columns=["书名", "作者", "阅读状态", "添加时间", "个人评分", "标签"])

df = load_data()

st.title("📚 我的小说书单")

# 2. 侧边栏：添加/编辑表单
with st.sidebar:
    st.header("📝 记录一本小说")
    with st.form("book_form", clear_on_submit=True):
        name = st.text_input("书名 *")
        author = st.text_input("作者 *")
        status = st.selectbox("阅读状态", ["已读完", "在读中", "待读", "弃坑"])
        add_date = st.date_input("添加时间")
        rating = st.slider("个人评分 (星级)", 1, 5, 5)
        tags = st.text_input("标签 (用逗号分隔，如: 仙侠,古代,强强)")
        
        submitted = st.form_submit_button("保存记录")
        
        if submitted:
            if not name or not author:
                st.error("请填写书名和作者！")
            else:
                stars = "⭐" * rating
                new_row = pd.DataFrame([{
                    "书名": name,
                    "作者": author,
                    "阅读状态": status,
                    "添加时间": str(add_date),
                    "个人评分": stars,
                    "标签": tags
                }])
                
                # 追加新记录并更新 Google Sheets
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("记录已成功保存到云端！")
                st.rerun()

# 3. 顶部数据统计卡片
col1, col2, col3, col4 = st.columns(4)
total_books = len(df)
finished = len(df[df["阅读状态"] == "已读完"]) if not df.empty else 0
reading = len(df[df["阅读状态"] == "在读中"]) if not df.empty else 0
plan = len(df[df["阅读状态"] == "待读"]) if not df.empty else 0

col1.metric("累计记录", f"{total_books} 本")
col2.metric("已读完", f"{finished} 本")
col3.metric("在读中", f"{reading} 本")
col4.metric("待读", f"{plan} 本")

st.divider()

# 4. 数据筛选与主表格展示
if not df.empty:
    col_filter1, col_filter2 = st.columns([1, 2])
    with col_filter1:
        status_filter = st.multiselect(
            "按状态筛选", 
            options=["已读完", "在读中", "待读", "弃坑"], 
            default=["已读完", "在读中", "待读", "弃坑"]
        )
    with col_filter2:
        search_kw = st.text_input("搜索书名 / 作者 / 标签")

    # 执行过滤
    filtered_df = df[df["阅读状态"].isin(status_filter)]
    if search_kw:
        mask = (
            filtered_df["书名"].astype(str).str.contains(search_kw, case=False) |
            filtered_df["作者"].astype(str).str.contains(search_kw, case=False) |
            filtered_df["标签"].astype(str).str.contains(search_kw, case=False)
        )
        filtered_df = filtered_df[mask]

    # 展示列表
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "个人评分": st.column_config.TextColumn("评分"),
            "标签": st.column_config.TextColumn("标签"),
        }
    )
else:
    st.info("目前还没有图书记录，请在左侧边栏添加第一本书吧！")
