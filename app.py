import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="我的小说书单", page_icon="📚", layout="wide")

# 1. 连接 Supabase 云数据库
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
  st.error("请先在 Streamlit Cloud 设置 Secrets 中的 SUPABASE_URL 和 SUPABASE_KEY！")
  st.stop()

try:
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
  st.error(f"连接数据库失败，请检查 Secrets 配置：{e}")
  st.stop()


# 2. 读取数据
def load_data():
  try:
    response = supabase.table("books").select("*").execute()
    data = response.data
    if data:
      return pd.DataFrame(data)
  except Exception:
    pass
  return pd.DataFrame(
      columns=[
          "id",
          "书名",
          "作者",
          "阅读状态",
          "添加时间",
          "个人评分",
          "标签",
          "读后感",
      ]
  )


df = load_data()

st.title("📚 我的小说书单")

# 3. 侧边栏：记录小说
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
        new_book = {
            "书名": name,
            "作者": author,
            "阅读状态": status,
            "添加时间": str(add_date),
            "个人评分": stars,
            "标签": tags,
            "读后感": review,
        }

        try:
          supabase.table("books").insert(new_book).execute()
          st.success("记录已成功保存！")
          st.rerun()
        except Exception as err:
          st.error(f"保存失败: {err}")

# 4. 分类看板 (4栏布局)
st.subheader("分类与状态")
status_categories = ["已读完", "在读中", "待读", "弃坑"]
cols = st.columns(4)

for idx, cat_name in enumerate(status_categories):
  with cols[idx]:
    cat_df = df[df["阅读状态"] == cat_name] if not df.empty else pd.DataFrame()
    st.markdown(f"**{cat_name} ({len(cat_df)})**")

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

# 5. 明细列表与管理（包含删除功能）
st.subheader("📖 书单明细与管理")
if not df.empty:
  col_filter1, col_filter2 = st.columns([1, 2])
  with col_filter1:
    status_filter = st.multiselect(
        "按状态筛选",
        options=["已读完", "在读中", "待读", "弃坑"],
        default=["已读完", "在读中", "待读", "弃坑"],
    )
  with col_filter2:
    search_kw = st.text_input("搜索书名 / 作者 / 标签 / 读后感")

  filtered_df = df[df["阅读状态"].isin(status_filter)]
  if search_kw:
    mask = (
        filtered_df["书名"].astype(str).str.contains(search_kw, case=False)
        | filtered_df["作者"].astype(str).str.contains(search_kw, case=False)
        | filtered_df["标签"].astype(str).str.contains(search_kw, case=False)
        | filtered_df["读后感"].astype(str).str.contains(search_kw, case=False)
    )
    filtered_df = filtered_df[mask]

  # 展开折叠显示每本书，包含删除按钮
  for _, row in filtered_df.iterrows():
    book_id = row.get("id")
    book_title = row.get("书名", "")
    author_name = row.get("作者", "")
    review_text = row.get("读后感", "")

    with st.expander(
        f"📘 《{book_title}》 - {author_name} (状态: {row.get('阅读状态', '')} | {row.get('个人评分', '')})"
    ):
      c1, c2 = st.columns([4, 1])
      with c1:
        st.markdown(f"**标签**：`{row.get('标签', '')}`")
        st.markdown(f"**添加时间**：{row.get('添加时间', '')}")
        st.markdown("**读后感 / 心得**：")
        if review_text and str(review_text).strip():
          st.info(review_text)
        else:
          st.caption("暂未填写读后感。")
      with c2:
        # 删除按钮
        if st.button("🗑️ 删除本项", key=f"del_{book_id}"):
          try:
            supabase.table("books").delete().eq("id", book_id).execute()
            st.success(f"《{book_title}》已被删除！")
            st.rerun()
          except Exception as e:
            st.error(f"删除失败: {e}")
else:
  st.info("目前还没有图书记录，请在左侧边栏添加第一本书吧！")
