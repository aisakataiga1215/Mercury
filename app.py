import streamlit as st
import uuid
from agent.react_agent import ReactAgent

st.set_page_config(page_title="Mercury", page_icon="◈", layout="wide")

# ── CSS ──────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700;900&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

/* ── Root ─────────────────────────────────────────── */
:root {
    --bg-abyss: #060608;
    --bg-surface: #0b0b10;
    --bg-elevated: #101018;
    --border-ghost: #181820;
    --border-active: #2a2a38;
    --gold: #c9a96e;
    --gold-soft: #e0c78a;
    --gold-dim: #7a6540;
    --mercury: #9898b0;
    --mercury-dim: #5a5a6c;
    --text-primary: #c8c8d4;
    --text-secondary: #707080;
    --text-muted: #3e3e4c;
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
}

/* ── Base ─────────────────────────────────────────── */
.stApp {
    background: var(--bg-abyss);
    background-image:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(201,169,110,0.04) 0%, transparent 70%),
        radial-gradient(ellipse 40% 50% at 85% 20%, rgba(150,150,180,0.03) 0%, transparent 60%);
}
#MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
h1 a, h2 a, h3 a { display: none !important; }

/* Noise grain */
[data-testid="stAppViewContainer"]::before {
    content: ""; position: fixed; inset: 0; z-index: 99999; pointer-events: none;
    opacity: 0.018;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

* { font-family: 'Noto Sans SC', sans-serif; }

/* ── Sidebar ──────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #09090e !important;
    border-right: 1px solid var(--border-ghost) !important;
    box-shadow: inset -1px 0 20px rgba(0,0,0,0.3);
}
[data-testid="stSidebar"] * { color: var(--text-secondary) !important; }
[data-testid="stSidebar"] .stMarkdown p { font-size: 0.78rem; }
[data-testid="stSidebar"] button {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-ghost) !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius-md) !important;
    padding: 8px 16px !important;
    font-size: 0.8rem !important;
    transition: all 0.25s ease !important;
}
[data-testid="stSidebar"] button:hover {
    border-color: var(--gold-dim) !important;
    color: var(--gold) !important;
    background: rgba(201,169,110,0.04) !important;
}
[data-testid="stSidebar"] hr {
    border-color: var(--border-ghost) !important;
    margin: 16px 0 !important;
}
[data-testid="stSidebar"] .stCaption {
    font-family: 'SF Mono','Consolas',monospace !important;
    font-size: 0.7rem !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.04em;
}

/* ── Hero ─────────────────────────────────────────── */
.hero {
    font-family: 'Noto Serif SC', serif;
    font-size: 4.8rem; font-weight: 900; letter-spacing: 0.04em;
    margin: 0.4rem 0 0 0; line-height: 1;
    background: linear-gradient(160deg, #e8d5a3 0%, #c9a96e 18%, #f0e0b8 30%, #b8935a 50%, #d4b878 70%, #9a7a3e 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 2px 12px rgba(201,169,110,0.12));
}
.subhero {
    font-family: 'Noto Sans SC', sans-serif;
    color: var(--mercury-dim);
    font-size: 0.78rem; font-weight: 300;
    letter-spacing: 0.32em;
    margin: 0 0 1.6rem 4px;
    text-transform: uppercase;
}
.gold-rule {
    width: 48px; height: 1px;
    background: linear-gradient(90deg, var(--gold-dim), transparent);
    margin: 0 0 1.6rem 4px;
}

/* ── Think line ───────────────────────────────────── */
.think-line {
    font-size: 0.76rem;
    font-family: 'SF Mono','Consolas','Noto Sans SC',monospace;
    color: var(--mercury-dim);
    margin: 4px 0 12px 0;
    display: flex; align-items: center; gap: 8px;
    padding: 4px 0;
    transition: color 0.4s ease;
}
.think-line .icon { width: 18px; text-align: center; flex-shrink: 0; font-size: 0.8rem; }
.think-line.done { color: var(--text-muted); }
.think-line:not(.done) .spin-icon {
    color: var(--gold);
    text-shadow: 0 0 8px rgba(201,169,110,0.3);
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin-icon { display: inline-block; animation: spin 1.4s linear infinite; }

/* ── Chat Messages ────────────────────────────────── */
/* User bubble */
[data-testid="stChatMessage"][aria-label*="user"] {
    background: transparent !important;
}
[data-testid="stChatMessage"][aria-label*="user"] .stMarkdown p {
    background: var(--bg-elevated);
    border: 1px solid var(--border-ghost);
    border-radius: var(--radius-lg) var(--radius-lg) 4px var(--radius-lg);
    padding: 10px 18px;
    display: inline-block;
    color: var(--text-primary);
    font-size: 0.92rem;
    max-width: 85%;
    line-height: 1.6;
}

/* Assistant text */
[data-testid="stChatMessage"][aria-label*="assistant"] {
    background: transparent !important;
}
[data-testid="stChatMessage"][aria-label*="assistant"] .stMarkdown p {
    color: var(--text-primary);
    font-size: 0.92rem;
    line-height: 1.75;
}
[data-testid="stChatMessage"][aria-label*="assistant"] code {
    font-family: 'SF Mono','Consolas',monospace !important;
    background: var(--bg-elevated);
    border: 1px solid var(--border-ghost);
    border-radius: var(--radius-sm);
    padding: 2px 6px;
    font-size: 0.82rem;
    color: var(--gold-soft);
}
[data-testid="stChatMessage"][aria-label*="assistant"] table {
    width: 100%; border-collapse: collapse;
    font-size: 0.84rem; margin: 12px 0;
    border: 1px solid var(--border-ghost);
    border-radius: var(--radius-md);
    overflow: hidden;
}
[data-testid="stChatMessage"][aria-label*="assistant"] th {
    background: var(--bg-elevated);
    color: var(--gold-soft);
    font-weight: 500;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border-active);
    font-size: 0.78rem;
    letter-spacing: 0.04em;
}
[data-testid="stChatMessage"][aria-label*="assistant"] td {
    padding: 8px 14px;
    border-bottom: 1px solid var(--border-ghost);
    color: var(--text-primary);
}
[data-testid="stChatMessage"][aria-label*="assistant"] tr:last-child td { border-bottom: none; }
[data-testid="stChatMessage"][aria-label*="assistant"] h1,
[data-testid="stChatMessage"][aria-label*="assistant"] h2,
[data-testid="stChatMessage"][aria-label*="assistant"] h3 {
    color: var(--gold-soft);
    font-family: 'Noto Serif SC', serif;
}
[data-testid="stChatMessage"][aria-label*="assistant"] h2 {
    font-size: 1.15rem; margin: 1.2em 0 0.5em 0;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border-ghost);
}
[data-testid="stChatMessage"][aria-label*="assistant"] strong {
    color: var(--gold-soft); font-weight: 500;
}
[data-testid="stChatMessage"][aria-label*="assistant"] blockquote {
    border-left: 2px solid var(--gold-dim);
    padding-left: 14px; margin: 10px 0;
    color: var(--mercury);
}

/* ── Input ────────────────────────────────────────── */
[data-testid="stChatInput"] { background: transparent !important; padding: 8px 0 !important; }
[data-testid="stChatInput"] > div:first-child {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-ghost) !important;
    border-radius: var(--radius-lg) !important;
    display: flex !important; align-items: center !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}
[data-testid="stChatInput"] > div:first-child:focus-within {
    border-color: var(--gold-dim) !important;
    box-shadow: 0 0 0 3px rgba(201,169,110,0.04), 0 0 20px rgba(201,169,110,0.03) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important; color: var(--text-primary) !important;
    border: none !important; outline: none !important;
    padding: 14px 18px !important;
    flex: 1 !important; min-width: 0 !important;
    font-size: 0.9rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; }
[data-testid="stChatInput"] button {
    background: transparent !important; color: var(--text-muted) !important;
    margin: 0 10px 0 0 !important; padding: 6px !important;
    flex-shrink: 0 !important;
    transition: color 0.2s ease !important;
}
[data-testid="stChatInput"] button:hover { color: var(--gold) !important; }

/* ── Misc ─────────────────────────────────────────── */
.stSpinner > div { border-top-color: var(--gold) !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-active); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--mercury-dim); }

@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.stChatMessage { animation: fadeSlideIn 0.35s ease-out; }

/* Empty state */
.empty-hint {
    text-align: center; padding: 60px 20px;
    color: var(--text-muted); font-size: 0.85rem;
}
.empty-hint .icon { font-size: 2.4rem; margin-bottom: 16px; opacity: 0.3; }

/* Responsive */
@media (max-width: 768px) {
    .hero { font-size: 3rem; }
    .subhero { font-size: 0.7rem; letter-spacing: 0.2em; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session ──────────────────────────────────────────────
# 自动清掉旧格式会话
if st.session_state.get("_fmt_ver") != 5:
    st.session_state.clear()
    st.session_state["_fmt_ver"] = 5

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = uuid.uuid4().hex
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
    <div style="text-align:center;padding:28px 0 12px 0;">
      <div style="
        font-family:'Noto Serif SC',serif; font-size:1.8rem; font-weight:700;
        background:linear-gradient(160deg,#c9a96e,#e8d5a3,#b8935a);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        margin-bottom:6px;
      ">◈</div>
      <div style="font-size:0.7rem;letter-spacing:0.28em;color:#5a5a6c;">MERCURY</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption(f"会话  `{st.session_state['thread_id'][:8]}…`")
    if st.button("清除对话记忆"):
        st.session_state["agent"] = ReactAgent()
        st.session_state["thread_id"] = uuid.uuid4().hex
        st.session_state["messages"] = []
        st.rerun()

# ── Header ───────────────────────────────────────────────
st.markdown('<h1 class="hero">Mercury</h1>', unsafe_allow_html=True)
st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
st.markdown('<p class="subhero">电商运营智能体</p>', unsafe_allow_html=True)


# ── 单行思考 HTML ───────────────────────────────────────
def think_html(step: str, live: bool) -> str:
    clean = step.lstrip("✓⟳◌").strip()
    if clean == "完成":
        return '<div class="think-line done"><span class="icon">✓</span>完成</div>'
    icon = (
        '<span class="icon spin-icon">◌</span>'
        if live
        else '<span class="icon">✓</span>'
    )
    cls = "" if live else "done"
    return f'<div class="think-line {cls}">{icon}{clean}</div>'


# ── Chat history ─────────────────────────────────────────
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            if msg.get("step"):
                st.markdown(think_html(msg["step"], live=False), unsafe_allow_html=True)
            st.markdown(msg["content"])

# ── Input ────────────────────────────────────────────────
if prompt := st.chat_input("输入电商运营需求…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    cur_step = ""  # 当前这一步的文本
    reply_text = ""

    with st.chat_message("assistant"):
        think_placeholder = st.empty()
        reply_placeholder = st.empty()
        res = st.session_state["agent"].execute_stream(
            prompt,
            thread_id=st.session_state["thread_id"],
        )
        for chunk in res:
            if chunk.startswith("[think]"):
                cur_step = chunk.removeprefix("[think]").strip()
            elif chunk.startswith("[reply]"):
                reply_text += chunk.removeprefix("[reply]")

            if cur_step:
                think_placeholder.markdown(
                    think_html(cur_step, live=not reply_text),
                    unsafe_allow_html=True,
                )
            if reply_text:
                reply_placeholder.markdown(reply_text)

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": reply_text,
            "step": cur_step,
        }
    )
    st.rerun()
