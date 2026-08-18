import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="我的小说书单", page_icon="📚", layout="wide")

# 1. 连接 Google Sheets 数据库
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(ttl=0)
        df = df.dropna(how="all")
        # 确保读后感列存在
        if "读后感" not in df.columns:
            df["读后感"] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=["书名", "作者", "阅读状态", "添加时间", "个人评分", "标签", "读后感"])

df = load_data()

st.title("📚 我的小说书单")

# 2. 侧边栏：添加记录（含读后感）
with st.sidebar:
    st.header("📝 记录一本小说")
    with st.form("book_form", clear_on_submit=True):
        name = st.text_input("书名 *")
        author = st.text_input("作者 *")
        status = st.selectbox("阅读状态", ["已读完", "在读中", "待读", "弃坑"])
        add_date = st.date_input("添加时间")
        rating = st.slider("个人评分 (星级)", 1, 5, 5)
        tags = st.text_input("标签 (用逗号分隔，如: 仙侠,古代,强强)")
        review = st.text_area("读后感 / 书评", help="记录你的阅读心得与笔记")
        
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
                    "标签": tags,
                    "读后感": review
                }])
                
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("记录已成功保存到云端！")
                st.rerun()

# 3. 分类与状态看板 (4栏布局)
st.subheader("分类与状态")

status_categories = ["已读完", "在读中", "待读", "弃坑"]
cols = st.columns(4)

for idx, cat_name in enumerate(status_categories):
    with cols[idx]:
        # 过滤出当前状态的书籍
        cat_df = df[df["阅读状态"] == cat_name] if not df.empty else pd.DataFrame()
        count = len(cat_df)
        
        # 卡片头部
        st.markdown(f"**{cat_name} ({count})**")
        
        # 展示框/容器
        with st.container(border=True):
            if not cat_df.empty:
                for _, row in cat_df.iterrows():
                    st.markdown(f"**{row['书名']}**")
                    st.caption(f"作者：{row['作者']}")
                    st.markdown(f"{row['个人评分']}")
                    st.divider()
            else:
                st.caption("暂无")

st.markdown("<br>", unsafe_allow_html=True)

# 4. 下方表格展示与筛选
st.subheader("书单明细与读后感")

if not df.empty:
    col_filter1, col_filter2 = st.columns([1, 2])
    with col_filter1:
        status_filter = st.multiselect(
            "按状态筛选", 
            options=["已读完", "在读中", "待读", "弃坑"], 
            default=["已读完", "在读中", "待读", "弃坑"]
        )
    with col_filter2:
        search_kw = st.text_input("搜索书名 / 作者 / 标签 / 读后感")

    # 执行过滤
    filtered_df = df[df["阅读状态"].isin(status_filter)]
    if search_kw:
        mask = (
            filtered_df["书名"].astype(str).str.contains(search_kw, case=False) |
            filtered_df["作者"].astype(str).str.contains(search_kw, case=False) |
            filtered_df["标签"].astype(str).str.contains(search_kw, case=False) |
            filtered_df["读后感"].astype(str).str.contains(search_kw, case=False)
        )
        filtered_df = filtered_df[mask]

    # 表格主数据展示
    st.dataframe(
        filtered_df[["书名", "作者", "阅读状态", "个人评分", "标签", "添加时间"]],
        use_container_width=True,
        hide_index=True
    )

    # 展开查看具体书籍的读后感
    st.markdown("##### 📖 查看书籍读后感")
    for _, row in filtered_df.iterrows():
        review_text = row.get("读后感", "")
        with st.expander(f"📘 《{row['书名']}》 - {row['作者']} (状态: {row['阅读状态']} | {row['个人评分']})"):
            st.markdown(f"**标签**：`{row['标签']}`")
            st.markdown(f"**添加时间**：{row['添加时间']}")
            st.markdown("**读后感 / 心得**：")
            if review_text and str(review_text).strip():
                st.info(review_text)
            else:
                st.caption("暂未填写读后感。")
else:
    st.info("目前还没有图书记录，请在左侧边栏添加第一本书吧！")
