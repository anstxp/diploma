# HEMAX Frontend

Vue.js 3 frontend для HEMAX — медичної платформи аналізів. Стиль успадкований від попереднього проекту Books-UI, адаптований під медичний контекст.

## Що всередині

- Vue 3 + Vuex 4 + Vue Router 4
- SCSS з CSS variables (палітра `#415A77` / `#1B263B` / `#0D1B2A`)
- Poppins font
- Axios клієнт з JWT refresh token rotation
- Інтеграція з C# backend (`http://localhost:5050/api/*`)
- Підтримка ролей: `User`, `Doctor`, `Administrator`

## Запуск

```bash
npm install
npm run serve
```

Frontend стартує на `http://localhost:8080`. Запит до `/api/*` проксується на backend `http://localhost:5050`.

Перед запуском переконайся:
- C# backend запущений: `cd ~/Downloads/hemax_backend/HEMAX.Web && dotnet run --urls "http://localhost:5050"`
- MSSQL контейнер живий: `docker ps | grep mclaren`
- Python ML services підняті (для submit аналізів): `docker compose up -d`

## Demo credentials

Після того як backend запустився і засіяв юзерів:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@hemax.local | Admin#12345 |
| Doctor | doctor@hemax.local | Doctor#12345 |
| User | patient@hemax.local | Patient#12345 |

## Структура

```
src/
├── api/                      # axios клієнти
├── components/
│   ├── nav-components/       # header, navbar, footer, bottom-navbar
│   ├── auth-components/      # sign-in, sign-up, edit-user
│   ├── analysis-components/  # CBC, CHEM, RISK, NEURO, DERMA forms
│   ├── patient-components/
│   ├── blog-components/
│   └── UI/                   # features, hero, FAQ, contacts, newsletter
├── views/
│   ├── HomeView.vue
│   ├── AnalysesView.vue
│   ├── NewAnalysisView.vue
│   ├── AnalysisDetailsView.vue
│   ├── BlogPostsView.vue
│   ├── SignInView.vue
│   ├── UserHome.vue
│   └── admin/
│       ├── DashboardView.vue
│       ├── UsersView.vue
│       └── AuditLogView.vue
├── store/
│   ├── index.js
│   └── modules/
│       ├── auth.js
│       ├── analyses.js
│       ├── patients.js
│       ├── blog.js
│       └── notifications.js
├── router/index.js
├── App.vue
└── main.js
```
