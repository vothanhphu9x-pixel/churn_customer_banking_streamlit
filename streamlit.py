import os
import json
import pandas as pd
import streamlit as st
from graphviz import Digraph

# --- 1. CẤU HÌNH & HẰNG SỐ ---
PROJECT_ROOT = os.getcwd()

DATA_DIR = os.path.join(PROJECT_ROOT, "data")

SCHEMA_PATH = os.path.join(DATA_DIR, "schema.json")
DB_SCHEMA_PATH = os.path.join(DATA_DIR, "database_schema.json")


REQUIRED_KEYS = [
    "Feature", "Category", "Used in Model", "Strength", 
    "DataType", "Description", "Example", "NullPolicy", "BusinessMeaning"
]

# --- 2. XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_schema(raw_data):
    """Chuẩn hóa dữ liệu từ schema.json cho phần chi tiết."""
    if not raw_data: return {}
    normalized = {}
    for table, meta in raw_data.items():
        columns = []
        raw_cols = meta.get("columns", [])
        for idx, col in enumerate(raw_cols):
            norm_col = {
                "Feature": col.get("Feature") or col.get("feature") or f"col_{idx}",
                "Category": col.get("Category") or col.get("category") or "Raw",
                "Used in Model": col.get("Used in Model") or col.get("used_in_model") or "❌",
                "Strength": col.get("Strength") or col.get("strength") or "",
                "DataType": col.get("DataType") or col.get("datatype") or "",
                "Description": col.get("Description") or col.get("description") or "",
                "Example": col.get("Example") or col.get("example") or "",
                "NullPolicy": col.get("NullPolicy") or col.get("nullpolicy") or "NULLABLE",
                "BusinessMeaning": col.get("BusinessMeaning") or col.get("businessmeaning") or ""
            }
            columns.append(norm_col)
        normalized[table] = {
            "description": meta.get("description", ""),
            "columns": columns
        }
    return normalized

def create_sample_csv(columns):
    data = {}
    for col in columns:
        dtype = col["DataType"].lower()
        if "int" in dtype: val = 0
        elif "float" in dtype: val = 0.0
        elif "date" in dtype: val = "2023-01-01"
        elif "bool" in dtype: val = False
        else: val = "example"
        data[col["Feature"]] = [val]
    return pd.DataFrame(data).to_csv(index=False).encode("utf-8")

# --- 3. GIAO DIỆN (UI) ---
def render_sidebar(schema):
    st.sidebar.header("⚙️ Cài đặt")
    if schema:
        st.sidebar.success("✅ Đã load Schema")
    else:
        st.sidebar.error("❌ Lỗi load Schema")
        
    if st.sidebar.button("🔄 Tải lại dữ liệu"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.divider()
    tables = list(schema.keys()) if schema else []
    selected = st.sidebar.radio("📂 Chọn bảng dữ liệu:", tables)
    return selected

def create_erd_node_label(table_name, meta):
    """Tạo nhãn HTML cho node."""
    pk_list = meta.get("pk", [])
    fks = meta.get("fk", {})
    columns = meta.get("columns", {})
    
    # Colors (Dark Theme)
    COLORS = {
        "header_bg": "#2E86C1",
        "header_txt": "#FFFFFF",
        "row_bg": "#262730",
        "row_txt": "#FAFAFA",
        "pk_bg": "#3E414A",
        "type_txt": "#A0A0A0"
    }
    
    label = f'''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="2" BGCOLOR="{COLORS['row_bg']}">
        <TR>
            <TD COLSPAN="2" BGCOLOR="{COLORS['header_bg']}" ALIGN="CENTER">
                <B><FONT COLOR="{COLORS['header_txt']}" POINT-SIZE="10">{table_name}</FONT></B>
            </TD>
        </TR>
    '''
    
    for col_name, col_type in columns.items():
        is_pk = col_name in pk_list
        is_fk = col_name in fks
        bg_color = COLORS['pk_bg'] if is_pk else COLORS['row_bg']
        icon = "🔑 " if is_pk else ("🔗 " if is_fk else "")
        col_display = f"<B>{col_name}</B>" if is_pk else (f"<I>{col_name}</I>" if is_fk else col_name)
        
        label += f'''
        <TR>
            <TD ALIGN="LEFT" BGCOLOR="{bg_color}"><FONT COLOR="{COLORS['row_txt']}" POINT-SIZE="8">{icon}{col_display}</FONT></TD>
            <TD ALIGN="RIGHT" BGCOLOR="{bg_color}"><FONT COLOR="{COLORS['type_txt']}" POINT-SIZE="7">{col_type}</FONT></TD>
        </TR>
        '''
    label += "</TABLE>>"
    return label

def render_graph(db_schema):
    """Vẽ sơ đồ ERD từ database_schema.json"""
    st.header("1. Sơ đồ quan hệ (ERD)")
    
    if not db_schema:
        st.warning("⚠️ Không tìm thấy file database_schema.json")
        return

    # 1. Tìm bảng trung tâm (Hub)
    connections = {t: 0 for t in db_schema}
    for t, meta in db_schema.items():
        fks = meta.get("fk", {})
        connections[t] += len(fks)
        for ref in fks.values():
            if "." in ref:
                ref_table = ref.split(".")[0]
                if ref_table in connections:
                    connections[ref_table] += 1
    central_table = max(connections, key=connections.get) if connections else ""

    # 2. Config Graph (Layout Radial)
    dot = Digraph(comment='ERD')
    dot.engine = 'twopi'
    
    dot.attr(
        root=central_table,
        ranksep="3.0",
        overlap="false",
        splines="ortho",
        bgcolor="#0E1117",
        pad="0.5",
        nodesep="0.8"
    )
    
    dot.attr('node', shape="plain", fontname="Arial")
    dot.attr('edge', fontname="Arial", fontsize="7", color="#888888", penwidth="0.8")

    # 3. Nodes
    for table_name, meta in db_schema.items():
        label = create_erd_node_label(table_name, meta)
        dot.node(table_name, label)

    # 4. Edges
    for table_name, meta in db_schema.items():
        fks = meta.get("fk", {})
        for fk_col, ref in fks.items():
            if "." in ref:
                ref_table = ref.split(".")[0]
                # Kết nối từ bảng đến bảng (không dùng port) để dây đi từ rìa
                dot.edge(
                    ref_table, 
                    table_name,
                    arrowhead="crow", 
                    arrowtail="none",
                    dir="both"
                )

    st.graphviz_chart(dot, use_container_width=True)

def render_table_details(name, data):
    st.divider()
    st.header(f"2. Chi tiết: {name}")
    if data["description"]:
        st.info(data["description"])
    
    df = pd.DataFrame(data["columns"])
    cols_to_show = [c for c in REQUIRED_KEYS if c in df.columns]
    st.dataframe(df[cols_to_show], use_container_width=True)
    
    csv = create_sample_csv(data["columns"])
    st.download_button("📥 Tải CSV mẫu", csv, f"{name}_sample.csv", "text/csv")

# --- 4. MAIN ---
def main():
    st.set_page_config(page_title="Schema Explorer", layout="wide", page_icon="📊")
    st.title("📊 Data Schema Explorer")
    
    # Load data
    raw_schema = load_json(SCHEMA_PATH)
    db_schema = load_json(DB_SCHEMA_PATH)
    
    schema = normalize_schema(raw_schema)
    
    # UI
    selected_table = render_sidebar(schema)
    
    render_graph(db_schema)
    
    if selected_table and selected_table in schema:
        render_table_details(selected_table, schema[selected_table])

if __name__ == "__main__":
    main()
