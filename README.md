# Stucal — 家教課程管理系統

給家教老師與學生（家長）使用的私人課程管理 Web App。支援多位老師各自管理旗下學生、課程、教材。

## 功能總覽

### 老師端
| 功能 | 說明 |
|------|------|
| 帳號申請 | 填寫背景資料後送交審核，通過後方可登入 |
| 學生管理 | 新增學生並取得 8 碼唯一密鑰，切換當前學生 |
| 課程排定 | 新增課程（日期、時段、預計進度、提醒事項） |
| 課程記錄 | 填寫實際上課內容、老師備註（學生不可見） |
| 教材庫 | 上傳本地檔案（PDF、Word、PPT 等）或儲存外部連結；可指定特定學生或共用 |
| 月曆總覽 | 以月份瀏覽所有排定課程 |

### 學生端
| 功能 | 說明 |
|------|------|
| 密鑰加入 | 輸入老師提供的 8 碼密鑰即可加入，首次可自訂顯示名稱 |
| 首頁總覽 | 今日課程資訊；無課時顯示下次上課倒數天數 |
| 課程查閱 | 查看課程詳情（預計進度、實際內容），老師備註欄隱藏 |
| 教材查閱 | 瀏覽共用教材及指定給自己的教材 |
| 課程紀錄 | 所有已完成課程的時間倒序列表 |

### 管理員後台（`/panel/`）
- 審核 / 拒絕老師申請
- 撤銷已核准老師的資格
- 查看全站學生與課程統計

## 技術架構

| 層級 | 技術 |
|------|------|
| Backend | Django 5.1.4 |
| Database | PostgreSQL（本地開發用 SQLite） |
| Frontend | Django Templates + Tailwind CSS CDN + Alpine.js |
| 靜態檔案 | WhiteNoise |
| 部署 | Zeabur (`zbpack.json`) / Render (`render.yaml`) |

## 角色與 Session 設計

```
訪客 → [landing /]
  ├─ 老師登入 → session: teacher_id + current_student_id
  ├─ 學生加入 → session: student_role + student_key
  └─ 管理員   → session: admin_user_id（獨立，不衝突）
```

- 三種角色的 session 互相獨立，切換登入時會自動清除對方 session
- 老師需先選定當前學生，才能進入主要功能頁面

## 本地開發

### 1. 安裝依賴

```bash
# 建議使用 uv（速度較快）
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt

# 或使用 pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 初始化資料庫

```bash
.venv/bin/python manage.py migrate
```

### 3. 建立管理員帳號

```bash
.venv/bin/python manage.py createsuperuser
```

管理員後台位於 `/panel/`，需使用 Django `is_staff` 帳號登入。

### 4. 啟動伺服器

```bash
.venv/bin/python manage.py runserver
```

瀏覽器開啟 `http://127.0.0.1:8000`

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `SECRET_KEY` | Django 密鑰 | 開發用預設值（**生產環境務必更換**） |
| `DATABASE_URL` | PostgreSQL 連接字串 | 無則使用 SQLite |
| `DJANGO_DEBUG` | 啟用 Debug 模式 | `False` |

## 部署

### Zeabur

1. 登入 [zeabur.com](https://zeabur.com) → New Project
2. Add Service → **PostgreSQL**
3. Add Service → **Git** → 選此 repo
4. 設定環境變數：`SECRET_KEY`、`DATABASE_URL`（自動從 PostgreSQL 服務取得）
5. Deploy

### Render

1. 登入 [render.com](https://render.com) → New → Blueprint
2. 選此 repo，Render 會自動讀取 `render.yaml`
3. 建立後進入 service → Environment，手動設定 `SECRET_KEY`
4. 首次部署完成後執行：

```bash
# 於 Render Shell 建立管理員
python manage.py createsuperuser
```

> **注意**：Render 免費方案的磁碟為暫時性儲存，重新部署後上傳的媒體檔案會消失。生產環境建議串接 S3 等物件儲存服務。

## 專案結構

```
Stucal/
├── manage.py
├── requirements.txt
├── render.yaml              # Render 部署設定
├── zbpack.json              # Zeabur 部署設定
├── media/                   # 上傳檔案（本地開發）
├── tutoring/                # Django project 設定
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── core/                    # 主應用
    ├── models.py            # TeacherProfile, Student, Material, Session
    ├── views.py             # 所有 view（老師 / 學生 / 管理員）
    ├── urls.py
    ├── forms.py
    ├── admin.py
    ├── decorators.py        # @teacher_login_required, @student_login_required, @admin_required
    ├── migrations/
    └── templates/core/
        ├── base.html
        ├── landing.html
        ├── home.html
        ├── calendar.html
        ├── session_detail.html
        ├── session_form.html
        ├── materials.html
        ├── material_form.html
        ├── history.html
        ├── teacher_login.html
        ├── teacher_register.html
        ├── teacher_pending.html
        ├── student_list.html
        ├── student_form.html
        ├── student_join.html
        ├── student_setname.html
        ├── panel_login.html
        └── panel_dashboard.html
```

## 資料模型

```
TeacherProfile ─┬─< Student ─┬─< Session >─< Material
  (User 1:1)    │            │
                └────────────┘ Material 可指定給特定學生或設為共用（student=NULL）
```

- **TeacherProfile**：關聯 Django User，需經管理員審核才能啟用
- **Student**：屬於某位老師；含唯一 `access_key`（8 碼），學生以此加入
- **Session**：課程紀錄，狀態分為 `scheduled` / `completed` / `cancelled`
- **Material**：教材，可掛載連結或上傳檔案，並可透過 M2M 關聯到課程
