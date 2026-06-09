OPNs_Project
1. 项目名称

基于 OPNs-SVM/SVR 的 IgAN 病理标签预测与 AI 辅助分析系统

本项目用于完成软件工程专业硕士“专业实践”任务，并服务于毕业论文《基于有序规范实数对的支持向量机算法研究与应用》的应用系统部分。

系统以 IgA 肾病 IgAN 表格数据为主要应用场景，支持 M、E、S、T、C 病理标签分类预测，同时保留 OPNs-SVR 连续指标回归模块，用于支撑论文中的回归算法应用。

2. 当前项目目录

当前项目在 WSL2 中创建，根目录命名为：

OPNs_Project

初始目录结构如下：

OPNs_Project/
├── frontend/
├── backend/
└── README.md

后续开发完成后，推荐扩展为：

OPNs_Project/
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   ├── storage/
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
│
├── docs/
│   ├── api_design.md
│   ├── database_design.md
│   ├── development_log.md
│   └── experiment_notes.md
│
├── .gitignore
├── README.md
└── LICENSE

其中：

frontend/：React 前端项目。
backend/：FastAPI 后端项目。
docs/：系统设计文档、接口文档、数据库设计、开发记录。
README.md：项目总说明和开发任务说明。
.gitignore：Git 忽略规则。
3. 开发环境
3.1 操作环境

本项目开发环境为：

Windows + WSL2 + Ubuntu
VS Code + WSL 扩展
Codex CLI
Git
Node.js
Python

开发时应优先在 WSL2 的 Linux 文件系统中操作项目，例如：

cd ~
mkdir OPNs_Project
cd OPNs_Project

不建议将项目放在 /mnt/c/Users/... 下进行高频开发。WSL2 Linux 文件系统中的文件访问性能通常更适合 Node.js、Python 依赖安装和大量文件读写。

4. VS Code + WSL 使用方式

在 Windows 中安装 VS Code 后，安装扩展：

WSL

进入 WSL2 终端后，在项目根目录执行：

cd ~/OPNs_Project
code .

此时 VS Code 会通过 Remote WSL 打开当前 Linux 项目目录。

后续开发、终端命令、Codex CLI、Git 命令均建议在 VS Code 的 WSL 终端中执行。

5. Codex CLI 使用约定

本项目计划使用 Codex CLI 辅助开发。

Codex CLI 的使用原则：

1. 每次只让 Codex 完成一个明确模块。
2. 不要一次性要求 Codex 完成整个系统。
3. 每次修改前先查看 git status。
4. 每次修改后必须检查 git diff。
5. 每个阶段功能可运行后再提交 Git。
6. 不允许 Codex 删除已有核心文件，除非明确说明。
7. 不允许 Codex 硬编码 API Key、数据库密码或个人隐私数据。
8. 不允许 Codex 输出医学诊断、治疗建议或用药建议。

推荐 Codex CLI 工作流程：

cd ~/OPNs_Project

git status

codex

# Codex 完成修改后
git status
git diff

# 运行必要检查
# 前端
cd frontend
npm run lint
npm run build

# 后端
cd ../backend
python -m compileall app

# 回到根目录提交
cd ..
git add .
git commit -m "feat: implement xxx module"

如果某个阶段尚未配置 lint 或 build，则先执行可用的基础检查，例如：

python -m compileall app

或：

npm run build
6. Git 版本控制要求
6.1 初始化 Git

在项目根目录执行：

cd ~/OPNs_Project
git init

创建 .gitignore：

touch .gitignore

推荐 .gitignore 内容：

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.venv/
venv/
env/
*.egg-info/
.pytest_cache/
.mypy_cache/

# FastAPI / backend local files
backend/.env
backend/opns_medical.db
backend/storage/datasets/*
backend/storage/models/*
backend/storage/predictions/*
backend/storage/reports/*
!backend/storage/datasets/.gitkeep
!backend/storage/models/.gitkeep
!backend/storage/predictions/.gitkeep
!backend/storage/reports/.gitkeep

# Node / React
frontend/node_modules/
frontend/dist/
frontend/.env
frontend/.env.local

# Logs
*.log
logs/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/

为 storage 子目录保留空目录：

mkdir -p backend/storage/datasets
mkdir -p backend/storage/models
mkdir -p backend/storage/predictions
mkdir -p backend/storage/reports

touch backend/storage/datasets/.gitkeep
touch backend/storage/models/.gitkeep
touch backend/storage/predictions/.gitkeep
touch backend/storage/reports/.gitkeep

首次提交：

git add .
git commit -m "chore: initialize OPNs project structure"
6.2 分支建议

个人开发阶段可以直接使用 main 分支。

如果希望更规范，可以使用功能分支：

git checkout -b feature/auth-module
git checkout -b feature/dataset-upload
git checkout -b feature/opns-svm-training
git checkout -b feature/ai-analysis

合并前检查：

git status
git diff

合并：

git checkout main
git merge feature/auth-module
6.3 提交信息规范

推荐使用简化版 Conventional Commits：

feat: 新功能
fix: 修复问题
docs: 文档修改
style: 代码格式修改
refactor: 重构
test: 测试相关
chore: 工程配置或依赖调整

示例：

git commit -m "feat: implement user authentication api"
git commit -m "feat: add dataset upload and preview"
git commit -m "feat: implement OPNs transformer"
git commit -m "fix: handle missing values in dataset profiling"
git commit -m "docs: update development specification"
6.4 每次 Codex 修改后的 Git 检查

每次 Codex 完成代码修改后，必须执行：

git status
git diff

如果修改较多，使用：

git diff --stat

必要时查看单个文件：

git diff backend/app/main.py
git diff frontend/src/App.tsx

确认无误后再提交：

git add .
git commit -m "feat: describe completed module"
7. 技术栈
7.1 前端
React
TypeScript
Vite
Ant Design
ECharts
Axios
React Router
Zustand 或 Redux Toolkit
7.2 后端
Python
FastAPI
SQLAlchemy
Pydantic
pandas
numpy
scikit-learn
joblib
passlib 或 bcrypt
python-jose 或 PyJWT
openpyxl
python-multipart
7.3 数据库

开发阶段优先使用 SQLite：

DATABASE_URL=sqlite:///./opns_medical.db

增强版本支持 PostgreSQL：

DATABASE_URL=postgresql://postgres:password@localhost:5432/opns_medical

推荐通过 SQLAlchemy 统一数据库访问逻辑，使 SQLite 和 PostgreSQL 可切换。

8. 系统总体功能

系统应包含以下模块：

1. 用户登录注册模块
2. 数据集管理模块
3. 文件导入模块
4. 数据预览模块
5. 数据可视化模块
6. OPNs 特征构造模块
7. OPNs-SVM 分类建模模块
8. OPNs-SVR 回归建模模块
9. IgAN 单病例预测模块
10. 批量预测模块
11. 模型评估与对比模块
12. AI 辅助数据分析模块
13. AI 辅助模型结果分析模块
14. AI 辅助预测结果说明模块
15. 报告导出模块
9. 系统核心业务流程
用户注册/登录
    ↓
创建数据集
    ↓
上传 CSV/XLSX 文件
    ↓
数据预览与数据质量分析
    ↓
选择任务类型
    ↓
选择目标变量
    ↓
配置 OPNs 特征构造方式
    ↓
训练模型
    ↓
查看模型评估结果
    ↓
AI 生成结果分析
    ↓
单病例预测或批量预测
    ↓
导出预测结果或实验报告
10. 前端设计
10.1 前端目录结构
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── router/
│   │   └── index.tsx
│   ├── api/
│   │   ├── request.ts
│   │   ├── auth.ts
│   │   ├── datasets.ts
│   │   ├── models.ts
│   │   ├── predictions.ts
│   │   ├── evaluation.ts
│   │   └── ai.ts
│   ├── store/
│   │   └── authStore.ts
│   ├── layouts/
│   │   ├── AppLayout.tsx
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── dashboard/
│   │   │   └── DashboardPage.tsx
│   │   ├── datasets/
│   │   │   ├── DatasetListPage.tsx
│   │   │   ├── DatasetCreatePage.tsx
│   │   │   ├── DatasetDetailPage.tsx
│   │   │   ├── DatasetPreviewPage.tsx
│   │   │   └── DatasetProfilePage.tsx
│   │   ├── models/
│   │   │   ├── ModelListPage.tsx
│   │   │   ├── ModelTrainPage.tsx
│   │   │   ├── ModelDetailPage.tsx
│   │   │   └── ModelEvaluationPage.tsx
│   │   ├── prediction/
│   │   │   ├── IganSinglePredictionPage.tsx
│   │   │   ├── BatchPredictionPage.tsx
│   │   │   └── PredictionHistoryPage.tsx
│   │   ├── ai/
│   │   │   ├── DatasetAIAnalysisPage.tsx
│   │   │   ├── ModelAIAnalysisPage.tsx
│   │   │   └── ReportGeneratorPage.tsx
│   │   └── reports/
│   │       └── ReportListPage.tsx
│   ├── components/
│   │   ├── Dataset/
│   │   ├── Model/
│   │   ├── Prediction/
│   │   ├── Charts/
│   │   └── Common/
│   └── types/
│       ├── auth.ts
│       ├── dataset.ts
│       ├── model.ts
│       └── prediction.ts
10.2 前端路由
/login
/register

/dashboard

/datasets
/datasets/create
/datasets/:id
/datasets/:id/preview
/datasets/:id/profile
/datasets/:id/charts

/models
/models/train
/models/:id
/models/:id/evaluation

/prediction/igan/single
/prediction/batch
/prediction/regression/single
/prediction/history

/ai/dataset-analysis
/ai/model-analysis
/ai/report-generator

/reports
/settings
11. 后端设计
11.1 后端目录结构
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── datasets.py
│   │   ├── models.py
│   │   ├── predictions.py
│   │   ├── evaluation.py
│   │   ├── ai.py
│   │   └── reports.py
│   ├── db_models/
│   │   ├── user.py
│   │   ├── dataset.py
│   │   ├── ml_model.py
│   │   ├── training_run.py
│   │   ├── prediction.py
│   │   └── ai_report.py
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   ├── dataset_schema.py
│   │   ├── model_schema.py
│   │   ├── prediction_schema.py
│   │   ├── evaluation_schema.py
│   │   └── ai_schema.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── dataset_service.py
│   │   ├── training_service.py
│   │   ├── prediction_service.py
│   │   ├── evaluation_service.py
│   │   ├── ai_analysis_service.py
│   │   └── report_service.py
│   ├── ml/
│   │   ├── opns_transformer.py
│   │   ├── pairing_strategy.py
│   │   ├── feature_mapper.py
│   │   ├── trainer.py
│   │   ├── evaluator.py
│   │   └── predictor.py
│   └── utils/
│       ├── security.py
│       ├── file_utils.py
│       ├── dataframe_utils.py
│       └── response.py
├── storage/
│   ├── datasets/
│   ├── models/
│   ├── predictions/
│   └── reports/
├── requirements.txt
├── .env.example
└── run.py
12. 数据库设计
12.1 users
id              Integer primary key
username        String unique
email           String unique
password_hash   String
role            String default "user"
created_at      DateTime
updated_at      DateTime
12.2 datasets
id              Integer primary key
user_id         Integer foreign key
name            String
task_type       String
description     Text
file_path       String
file_type       String
sample_count    Integer
feature_count   Integer
target_columns  JSON
created_at      DateTime
updated_at      DateTime

task_type 可选值：

classification
regression
multi_output_classification
12.3 dataset_columns
id              Integer primary key
dataset_id      Integer foreign key
column_name     String
data_type       String
role            String
missing_count   Integer
unique_count    Integer
mean            Float nullable
std             Float nullable
min_value       Float nullable
max_value       Float nullable

role 可选值：

feature
target
ignored
12.4 models
id                  Integer primary key
user_id             Integer foreign key
dataset_id          Integer foreign key
model_name          String
task_type           String
algorithm           String
target_columns      JSON
feature_columns     JSON
opns_enabled        Boolean
pairing_method      String
mapping_config      JSON
hyperparameters     JSON
model_file_path     String
scaler_file_path    String nullable
metadata_file_path  String nullable
created_at          DateTime
updated_at          DateTime

algorithm 可选值：

SVM
SVR
OPNs-SVM
OPNs-SVR
RandomForestClassifier
RandomForestRegressor
LogisticRegression
RidgeRegression
12.5 training_runs
id              Integer primary key
model_id        Integer foreign key
train_size      Integer
test_size       Integer
random_state    Integer
status          String
started_at      DateTime
finished_at     DateTime nullable
error_message   Text nullable
12.6 model_metrics
id              Integer primary key
model_id        Integer foreign key
target_name     String nullable
metric_name     String
metric_value    Float
created_at      DateTime
12.7 prediction_jobs
id                  Integer primary key
user_id             Integer foreign key
model_id            Integer foreign key
dataset_id          Integer nullable
job_type            String
input_file_path     String nullable
output_file_path    String nullable
status              String
created_at          DateTime
finished_at         DateTime nullable
error_message       Text nullable
12.8 prediction_results
id                  Integer primary key
job_id              Integer foreign key
sample_index        Integer
input_json          JSON
prediction_json     JSON
created_at          DateTime
12.9 ai_analysis_reports
id                  Integer primary key
user_id             Integer foreign key
dataset_id          Integer nullable
model_id            Integer nullable
prediction_job_id   Integer nullable
analysis_type       String
input_summary_json  JSON
generated_text      Text
created_at          DateTime
13. API 设计
13.1 认证接口
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
PUT  /api/auth/password
POST /api/auth/logout
13.2 数据集接口
POST   /api/datasets
GET    /api/datasets
GET    /api/datasets/{dataset_id}
DELETE /api/datasets/{dataset_id}

POST   /api/datasets/{dataset_id}/upload
GET    /api/datasets/{dataset_id}/preview
GET    /api/datasets/{dataset_id}/profile
GET    /api/datasets/{dataset_id}/columns
GET    /api/datasets/{dataset_id}/charts/label-distribution
GET    /api/datasets/{dataset_id}/charts/missing-values
GET    /api/datasets/{dataset_id}/charts/correlation
13.3 模型接口
POST   /api/models/train
GET    /api/models
GET    /api/models/{model_id}
DELETE /api/models/{model_id}
GET    /api/models/{model_id}/metrics
GET    /api/models/{model_id}/metadata
13.4 评估接口
GET /api/evaluation/classification/{model_id}
GET /api/evaluation/regression/{model_id}
GET /api/evaluation/confusion-matrix/{model_id}
GET /api/evaluation/roc/{model_id}
GET /api/evaluation/residuals/{model_id}
GET /api/evaluation/predicted-vs-actual/{model_id}
13.5 预测接口
POST /api/predictions/igan/single
POST /api/predictions/regression/single

POST /api/predictions/batch/upload
POST /api/predictions/batch/run
GET  /api/predictions/batch/{job_id}
GET  /api/predictions/batch/{job_id}/download

GET  /api/predictions/history
GET  /api/predictions/{prediction_id}
13.6 AI 分析接口
POST /api/ai/dataset-analysis/{dataset_id}
GET  /api/ai/dataset-analysis/{dataset_id}

POST /api/ai/model-analysis/{model_id}
GET  /api/ai/model-analysis/{model_id}

POST /api/ai/prediction-explanation/{prediction_job_id}
POST /api/ai/report/{model_id}
14. IgAN MEST-C 分类设计

IgAN 数据中的 M、E、S、T、C 是分类标签，不应强行作为 SVR 回归目标。

系统应将 IgAN 病理标签建模为多输出分类任务。推荐内部实现为五个独立分类器：

M 分类器：M0 / M1
E 分类器：E0 / E1
S 分类器：S0 / S1
T 分类器：T0 / T1 / T2
C 分类器：C0 / C1 / C2

训练模型：

标准 SVM
OPNs-SVM
Random Forest Classifier
Logistic Regression

预测输出示例：

{
  "task": "igan_mestc",
  "result": {
    "M": {"label": "M1", "probability": 0.76},
    "E": {"label": "E0", "probability": 0.82},
    "S": {"label": "S1", "probability": 0.69},
    "T": {"label": "T0", "probability": 0.71},
    "C": {"label": "C1", "probability": 0.64}
  },
  "disclaimer": "该结果仅用于科研分析，不作为临床诊断或治疗依据。"
}

模型文件保存结构：

backend/storage/models/model_001/
├── metadata.json
├── scaler.pkl
├── opns_transformer.pkl
├── M_classifier.pkl
├── E_classifier.pkl
├── S_classifier.pkl
├── T_classifier.pkl
└── C_classifier.pkl
15. OPNs-SVR 回归模块设计

为了保留 OPNs-SVR，系统应提供连续目标预测模块。

可支持以下任务：

CKD 或其他医学表格数据中的 GFR/eGFR 预测
IgAN 数据中连续实验室指标预测
Energy Efficiency 数据中的 heating load / cooling load 预测
Concrete 数据中的 compressive strength 预测

回归模型：

标准 SVR
OPNs-SVR
Random Forest Regressor
Ridge Regression

回归指标：

MAE
RMSE
R2
MAPE

回归图表：

真实值-预测值散点图
残差分布图
残差折线图
模型指标对比图
16. OPNs 特征构造模块
16.1 配对方式

至少支持：

adjacent
random
correlation_greedy

含义：

adjacent：按原始特征顺序两两配对。
random：随机打乱特征后两两配对。
correlation_greedy：根据特征与目标的相关性和特征间冗余进行贪心配对。
16.2 特征映射

对每一对特征 (x_p, x_q)，构造结构特征：

x_p + x_q
x_p - x_q
abs(x_p - x_q)
x_p * x_q
x_p^2 + x_q^2
16.3 类设计

backend/app/ml/opns_transformer.py

class OPNsTransformer:
    def __init__(
        self,
        pairing_method: str = "adjacent",
        mapping_config: dict | None = None,
        random_state: int | None = None,
    ):
        pass

    def fit(self, X, y=None):
        pass

    def transform(self, X):
        pass

    def fit_transform(self, X, y=None):
        pass

backend/app/ml/pairing_strategy.py

def adjacent_pairing(feature_names: list[str]) -> list[tuple[str, str]]:
    pass

def random_pairing(feature_names: list[str], random_state: int | None = None) -> list[tuple[str, str]]:
    pass

def correlation_greedy_pairing(X, y, feature_names: list[str]) -> list[tuple[str, str]]:
    pass
17. 数据可视化模块

前端使用 ECharts 展示数据分析和模型评估图表。

17.1 数据集图表

必须实现：

缺失值柱状图
标签分布柱状图
数值特征分布直方图
相关性热力图
17.2 分类评估图表

必须实现：

M/E/S/T/C 指标对比柱状图
混淆矩阵热力图
ROC 曲线，可选
17.3 回归评估图表

必须实现：

真实值-预测值散点图
残差分布图
回归指标对比柱状图
18. AI 辅助分析模块

AI 模块不直接输出医学诊断结论，不直接输出治疗建议。

系统中的 AI 模块只用于：

数据质量分析
标签分布说明
类别不平衡提示
模型评估结果解释
预测结果自然语言说明
实验报告初稿生成
18.1 AI 数据集分析

输入摘要示例：

{
  "sample_count": 312,
  "feature_count": 18,
  "target_columns": ["M", "E", "S", "T", "C"],
  "missing_values": {
    "albumin": 26,
    "uric_acid": 18
  },
  "label_distribution": {
    "M": {"M0": 180, "M1": 132},
    "E": {"E0": 260, "E1": 52}
  }
}

输出文本应包括：

数据规模说明
缺失值说明
标签分布说明
类别不平衡提示
建模注意事项
科研用途声明
18.2 AI 模型结果分析

输入摘要示例：

{
  "task": "IgAN MEST-C classification",
  "algorithm": "OPNs-SVM",
  "baseline": "standard SVM",
  "metrics": {
    "M": {"accuracy": 0.82, "precision": 0.80, "recall": 0.78, "f1": 0.79},
    "E": {"accuracy": 0.76, "precision": 0.73, "recall": 0.65, "f1": 0.69}
  }
}

输出文本应包括：

整体模型表现
不同标签表现差异
与基线模型对比
可能原因分析
模型局限性
科研用途声明
18.3 AI 单病例预测说明

AI 输出必须包含：

模型预测结果说明
置信度说明
不确定性说明
科研用途声明

AI 输出禁止包含：

诊断结论
治疗建议
用药建议
临床处置建议
18.4 AI 模式

建议 AI 服务支持两种模式：

mock 模式：不调用外部大模型，使用模板生成分析文本。
llm 模式：调用外部大模型 API 生成文本。

环境变量：

AI_MODE=mock
OPENAI_API_KEY=

MVP 阶段优先实现 mock 模式。这样即使没有外部 API Key，系统仍然可以运行和展示。

19. 安全与合规要求
19.1 账号安全
密码必须哈希存储。
接口必须进行 JWT 鉴权。
用户只能访问自己的数据集、模型和预测记录。
19.2 文件安全
限制上传文件类型为 csv、xlsx。
限制上传文件大小。
文件名应重命名，避免直接使用用户上传文件名。
不要执行上传文件中的任何内容。
19.3 医学边界

系统所有预测页面、AI 分析页面和报告导出内容中必须加入：

本系统预测结果仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。实际医学判断应由具有资质的临床医生结合完整病史、检查结果和病理资料完成。
20. WSL2 环境初始化建议
20.1 检查基础环境
node -v
npm -v
python3 --version
pip --version
git --version

如需创建 Python 虚拟环境：

cd ~/OPNs_Project/backend
python3 -m venv .venv
source .venv/bin/activate

安装后端依赖：

pip install -r requirements.txt

前端安装依赖：

cd ~/OPNs_Project/frontend
npm install
21. 本地运行方式
21.1 启动后端
cd ~/OPNs_Project/backend

source .venv/bin/activate

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

后端地址：

http://localhost:8000

API 文档地址：

http://localhost:8000/docs
21.2 启动前端
cd ~/OPNs_Project/frontend

npm install
npm run dev

前端地址通常为：

http://localhost:5173
22. MVP 开发任务
22.1 阶段一：基础系统

任务：

1. 初始化 React + TypeScript + Vite 前端项目。
2. 初始化 FastAPI 后端项目。
3. 配置 SQLite 数据库。
4. 实现 SQLAlchemy 基础连接。
5. 实现用户注册接口。
6. 实现用户登录接口。
7. 实现 JWT 鉴权。
8. 实现前端登录页。
9. 实现前端注册页。
10. 实现登录后主布局。

验收标准：

用户可以注册、登录，并进入系统首页。
未登录用户不能访问系统内部页面。

Git 提交建议：

git add .
git commit -m "feat: implement authentication module"
22.2 阶段二：数据集管理

任务：

1. 实现数据集创建接口。
2. 实现 CSV/XLSX 上传接口。
3. 保存上传文件到 backend/storage/datasets。
4. 使用 pandas 读取文件并生成数据摘要。
5. 实现数据预览接口。
6. 实现字段统计接口。
7. 实现缺失值统计接口。
8. 实现前端数据集列表页。
9. 实现前端数据预览表格。
10. 实现标签分布和缺失值图表。

验收标准：

用户可以上传 IgAN 数据。
系统可以展示前 50 行数据。
系统可以展示字段列表、缺失值统计和标签分布图。

Git 提交建议：

git add .
git commit -m "feat: implement dataset upload and preview"
22.3 阶段三：OPNs-SVM 分类训练

任务：

1. 实现 OPNsTransformer。
2. 实现 adjacent pairing。
3. 实现 random pairing。
4. 实现结构特征映射。
5. 实现标准 SVM 训练。
6. 实现 OPNs-SVM 训练。
7. 实现 IgAN M/E/S/T/C 五标签分类训练。
8. 保存模型文件。
9. 保存模型指标。
10. 实现模型详情页和评估页。

验收标准：

系统可以训练 IgAN MEST-C 分类模型。
系统可以保存模型。
系统可以展示每个标签的 Accuracy、Precision、Recall 和 F1。

Git 提交建议：

git add .
git commit -m "feat: implement OPNs-SVM training module"
22.4 阶段四：预测功能

任务：

1. 实现单病例预测接口。
2. 实现前端动态输入表单。
3. 实现 M/E/S/T/C 预测结果展示。
4. 实现批量预测文件上传。
5. 实现批量预测接口。
6. 实现批量预测结果表格。
7. 实现预测结果导出 CSV。

验收标准：

用户可以选择模型并输入单个病例。
系统可以输出 M/E/S/T/C 预测结果。
用户可以上传批量病例文件并导出预测结果。

Git 提交建议：

git add .
git commit -m "feat: implement single and batch prediction"
22.5 阶段五：AI 辅助分析

任务：

1. 实现 AIAnalysisService。
2. 实现 mock 模式数据集分析。
3. 实现 mock 模式模型结果分析。
4. 实现 mock 模式预测说明。
5. 在数据集详情页加入“生成 AI 数据分析”按钮。
6. 在模型评估页加入“生成 AI 结果分析”按钮。
7. 在预测结果页加入“生成 AI 预测说明”按钮。
8. 保存 AI 生成文本到数据库。

验收标准：

系统可以基于结构化统计结果生成自然语言分析。
AI 输出中必须包含科研用途声明。
AI 输出中不得包含诊断或治疗建议。

Git 提交建议：

git add .
git commit -m "feat: implement AI analysis mock service"
22.6 阶段六：OPNs-SVR 回归模块

任务：

1. 实现回归任务训练流程。
2. 实现标准 SVR。
3. 实现 OPNs-SVR。
4. 实现回归指标 MAE、RMSE、R2。
5. 实现真实值-预测值散点图。
6. 实现残差图。
7. 实现回归单样本预测。
8. 实现回归批量预测。

验收标准：

系统可以上传回归数据集。
系统可以训练 OPNs-SVR。
系统可以展示 MAE、RMSE 和 R2。
系统可以进行连续值预测。

Git 提交建议：

git add .
git commit -m "feat: implement OPNs-SVR regression module"
23. 推荐 Codex 执行顺序
23.1 第一次 Codex Prompt：初始化项目
请基于当前目录结构初始化前后端分离项目。

当前根目录为 OPNs_Project，已包含 frontend、backend 和 README.md。

要求：
1. 不要重新创建 OPNs_Project 根目录。
2. 在 frontend 中初始化 React + TypeScript + Vite + Ant Design 项目结构。
3. 在 backend 中初始化 FastAPI + SQLAlchemy + SQLite 项目结构。
4. 后端先实现 app/main.py、config.py、database.py。
5. 创建 backend/storage/datasets、models、predictions、reports，并加入 .gitkeep。
6. 创建 .gitignore。
7. 不要实现业务功能。
8. 不要硬编码密钥。
9. 修改完成后说明运行方式。

完成后检查：

git status
git diff

提交：

git add .
git commit -m "chore: initialize frontend and backend projects"
23.2 第二次 Codex Prompt：认证模块
请在现有项目基础上实现登录注册模块。

要求：
1. 后端实现 users 表。
2. 后端实现注册、登录、/api/auth/me。
3. 密码必须哈希存储。
4. 使用 JWT 进行鉴权。
5. 前端实现登录页、注册页、Dashboard 页面。
6. 前端实现路由守卫。
7. 前端通过 api/request.ts 统一封装 Axios。
8. 不要实现其他业务模块。

提交：

git add .
git commit -m "feat: implement authentication module"
23.3 第三次 Codex Prompt：数据集管理
请在现有项目基础上实现数据集管理模块。

要求：
1. 后端实现数据集创建、列表、详情、删除接口。
2. 后端实现 CSV/XLSX 文件上传接口。
3. 文件保存到 backend/storage/datasets。
4. 使用 pandas 读取上传文件，统计样本数、字段数、缺失值、字段类型。
5. 实现数据预览接口，默认返回前 50 行。
6. 前端实现数据集列表页、创建数据集页、上传文件组件和数据预览表格。
7. 使用 Ant Design Table 展示预览数据。
8. 保证用户只能访问自己的数据集。

提交：

git add .
git commit -m "feat: implement dataset management module"
23.4 第四次 Codex Prompt：数据可视化
请在现有项目基础上实现数据可视化模块。

要求：
1. 后端提供标签分布、缺失值统计、数值字段统计和相关性矩阵接口。
2. 前端使用 ECharts 实现缺失值柱状图、标签分布柱状图和相关性热力图。
3. IgAN 数据集中如果存在 M、E、S、T、C 字段，应分别展示标签分布。
4. 图表组件放在 frontend/src/components/Charts。
5. 页面放在 frontend/src/pages/datasets/DatasetProfilePage.tsx。

提交：

git add .
git commit -m "feat: implement dataset visualization module"
23.5 第五次 Codex Prompt：OPNs-SVM
请在现有项目基础上实现 OPNs-SVM 模型训练模块。

要求：
1. 在 backend/app/ml 中实现 OPNsTransformer。
2. 支持 adjacent 和 random 两种配对方式。
3. 支持 sum、diff、abs_diff、product、square_sum 五种结构特征映射。
4. 实现标准 SVM 和 OPNs-SVM 训练。
5. 对 IgAN 的 M、E、S、T、C 进行五个分类器训练。
6. 保存 scaler、opns_transformer 和每个分类器。
7. 保存模型 metadata.json。
8. 保存 Accuracy、Precision、Recall、F1 指标到数据库。
9. 前端实现模型训练页面和模型评估页面。
10. 不要实现 OPNs-SVR，回归模块后续单独实现。

提交：

git add .
git commit -m "feat: implement OPNs-SVM training"
23.6 第六次 Codex Prompt：预测模块
请在现有项目基础上实现 IgAN 单病例预测和批量预测模块。

要求：
1. 单病例预测页面根据模型 metadata 中的 feature_columns 动态生成表单。
2. 后端加载模型、scaler、opns_transformer 和 M/E/S/T/C 分类器进行预测。
3. 返回每个标签的预测类别和预测概率。
4. 批量预测支持上传 CSV/XLSX。
5. 批量预测结果以表格展示，并支持导出 CSV。
6. 所有预测结果必须包含“仅用于科研分析，不作为临床诊断或治疗依据”的声明。

提交：

git add .
git commit -m "feat: implement IgAN prediction module"
23.7 第七次 Codex Prompt：AI 辅助分析
请在现有项目基础上实现 AI 辅助分析模块。

要求：
1. 实现 AIAnalysisService。
2. 支持 mock 模式，不依赖外部 API。
3. 数据集分析根据样本数、字段数、缺失值、标签分布生成自然语言说明。
4. 模型结果分析根据 Accuracy、Precision、Recall、F1、MAE、RMSE、R2 等指标生成说明。
5. 预测结果说明根据 M/E/S/T/C 预测类别和概率生成说明。
6. AI 输出不得包含临床诊断、治疗建议或用药建议。
7. AI 输出必须包含科研用途声明。
8. 前端在数据集详情页、模型评估页和预测结果页加入 AI 分析按钮。

提交：

git add .
git commit -m "feat: implement AI analysis module"
23.8 第八次 Codex Prompt：OPNs-SVR
请在现有项目基础上实现 OPNs-SVR 回归模块。

要求：
1. 支持上传回归数据集。
2. 支持选择连续目标变量。
3. 实现标准 SVR 和 OPNs-SVR。
4. 计算 MAE、RMSE、R2。
5. 实现真实值-预测值散点图和残差图。
6. 支持单样本回归预测和批量回归预测。
7. 保持代码结构与 OPNs-SVM 分类模块一致。

提交：

git add .
git commit -m "feat: implement OPNs-SVR regression module"
24. 每次开发后的检查清单

每次让 Codex 修改代码后，必须检查：

git status
git diff --stat

如果后端有修改：

cd backend
source .venv/bin/activate
python -m compileall app

如果前端有修改：

cd frontend
npm run build

如果有测试脚本：

pytest
npm test

检查通过后再提交：

cd ~/OPNs_Project
git add .
git commit -m "type: message"
25. 项目验收标准

最终系统至少应满足：

1. 用户可以注册和登录。
2. 用户可以上传 IgAN 数据集。
3. 系统可以预览表格数据。
4. 系统可以展示缺失值和 M/E/S/T/C 标签分布。
5. 系统可以训练标准 SVM 和 OPNs-SVM。
6. 系统可以对 M/E/S/T/C 进行分类预测。
7. 系统可以进行单病例预测。
8. 系统可以进行批量预测。
9. 系统可以展示分类评估指标。
10. 系统可以生成 AI 数据分析文本。
11. 系统可以生成 AI 模型结果分析文本。
12. 系统可以保留 OPNs-SVR 回归模块。
13. 系统所有医学相关输出均包含科研用途声明。
14. 系统代码通过 Git 进行版本控制。
15. 每个主要开发阶段均有独立 Git 提交记录。
26. 与毕业论文和专业实践的对应关系
毕业论文中的 OPNs 特征构造方法
    ↓
系统中的 OPNsTransformer 模块

毕业论文中的 OPNs-SVM 分类算法
    ↓
系统中的 IgAN MEST-C 病理标签预测模块

毕业论文中的 OPNs-SVR 回归算法
    ↓
系统中的连续医学指标或公开回归数据预测模块

毕业论文中的实验结果分析
    ↓
系统中的模型评估与 AI 辅助结果分析模块

专业实践的软件系统要求
    ↓
React + FastAPI + 数据库 + 文件管理 + 可视化 + 模型服务 + Git 版本控制
27. 医学声明

系统所有预测页面、AI 分析页面和报告导出内容中必须加入以下声明：

本系统预测结果仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。实际医学判断应由具有资质的临床医生结合完整病史、检查结果和病理资料完成。
28. 开发注意事项
1. 不要将真实患者隐私数据提交到 Git。
2. 不要将 .env 文件提交到 Git。
3. 不要将数据库文件提交到 Git。
4. 不要将上传的数据集文件提交到 Git。
5. 不要将训练得到的大模型文件或 pkl 文件提交到 Git。
6. README.md 和 docs/ 下的设计文档应持续更新。
7. 每次完成功能模块后更新 docs/development_log.md。
8. Codex 生成代码后必须人工检查，不要直接提交未检查代码。
9. 医学相关文本必须保持科研辅助边界。
10. 系统核心是 OPNs-SVM/SVR，不要让 AI 模块喧宾夺主。