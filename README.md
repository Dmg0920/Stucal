# 家教課程管理系統 (Stucal)

給家教老師與學生家長使用的課程管理 Web App。

## 功能

- **首頁總覽**：今日課程資訊（時間、進度、提醒）；無課時顯示下次上課倒數
- **月曆**：以月份瀏覽所有排定課程
- **課程管理**：新增、編輯課程，記錄預計進度與實際上課內容
- **教材庫**：上傳本地檔案（PDF、Word、PPT 等）或儲存外部連結
- **課程紀錄**：所有已完成課程的時間倒序列表
- **雙角色**：老師 / 家長身份切換；老師備註欄位家長不可見

## 技術架構

| 層級 | 技術 |
|------|------|
| Backend | Django 5.1.4 |
| Database | PostgreSQL（本地開發用 SQLite） |
| Frontend | Django Templates + Tailwind CSS CDN + Alpine.js |
| 靜態檔案 | WhiteNoise |
| 部署 | Zeabur（含 `zbpack.json`） |

## 本地開發

### 1. 安裝依賴

```bash
# 建議使用 uv（速度快）
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

### 2. 初始化資料庫

```bash
.venv/bin/python manage.py makemigrations core
.venv/bin/python manage.py migrate
```

### 3. 啟動伺服器

```bash
.venv/bin/python manage.py runserver
```

瀏覽器開啟 http://127.0.0.1:8000

預設老師密碼：`teacher123`

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `SECRET_KEY` | Django 密鑰 | 開發用預設值（生產環境務必更換） |
| `TEACHER_PASSWORD` | 老師登入密碼 | `teacher123` |
| `DATABASE_URL` | PostgreSQL 連接字串 | 無則使用 SQLite |
| `DJANGO_DEBUG` | 啟用 Debug 模式 | `False` |

## 部署到 Zeabur

1. 登入 [zeabur.com](https://zeabur.com) → New Project
2. Add Service → **PostgreSQL**
3. Add Service → **Git** → 選此 repo
4. 設定環境變數：`SECRET_KEY`、`TEACHER_PASSWORD`、`DATABASE_URL`
5. Deploy

## 專案結構

```
Stucal/
├── manage.py
├── requirements.txt
├── zbpack.json          # Zeabur 部署設定
├── tutoring/            # Django project 設定
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── core/                # 主應用
    ├── models.py        # Material, Session
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── decorators.py    # @teacher_required
    └── templates/core/
```

## 注意事項

- **上傳檔案**：本地開發儲存於 `media/` 目錄；Zeabur 免費版為暫時性儲存，重新部署後會消失
- **老師密碼**：生產環境請設定 `TEACHER_PASSWORD` 環境變數
