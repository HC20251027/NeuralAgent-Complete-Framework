# 全功能本地化AI智能体大整合方案：NeuralAgent × Agno-BMAD-LM Studio融合架构

## 一、方案总体目标与核心优势

### 1.1 总体目标
构建一个完全本地化、离线运行的全功能AI智能体，具备：
- 多模态视觉理解：纯视觉解析、OCR增强、多模态融合三种技术路线并行
- 语音交互能力：语音识别、语音合成、声音分析一体化解决方案
- 人类级操作能力：模拟人类鼠标键盘操作 + 代码级自动化操作
- 自主任务执行：从视觉理解到操作执行的完整闭环
- 模块化可扩展：支持功能模块的灵活组合与扩展

### 1.2 核心优势
- **完全离线**：所有组件本地部署，无网络依赖，数据隐私安全
- **多技术融合**：集成当前最先进的三种视觉技术路线和完整的语音交互能力
- **操作多样性**：支持模拟操作和代码操作双重模式
- **资源优化**：在普通硬件（无独立GPU）上可运行
- **易用性**：提供可视化界面和零代码配置选项
- **协作高效**：集成Agno多智能体框架，实现任务智能分解与并行执行
- **开发流程**：内置BMAD-METHOD开发方法论，确保从需求到交付的规范化流程
- **语音交互**：全本地化语音识别、合成与分析能力，支持多语言

## 二、技术架构深度整合

### 2.1 总体架构设计
```
┌────────────────────────────────────────────────┐       ┌─────────────────────┐
│                   应用层：全功能AI智能体        │──────▶│                     │
│  - 用户界面与交互控制                           │       │                     │
│  - 敏捷开发流程管理 (BMAD集成)                  │       │                     │
│  - 任务管理与监控系统                           │       │                     │
├────────────────────────────────────────────────┤       │                     │
│ 协调层：Agno多智能体框架                        │──────▶│                     │
│  - 任务分解引擎                                 │       │                     │
│  - 角色分配系统                                 │       │                     │
│  - 进度监控与协调                               │       │                     │
│  - 结果整合与质量控制                           │       │                     │
├────────────────────────────────────────────────┤       │                     │
│ 视觉层：多模态视觉分析系统                      │──────▶│   APISIX网关        │
│  - 纯视觉解析：NeuralAgent YOLOv8-nano          │       │ （独立通信层）      │
│  - OCR增强路线：ScreenPipe + 增强模块           │       │                     │
│  - 多模态融合：LM Studio + 先进VLM              │       │                     │
├────────────────────────────────────────────────┤       │ （独立通信层）      │
│ 语音层：全功能语音交互系统                      │──────▶│                     │
│  - 语音识别模块：Whisper/Sherpa-onnx            │       │                     │
│  - 语音合成模块：VITS多语言引擎                 │       │                     │
│  - 声音分析模块：声纹识别与情感分析             │       │                     │
├────────────────────────────────────────────────┤       │                     │
│ 操作层：双重操作执行系统                        │──────▶│                     │
│  - 模拟人类操作：NeuralAgent操作引擎            │       │                     │
│  - 代码级操作：BMAD开发自动化                   │       │                     │
└────────────────────────────────────────────────┘       └─────────┬───────────┘
                                                                   │
                                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                                  服务层：本地化基础设施                          │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐     │
│  │  APISIX网关                     │  │  PostgreSQL + PgVector         │     │
│  │  - 路由转发                     │  │ （向量数据库）                  │     │
│  │  - 负载均衡                     │◀─│                                 │     │
│  │  - 安全认证                     │  │                                 │     │
│  │  - BMAD-Agno通信路由            │  └─────────────────────────────────┘     │
│  │  - 代理注册接口                 │                                            │
│  │  - 任务调用接口                 │  ┌─────────────────────────────────────────┐ │
│  │  - LM Studio模型请求转发        │  │           LM Studio本地模型服务          │ │
│  └─────────────────────────────────┘  │       （OpenAI兼容接口）               │ │
│                                       └─────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        本地工具链（FFmpeg、ChromeDriver等）            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

**架构说明：**
- **APISIX网关作为独立通信层**：垂直排列在架构右侧，负责所有业务层之间的通信转发
- **通信流向**：上层组件（应用层、协调层、视觉层、语音层、操作层）通过APISIX网关访问下层组件
- **特殊路径**：LM Studio与上层组件之间采用直接通信方式，不通过APISIX网关，以优化性能
- **网关职责**：负责路由转发、负载均衡、安全认证、限流控制等核心功能
- **服务层集成**：所有服务层组件（除LM Studio外）均通过APISIX网关提供服务
- **BMAD-Agno集成**：通过角色映射机制将BMAD的analyst-agent和architect-agent映射至domain-expert，pm-agent映射至planner，dev-agent映射至executor，qa-agent映射至validator
- **记忆共享机制**：Agno的三级记忆系统与BMAD的知识库实现双向同步，确保开发流程中的知识连续性

### 2.2 核心组件选型与整合

#### 2.2.1 视觉分析层 - 三路线并行架构

**路线一：纯视觉解析（NeuralAgent + 微软OmniParser）**
```python
# NeuralAgent视觉核心
visual_agent = NeuralAgent(
    screen_capture_module="mss",  # 跨平台截图
    ui_detection_model="YOLOv8-nano-ui",  # 专为UI微调的轻量模型
    element_recognition=["button", "input", "dropdown", "icon"],
    color_based_detection=True,  # HSV颜色空间识别
    contour_detection=True  # 轮廓检测辅助
)

# OmniParser增强
omniparser_integration = OmniParserIntegration(
    target_detection="yolov8-optimized",
    visual_language_model="gpt-4v-local",  # 本地化版本
    ocr_engine="tesseract-enhanced",
    element_merging=True  # 图标边界框去重融合
)
```

**路线二：OCR增强路线（ScreenPipe + 增强模块）**
```python
ocr_agent = ScreenPipeEnhanced(
    screen_stream_capture=True,  # 实时屏幕流感知
    ocr_engine="tesseract-5.0",  # 优化版本
    text_region_highlight=True,  # 文字区域高亮
    semantic_enhancement=True,  # 语义增强
    complex_layout_handling=True  # 复杂布局处理
)
```

**路线三：多模态融合（LM Studio + 先进VLM）**
```python
multimodal_agent = VLMAgent(
    base_model="qwen-vl-7b-gguf",  # 或ovis2-34b
    visual_understanding=True,
    video_processing=True,  # 视频理解能力
    structured_data_output=True,  # 结构化输出
    long_context_handling=True  # 长视频/多图像处理
)
```

#### 2.2.2 操作执行层 - 双重操作模式

**模式一：模拟人类操作（基于NeuralAgent操作引擎）**
```python
human_like_operator = HumanLikeOperator(
    mouse_control="pyautogui-enhanced",  # 增强版，误差≤1像素
    keyboard_control="pynput-advanced",
    operation_anti_shake=True,  # 操作防抖机制
    delay_strategy="adaptive",  # 自适应等待
    failover_mechanism=True  # 故障转移
)
```

**模式二：代码级操作（基于BMAD开发自动化）**
```python
code_operator = CodeLevelOperator(
    browser_automation="selenium-4.15",
    ide_integration=["vscode", "pycharm"],
    command_line="subprocess-enhanced",
    git_operations=True,
    file_system_operations=True
)
```

#### 2.2.3 语音交互层 - 全功能语音系统

**语音识别模块（ASR）**
```python
# Whisper本地语音识别
asr_engine = WhisperLocalEngine(
    model_path="D:/models/whisper-small.onnx",  # 轻量级模型
    language="zh",  # 支持中文
    vad_enabled=True,  # 语音活动检测
    real_time=True,  # 实时处理
    beam_size=5,  # 解码参数
    sample_rate=16000  # 采样率
)

# Sherpa-onnx 优化版本（更低延迟）
sherpa_asr = SherpaOnnxEngine(
    model_dir="D:/models/sherpa-onnx-streaming-zipformer-small",
    tokens_path="D:/models/tokens.txt",
    num_threads=4,  # CPU线程数
    decoding_method="greedy",  # 贪婪解码（更快）
    max_active_paths=4  # 搜索路径数
)
```

**语音合成模块（TTS）**
```python
# VITS本地语音合成
vits_tts = VitsTTS(
    model_path="D:/models/vits-zh-hf.pth",
    config_path="D:/models/vits-zh-hf.json",
    speaker_id=0,  # 说话人ID
    device="cpu",  # 可在CPU上运行
    sample_rate=22050,
    audio_format="wav"
)

# 多语言TTS配置
multilingual_tts = MultiLangTTS(
    engines={
        "zh": vits_tts,  # 中文引擎
        "en": EnVitsTTS("D:/models/vits-en.pth"),  # 英文引擎
        # 可添加更多语言引擎
    },
    language_detection=True,  # 自动语言检测
    emotion_support=True  # 情感合成支持
)
```

**声音分析模块**
```python
# 声纹识别系统
voiceprint_engine = VoiceprintRecognizer(
    model_path="D:/models/ecapa-tdnn.onnx",
    threshold=0.75,  # 相似度阈值
    embedding_dim=192,  # 特征维度
    speaker_database="D:/data/speakers.db"  # 说话人数据库
)

# 情感分析系统
emotion_analyzer = SpeechEmotionAnalyzer(
    model_path="D:/models/speech-emotion.onnx",
    emotions=["happy", "sad", "angry", "neutral", "excited"],
    frame_length=2.0,  # 分析帧长
    frame_shift=0.5  # 帧移
)
```

#### 2.2.4 智能协调层（Agno高级协作模式）

**Agno三大协作模式**：

**BMAD代理映射关系**：
- domain-expert → analyst-agent、architect-agent
- planner → pm-agent
- executor → dev-agent
- validator → qa-agent

1. **经理-员工模式**
   - 通过manager_agent作为"经理"，负责任务分解、角色分配、进度协调和结果整合
   - 支持动态任务分解（2-4个任务）和智能角色匹配
   - 适用于创意内容生成、项目规划等场景

2. **条件路由模式**
   - 根据前置条件动态路由任务到不同Agent处理
   - 支持可行性评估、复杂度评估、资源评估等多种条件类型
   - 适用于需求分析、PRD评审等场景

3. **并行执行模式**
   - 支持多个Agent并发执行独立任务
   - 内置进度监控和结果整合机制
   - 适用于竞品分析、多源数据采集等场景

```python
# 经理-员工模式增强版
manager_agent = EnhancedManagerAgent(
    task_decomposition="dynamic",
    role_matching="intelligent",
    progress_coordination="real-time",
    result_integration="structured"
)

# 条件路由系统
conditional_router = AdvancedConditionRouter(
    condition_types=["feasibility", "complexity", "resource"],
    routing_strategy="multi-level",
    fallback_mechanism=True
)

# 并行执行优化
parallel_executor = OptimizedParallelExecutor(
    max_concurrent=5,  # 硬件感知的并发控制
    resource_monitoring=True,
    priority_queuing=True
)
```

#### 2.2.4 开发方法论层（BMAD-METHOD）

**BMAD核心角色**：
- **分析师**：需求分析、竞品调研、用户画像
- **PM**：产品规划、原型设计、进度管理
- **架构师**：技术选型、架构设计、性能优化
- **开发**：代码实现、单元测试、文档编写
- **QA**：测试用例、自动化测试、质量保障

**工作流程**：
1. 从视频/UI到PRD自动生成
2. PRD可行性评估
3. 技术架构设计
4. 开发实现
5. 质量测试
6. 部署交付

## 三、部署方案详细实现

### 3.1 硬件与软件要求

#### 3.1.1 硬件要求
- **最低配置**：
  - CPU：Intel i5-12400H或同等性能
  - 内存：16GB RAM
  - 存储：100GB可用空间
  - 网络：纯离线环境
- **推荐配置**：
  - CPU：Intel i7-13700H或更高
  - 内存：32GB RAM
  - 存储：NVMe SSD，500GB可用空间
  - 可选：NVIDIA RTX 4060（加速视觉处理）

#### 3.1.2 软件依赖

| 组件 | 版本要求 | 安装路径 |
|------|---------|----------|
| Python | 3.10+ | D:\Python310 |
| Node.js | v20+ | D:\Node.js |
| LM Studio | v0.20+ | D:\LM Studio |
| PostgreSQL | 15+ | D:\PostgreSQL15 |
| APISIX | v3.7+ | D:\BMAD-Agno-Integration\apisix |
| Agno | v1.5+ | D:\BMAD-Agno-Integration\agno |
| BMAD-METHOD | v4.x | D:\BMAD-Agno-Integration\bmad |
| Whisper | small-medium | D:\models\whisper |
| VITS/Sherpa | - | D:\models\tts |
| 工具链 | - | D:\BMAD-Agno-Integration\tools |

### 3.2 分步部署流程

#### 第一阶段：基础环境部署

```batch
# 1. 创建项目目录结构
mkdir -p D:\BMAD-Agno-Integration\{agno,bmad,apisix,tools}

# 2. 安装Python 3.10+（离线包）
python-3.10.12-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 TargetDir=D:\Python310

# 3. 安装Node.js v20+（离线包）
node-v20.11.0-x64.msi /quiet ADDLOCAL=NodeRuntime,npm PREPEND_PATH=1 TARGETDIR=D:\Nodejs

# 4. 部署PostgreSQL 15 + PgVector
postgresql-15.4-1-windows-x64.exe --unattendedmodeui minimal --superpassword "pg123456" --servicename postgresql-x64-15

# 5. 安装PgVector扩展
copy vector.dll D:\PostgreSQL15\lib
# 然后通过pgAdmin执行: CREATE EXTENSION vector;

# 6. 创建Agno数据库
# 通过pgAdmin执行: CREATE DATABASE agno_memory;
```

#### 第二阶段：核心服务部署

##### 3.2.1 LM Studio本地模型服务

```batch
# 1. 安装LM Studio（离线）
LM-Studio-Setup-0.20.0.exe /S /D=D:\LM-Studio

# 2. 导入多模态模型（提前下载）
# - Qwen-VL-7B-GGUF（视觉语言模型）
# - Llama-3-8B-Instruct（通用语言模型）
# - Ovis2-34B（多模态增强）

# 3. 配置LM Studio服务
# 端口：1234
# API兼容性：OpenAI v1
# 默认模型：qwen-vl-7b-gguf
```

##### 3.2.2 APISIX网关配置

**配置文件路径**：`D:\BMAD-Agno-Integration\apisix\conf\config.yaml`

```yaml
apisix:
  node_listen: 8080  # 对外服务端口
  enable_admin: false
  
  # 独立通信层模式配置
  stream_proxy:
    tcp:
      - addr: 8080

upstreams:
  # 上游1: Agno服务
  - id: 1
    nodes:
      "127.0.0.1:8000": 1
    type: roundrobin
  # 上游2: BMAD服务
  - id: 2
    nodes:
      "127.0.0.1:3000": 1
    type: roundrobin
  # 上游3: PostgreSQL服务
  - id: 3
    nodes:
      "127.0.0.1:5432": 1
    type: roundrobin
    retries: 2

routes:
  # 路由1: Agno服务
  - uri: /api/agno/*
    upstream_id: 1
    plugins:
      proxy-rewrite:
        regex_uri: ["/api/agno/(.*)", "/$1"]
  
  # 路由2-6: BMAD各角色服务
  - uri: /api/bmad/analyst
    upstream_id: 2
    methods: [POST]
    plugins:
      proxy-rewrite:
        headers:
          X-Proxy-By: "APISIX-Gateway"
  - uri: /api/bmad/pm
    upstream_id: 2
    methods: [POST]
    plugins:
      proxy-rewrite:
        headers:
          X-Proxy-By: "APISIX-Gateway"
  - uri: /api/bmad/architect
    upstream_id: 2
    methods: [POST]
    plugins:
      proxy-rewrite:
        headers:
          X-Proxy-By: "APISIX-Gateway"
  - uri: /api/bmad/dev
    upstream_id: 2
    methods: [POST]
    plugins:
      proxy-rewrite:
        headers:
          X-Proxy-By: "APISIX-Gateway"
  - uri: /api/bmad/qa
    upstream_id: 2
    methods: [POST]
    plugins:
      proxy-rewrite:
        headers:
          X-Proxy-By: "APISIX-Gateway"

plugins:
  - name: limit-req
    enable: true
    config:
      rate: 100
      burst: 20
      key: remote_addr
  - name: retry
    enable: true
    config:
      retry_times: 3
      retry_timeout: 30000
  - name: cors
    enable: true
    config:
      allow_origins: "*"
      allow_methods: "GET,POST,PUT,DELETE,OPTIONS"
      allow_headers: "*"
  - name: prometheus
    enable: true
    config:
      prefer_name: true

# 注意：根据新架构设计，LM Studio服务不通过APISIX网关通信，采用直接通信方式优化性能
```

##### 3.2.3 Agno服务配置

**配置文件路径**：`D:\BMAD-Agno-Integration\agno\config\config.yaml`

```yaml
memory:
  vector_db:
    type: postgresql
    # 通过APISIX网关访问PostgreSQL
    host: 127.0.0.1
    port: 8080
    db_name: agno_memory
    user: postgres
    password: pg123456
    # 启用通过API网关连接的特殊配置
    gateway_mode: true

llm:
  provider: "openai"  # 使用openai兼容接口
  # 直接连接到LM Studio，不通过APISIX网关
  api_base: "http://127.0.0.1:1234/v1"  # LM Studio服务直接地址
  api_key: "lm-studio-local"  # 本地API Key
  default_model: "lmstudio-community/Llama-3-8B-Instruct-GGUF"
  parameters:
    max_tokens: 2048
    temperature: 0.2
    top_p: 0.9
    # 直接连接模式下的优化配置
    timeout: 120
    retry_count: 2
```

##### 3.2.4 BMAD服务配置

**配置文件路径**：`D:\BMAD-Agno-Integration\bmad\config\mode_config.mjs`

```javascript
export const llmConfig = {
  provider: "openai",
  // 直接连接到LM Studio，不通过APISIX网关
  apiBase: "http://127.0.0.1:1234/v1",
  apiKey: "lm-studio-local",
  modelName: "lmstudio-community/Llama-3-8B-Instruct-GGUF",
  parameters: {
    maxTokens: 2048,
    temperature: 0.2,
    timeout: 120000, // 增加超时时间
  },
  directConnection: true,
};

export const networkConfig = {
  enableAutoUpdate: false,
  enableRemoteLogging: false,
  gatewayMode: "passive", // 作为APISIX网关的后端服务
  gatewayUrl: "http://127.0.0.1:8080",
};

// 通过APISIX网关访问其他服务的配置
export const serviceConfig = {
  // PostgreSQL配置 - 通过APISIX网关
  database: {
    host: "127.0.0.1",
    port: 8080, // APISIX网关端口
    name: "bmad_db",
    user: "postgres",
    password: "pg123456",
    gatewayProxy: true,
  },
  // Agno服务配置 - 通过APISIX网关
  agno: {
    endpoint: "http://127.0.0.1:8080/api/agno",
    timeout: 30000,
    throughGateway: true,
  },
  // 各角色Agent的网关路径配置
  agentRoutes: {
    analyst: "/api/bmad/analyst",
    pm: "/api/bmad/pm",
    architect: "/api/bmad/architect",
    dev: "/api/bmad/dev",
    qa: "/api/bmad/qa",
  },
};
```

#### 第三阶段：视觉与语音系统部署

##### 3.3.1 语音系统部署

```batch
# 安装语音处理依赖（离线包）
pip install --no-index --find-links=./pip-packages SpeechRecognition pyaudio onnxruntime
pip install --no-index --find-links=./pip-packages whisper-onnx sherpa-onnx TTS

# 创建语音模型目录
mkdir -p D:/models/{whisper,tts,voiceprint}

# 下载模型（提前准备离线文件）
# - Whisper-small模型: whisper-small.onnx
# - VITS语音合成模型: vits-zh-hf.pth
# - ECAPA-TDNN声纹模型: ecapa-tdnn.onnx
```

##### 3.3.2 NeuralAgent视觉模块

```python
# 安装依赖（离线包）
pip install --no-index --find-links=./pip-packages neuralagent-enhanced

# 配置视觉模型
visual_config = {
    "yolov8_nano_ui": {
        "model_path": "D:/models/yolov8n-ui.onnx",
        "confidence_threshold": 0.7,
        "detection_categories": ["button", "input", "text", "icon", "image"]
    },
    "color_detection": {
        "hsv_ranges": {
            "red_button": [[0, 100, 100], [10, 255, 255]],
            "green_submit": [[35, 100, 100], [85, 255, 255]]
        }
    }
}
```

##### 3.3.3 ScreenPipe OCR模块

```python
# OCR增强配置
ocr_config = {
    "tesseract_path": "D:/BMAD-Agno-Integration/tools/tesseract",
    "language_packs": ["eng", "chi_sim", "chi_tra"],
    "preprocessing": {
        "grayscale": True,
        "denoise": True,
        "contrast_enhancement": True
    },
    "layout_analysis": "advanced"
}
```

### 3.3 BMAD-METHOD与Agno集成配置

#### 3.3.1 BMAD代理注册配置

在Agno配置中添加BMAD代理注册信息，实现角色映射关系：

**配置文件路径**：`D:\BMAD-Agno-Integration\agno\config\agents_registry.yaml`

```yaml
# BMAD代理注册配置
bmad_agents:
  # domain-expert映射到analyst和architect
  domain_expert:
    - type: "analyst-agent"
      endpoint: "/api/bmad/analyst"
      description: "需求分析、竞品调研、用户画像"
    - type: "architect-agent"
      endpoint: "/api/bmad/architect"
      description: "技术选型、架构设计、性能优化"
  # planner映射到pm
  planner:
    - type: "pm-agent"
      endpoint: "/api/bmad/pm"
      description: "产品规划、原型设计、进度管理"
  # executor映射到dev
  executor:
    - type: "dev-agent"
      endpoint: "/api/bmad/dev"
      description: "代码实现、单元测试、文档编写"
  # validator映射到qa
  validator:
    - type: "qa-agent"
      endpoint: "/api/bmad/qa"
      description: "测试用例、自动化测试、质量保障"

# 任务流编排配置
task_flows:
  development:
    steps:
      - role: "domain_expert"
        task_type: "requirement_analysis"
      - role: "planner"
        task_type: "prd_generation"
      - role: "executor"
        task_type: "code_implementation"
      - role: "validator"
        task_type: "quality_assurance"
    memory_sharing: true  # 启用Agno三级记忆系统共享
```

#### 3.3.2 记忆系统集成配置

配置Agno记忆系统与BMAD知识库的双向同步：

**配置文件路径**：`D:\BMAD-Agno-Integration\bmad\config\memory_sync.mjs`

```javascript
// BMAD与Agno记忆系统同步配置
export const memorySyncConfig = {
  // 同步开关
  enabled: true,
  
  // Agno记忆系统访问配置（通过APISIX网关）
  agnoMemoryService: {
    baseUrl: "http://127.0.0.1:8080/api/agno/memory",
    syncInterval: 300000, // 5分钟同步一次
    requestTimeout: 10000,
  },
  
  // 记忆标签配置
  memoryTags: {
    // BMAD生成的内容标签
    bmadToAgno: ["development", "bmad-generated", "code", "prd", "architecture"],
    // Agno提供的历史记忆标签
    agnoToBmad: ["project_history", "team_preferences", "coding_standards"],
  },
  
  // 同步策略
  syncStrategy: {
    // 项目历史同步（高优先级）
    projectHistory: {
      priority: "high",
      maxItems: 50,
      timeWindowDays: 30,
    },
    // 代码规范同步（中优先级）
    codingStandards: {
      priority: "medium",
      syncOnChange: true,
    },
    // 团队偏好同步（低优先级）
    teamPreferences: {
      priority: "low",
      syncInterval: 3600000, // 1小时同步一次
    },
  },
  
  // 冲突解决策略
  conflictResolution: "timestamp-based", // 基于时间戳的冲突解决
};
```

### 3.4 BMAD-METHOD与Agno集成验证

**脚本路径**：`D:\BMAD-Agno-Integration\start-all.bat`

```batch
@echo off

REM 一键启动脚本 - 基于新APISIX网关架构
REM APISIX作为独立通信层垂直排列在架构右侧
REM 上层组件通过APISIX网关访问下层组件（LM Studio除外）

echo [1/6] 启动 PostgreSQL 服务（底层数据存储）...
net start postgresql-x64-15

REM 给数据库服务启动时间
timeout /t 5 /nobreak >nul

echo [2/6] 启动 LM Studio 服务（直接通信的特殊组件）...
start "" "D:\LM Studio\LM Studio.exe"
timeout /t 30 /nobreak >nul

echo [3/6] 启动 APISIX 网关（独立通信层，优先级高）...
start cmd /k "cd /d D:\BMAD-Agno-Integration\apisix\bin && apisix start"
timeout /t 8 /nobreak >nul

echo [4/6] 启动语音服务...
start cmd /k "cd /d D:\BMAD-Agno-Integration\voice_service && python voice_server.py"
timeout /t 5 /nobreak >nul

echo [5/6] 启动 Agno 服务（通过APISIX访问数据库，直接访问LM Studio）...
start cmd /k "cd /d D:\BMAD-Agno-Integration\agno && python run.py"
timeout /t 5 /nobreak >nul

echo [6/6] 启动 BMAD 服务（通过APISIX访问Agno和数据库，直接访问LM Studio）...
start cmd /k "cd /d D:\BMAD-Agno-Integration\bmad && npm run start:local"
timeout /t 5 /nobreak >nul

echo.
echo 所有服务已启动，请检查日志确认服务状态
echo ------------------------------------------------------
echo 服务架构说明：
echo - APISIX网关作为独立通信层运行在 http://localhost:8080
echo - Agno/BMAD通过APISIX网关访问PostgreSQL
echo - Agno/BMAD直接访问LM Studio，不经过APISIX网关
echo - 所有组件间通信遵循右侧垂直网关架构设计
echo - BMAD代理已注册到Agno：analyst/pm/architect/dev/qa
echo - Agno三级记忆系统与BMAD知识库已启用双向同步
echo ------------------------------------------------------
echo 请通过APISIX网关访问系统: http://localhost:8080
```

### 3.5 BMAD-METHOD运维与故障处理

#### 3.5.1 功能验证测试

**测试脚本路径**：`D:\BMAD-Agno-Integration\tests\integration_test.py`

```python
# BMAD-Agno集成验证测试脚本
import requests
import json
import time

# APISIX网关地址
gateway_url = "http://127.0.0.1:8080"

# 1. 验证BMAD代理注册
print("[测试1] 验证BMAD代理注册...")
try:
    response = requests.get(f"{gateway_url}/api/agno/agents/registry")
    if response.status_code == 200:
        agents = response.json()
        print(f"注册的BMAD代理数量: {len(agents.get('bmad_agents', {}))}")
        print("BMAD代理注册验证通过")
    else:
        print(f"BMAD代理注册验证失败: {response.status_code}")
except Exception as e:
    print(f"BMAD代理注册验证异常: {str(e)}")

# 2. 验证角色映射关系
print("\n[测试2] 验证角色映射关系...")
try:
    # 检查domain-expert是否映射到analyst和architect
    response = requests.get(f"{gateway_url}/api/agno/agents/mappings")
    if response.status_code == 200:
        mappings = response.json()
        domain_expert_mappings = mappings.get('domain_expert', [])
        has_analyst = any('analyst' in agent['type'] for agent in domain_expert_mappings)
        has_architect = any('architect' in agent['type'] for agent in domain_expert_mappings)
        
        if has_analyst and has_architect:
            print("domain-expert角色映射验证通过")
        else:
            print("domain-expert角色映射验证失败")
    else:
        print(f"角色映射验证失败: {response.status_code}")
except Exception as e:
    print(f"角色映射验证异常: {str(e)}")

# 3. 验证记忆系统同步
print("\n[测试3] 验证记忆系统同步...")
try:
    # 向BMAD添加测试记忆
    test_memory = {
        "content": "测试代码规范：优先使用函数式组件",
        "tags": ["coding_standards", "bmad-generated"],
    }
    
    response = requests.post(
        f"{gateway_url}/api/bmad/memory/add",
        headers={"Content-Type": "application/json"},
        data=json.dumps(test_memory)
    )
    
    if response.status_code == 200:
        # 等待同步完成
        print("添加测试记忆成功，等待同步...")
        time.sleep(5)
        
        # 从Agno查询同步的记忆
        response = requests.get(
            f"{gateway_url}/api/agno/memory/search?query=测试代码规范"
        )
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results and any('测试代码规范' in result.get('content', '') for result in results):
                print("记忆系统同步验证通过")
            else:
                print("记忆系统同步验证失败")
        else:
            print(f"Agno记忆查询失败: {response.status_code}")
    else:
        print(f"BMAD记忆添加失败: {response.status_code}")
except Exception as e:
    print(f"记忆系统同步验证异常: {str(e)}")

print("\n集成验证测试完成")
```

#### 3.5.2 完整业务流程验证

```batch
REM 运行完整业务流程验证脚本
python D:\BMAD-Agno-Integration\tests\business_flow_test.py
```

**业务流程测试脚本**：验证从需求到代码的完整开发流程，确保Agno正确调度BMAD代理：
1. 提交开发任务（如"开发待办事项App MVP"）
2. 验证Agno自动调用BMAD analyst-agent进行需求分析
3. 验证Agno调用pm-agent生成PRD
4. 验证Agno调用dev-agent生成代码
5. 验证Agno调用qa-agent进行代码审查
6. 验证最终输出可运行的代码包

### 3.6 一键启动脚本

#### 3.6.1 常见故障处理

| 故障现象 | 排查步骤 |
|---------|----------|
| BMAD代理注册失败 | 1. 检查APISIX网关中BMAD服务路由配置<br>2. 确认BMAD服务状态和端口<br>3. 验证`agents_registry.yaml`配置文件格式 |
| 角色映射关系错误 | 1. 检查`agents_registry.yaml`中的角色映射配置<br>2. 重启Agno服务使配置生效<br>3. 通过API验证映射关系：`GET /api/agno/agents/mappings` |
| 记忆系统同步失败 | 1. 检查`memory_sync.mjs`配置<br>2. 验证PostgreSQL数据库连接<br>3. 查看BMAD和Agno日志中的同步错误信息<br>4. 尝试手动触发同步：`POST /api/bmad/memory/sync` |
| BMAD代理响应超时 | 1. 检查LM Studio服务状态<br>2. 增加timeout参数值<br>3. 降低模型复杂度或参数规模<br>4. 验证APISIX网关路由配置 |
| 开发流程中断 | 1. 检查Agno任务流配置<br>2. 验证各代理之间的数据传递<br>3. 查看Agno协调层日志<br>4. 尝试从断点恢复：`POST /api/agno/task/resume?task_id=xxx` |

#### 3.6.2 服务监控配置

**监控脚本路径**：`D:\BMAD-Agno-Integration\monitoring\health_check.py`

```python
# BMAD-Agno集成健康检查脚本
import requests
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    filename='D:\BMAD-Agno-Integration\logs\health_check.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 监控目标
services = [
    {"name": "APISIX Gateway", "url": "http://127.0.0.1:8080/v1/models", "timeout": 5},
    {"name": "LM Studio", "url": "http://127.0.0.1:1234/v1/models", "timeout": 5},
    {"name": "Agno Service", "url": "http://127.0.0.1:8080/api/agno/health", "timeout": 10},
    {"name": "BMAD Service", "url": "http://127.0.0.1:8080/api/bmad/health", "timeout": 10},
    {"name": "PostgreSQL (via Gateway)", "url": "http://127.0.0.1:8080/api/db/health", "timeout": 5},
]

# BMAD代理监控
bmad_agents = ["analyst", "pm", "architect", "dev", "qa"]

def check_service(service):
    """检查单个服务健康状态"""
    try:
        response = requests.get(service["url"], timeout=service["timeout"])
        if response.status_code == 200:
            logging.info(f"服务正常: {service['name']}")
            return True
        else:
            logging.error(f"服务异常: {service['name']}, 状态码: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"服务不可达: {service['name']}, 错误: {str(e)}")
        return False

def check_bmad_agents():
    """检查BMAD代理状态"""
    all_healthy = True
    for agent in bmad_agents:
        try:
            response = requests.get(
                f"http://127.0.0.1:8080/api/bmad/{agent}/health",
                timeout=5
            )
            if response.status_code != 200:
                logging.error(f"BMAD代理异常: {agent}, 状态码: {response.status_code}")
                all_healthy = False
            else:
                logging.info(f"BMAD代理正常: {agent}")
        except Exception as e:
            logging.error(f"BMAD代理不可达: {agent}, 错误: {str(e)}")
            all_healthy = False
    return all_healthy

def main():
    """主监控循环"""
    logging.info("=== 开始健康检查 ===")
    
    # 检查核心服务
    services_healthy = all(check_service(service) for service in services)
    
    # 检查BMAD代理
    agents_healthy = check_bmad_agents()
    
    # 检查集成状态
    try:
        response = requests.get("http://127.0.0.1:8080/api/agno/integration/status", timeout=5)
        integration_status = response.json()
        if integration_status.get("status") == "healthy":
            logging.info("Agno-BMAD集成状态: 正常")
        else:
            logging.warning(f"Agno-BMAD集成状态: 异常, 详情: {integration_status}")
    except Exception as e:
        logging.error(f"集成状态检查失败: {str(e)}")
    
    if services_healthy and agents_healthy:
        logging.info("=== 健康检查结果: 所有服务正常 ===")
    else:
        logging.warning("=== 健康检查结果: 发现异常服务 ===")

if __name__ == "__main__":
    main()
```

## 四、核心功能实现

### 4.1 语音交互核心功能

语音交互系统作为上层组件，遵循APISIX网关架构设计，通过网关访问其他服务（如Agno和PostgreSQL），但直接与LM Studio进行通信以优化性能。

```python
from voice_module import ASREngine, TTSEngine, VoiceprintEngine
import numpy as np
import pyaudio
import requests
import json

# 初始化语音系统
class VoiceInteractionSystem:
    def __init__(self):
        # 初始化ASR
        self.asr = ASREngine(model_path="D:/models/whisper/whisper-small.onnx")
        # 初始化TTS
        self.tts = TTSEngine(model_path="D:/models/tts/vits-zh-hf.pth")
        # 初始化声纹识别
        self.voiceprint = VoiceprintEngine(model_path="D:/models/voiceprint/ecapa-tdnn.onnx")
        # 初始化音频设备
        self.pa = pyaudio.PyAudio()
        
        # APISIX网关配置 - 作为独立通信层
        self.gateway_url = "http://127.0.0.1:8080"
        # LM Studio直接通信配置
        self.lm_studio_url = "http://127.0.0.1:1234/v1"
        
    def listen_and_recognize(self, duration=5):
        """录音并识别"""
        # 配置录音参数
        stream = self.pa.open(format=pyaudio.paFloat32,
                             channels=1,
                             rate=16000,
                             input=True,
                             frames_per_buffer=1024)
        
        print("正在聆听...")
        frames = []
        for i in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(np.frombuffer(data, dtype=np.float32))
        
        stream.stop_stream()
        stream.close()
        
        # 合并音频数据
        audio_data = np.concatenate(frames)
        
        # 语音识别
        text = self.asr.recognize(audio_data)
        print(f"识别结果: {text}")
        return text
    
    def speak(self, text, emotion="neutral"):
        """文本转语音"""
        # 生成音频
        audio_data = self.tts.synthesize(text, emotion=emotion)
        
        # 播放音频
        stream = self.pa.open(format=pyaudio.paFloat32,
                             channels=1,
                             rate=22050,
                             output=True)
        
        stream.write(audio_data.tobytes())
        stream.stop_stream()
        stream.close()
        
    def process_with_llm_direct(self, text):
        """直接与LM Studio通信处理文本（不通过APISIX网关）"""
        try:
            print(f"通过直接连接访问LM Studio处理文本...")
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer lm-studio-local"
            }
            data = {
                "model": "lmstudio-community/Llama-3-8B-Instruct-GGUF",
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 1000,
                "temperature": 0.2
            }
            
            # 直接连接到LM Studio，绕过APISIX网关
            response = requests.post(
                f"{self.lm_studio_url}/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"LM Studio直接通信错误: {response.status_code}")
                return "抱歉，无法处理您的请求。"
        except Exception as e:
            print(f"LM Studio通信异常: {str(e)}")
            return "处理请求时发生错误。"
    
    def enroll_speaker(self, speaker_name, duration=10):
        """注册说话人 - 通过APISIX网关存储到PostgreSQL"""
        print(f"请说10秒钟的话，用于注册{speaker_name}...")
        audio_data = self._record_audio(duration)
        embedding = self.voiceprint.extract_embedding(audio_data)
        
        # 通过APISIX网关存储到PostgreSQL
        try:
            print(f"通过APISIX网关存储说话人声纹信息...")
            headers = {"Content-Type": "application/json"}
            data = {
                "speaker_name": speaker_name,
                "embedding": embedding.tolist()
            }
            
            # 访问APISIX网关，由网关路由到正确的服务
            response = requests.post(
                f"{self.gateway_url}/api/agno/voice/enroll",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                print(f"说话人{speaker_name}注册成功（通过APISIX网关）")
            else:
                print(f"通过网关注册失败: {response.status_code}")
                # 降级：本地存储
                self.voiceprint.save_embedding(speaker_name, embedding)
                print(f"已降级到本地存储")
        except Exception as e:
            print(f"网关通信异常，降级到本地存储: {str(e)}")
            self.voiceprint.save_embedding(speaker_name, embedding)
    
    def verify_speaker(self, duration=5):
        """验证说话人 - 通过APISIX网关查询PostgreSQL"""
        print("请说话进行身份验证...")
        audio_data = self._record_audio(duration)
        embedding = self.voiceprint.extract_embedding(audio_data)
        
        # 通过APISIX网关查询数据库
        try:
            print(f"通过APISIX网关进行声纹验证...")
            headers = {"Content-Type": "application/json"}
            data = {
                "embedding": embedding.tolist()
            }
            
            # 访问APISIX网关
            response = requests.post(
                f"{self.gateway_url}/api/agno/voice/verify",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("matched"):
                    speaker_name = result["speaker_name"]
                    confidence = result["confidence"]
                    print(f"识别到说话人: {speaker_name} (置信度: {confidence:.2f}) - 通过APISIX网关")
                    return speaker_name, confidence
                else:
                    print("未识别到已知说话人（网关查询）")
                    return None, 0
            else:
                print(f"网关验证失败: {response.status_code}，降级到本地验证")
                # 降级：本地验证
                result = self.voiceprint.identify_speaker(embedding)
                if result:
                    speaker_name, confidence = result
                    print(f"识别到说话人(本地): {speaker_name} (置信度: {confidence:.2f})")
                    return speaker_name, confidence
                else:
                    print("本地验证也未识别到已知说话人")
                    return None, 0
        except Exception as e:
            print(f"网关通信异常，降级到本地验证: {str(e)}")
            result = self.voiceprint.identify_speaker(embedding)
            if result:
                speaker_name, confidence = result
                return speaker_name, confidence
            else:
                return None, 0
    
    def _record_audio(self, duration):
        """录音辅助函数"""
        stream = self.pa.open(format=pyaudio.paFloat32,
                             channels=1,
                             rate=16000,
                             input=True,
                             frames_per_buffer=1024)
        
        frames = []
        for i in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(np.frombuffer(data, dtype=np.float32))
        
        stream.stop_stream()
        stream.close()
        
        return np.concatenate(frames)

# 使用示例
def voice_interaction_demo():
    # 初始化语音系统
    voice_system = VoiceInteractionSystem()
    
    print("=== 语音交互系统启动 ===")
    print(f"- APISIX网关地址: {voice_system.gateway_url}")
    print(f"- LM Studio直接地址: {voice_system.lm_studio_url}")
    print("- 通信架构: 遵循APISIX右侧垂直网关设计")
    print("- 数据流向: 语音服务 → APISIX网关 → 其他服务")
    print("- 优化路径: 语音服务 → 直接连接LM Studio")
    print("=======================")
    
    # 语音交互循环
    while True:
        try:
            # 监听用户输入
            text = voice_system.listen_and_recognize()
            
            # 简单指令处理
            if "退出" in text or "exit" in text.lower():
                voice_system.speak("再见，祝您有愉快的一天！")
                break
            elif "你好" in text:
                voice_system.speak("你好！我是您的AI助手，有什么可以帮助您的吗？")
            elif "注册" in text:
                voice_system.speak("请告诉我您的名字，以便注册声纹")
                name = voice_system.listen_and_recognize()
                voice_system.enroll_speaker(name)
                voice_system.speak(f"{name}，您的声纹已成功注册！")
            elif "验证" in text:
                name, confidence = voice_system.verify_speaker()
                if name:
                    voice_system.speak(f"验证成功，欢迎回来，{name}！")
                else:
                    voice_system.speak("验证失败，请先注册声纹")
            else:
                # 使用直接连接LM Studio处理复杂请求
                print("处理复杂请求，使用直接连接LM Studio...")
                response = voice_system.process_with_llm_direct(text)
                voice_system.speak(response)
                
        except KeyboardInterrupt:
            print("\n程序已停止")
            break
    
    # 清理资源
    voice_system.pa.terminate()

# 启动语音交互演示
if __name__ == "__main__":
    voice_interaction_demo()
```

### 4.2 视频到PRD自动生成

视频到PRD自动生成功能遵循APISIX网关架构设计，通过网关访问Agno服务和PostgreSQL数据库进行流程管理和存储，同时直接与LM Studio进行多模态模型调用以优化性能。

```python
from agno.tool_registry import register_tool
import cv2
import ffmpeg
import os
import requests
import json
from agno.llm_client import get_llm_client

# 全局配置 - 遵循APISIX网关架构
GATEWAY_URL = "http://127.0.0.1:8080"  # APISIX独立通信层
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"  # LM Studio直接访问

# 步骤1: 提取视频关键帧
@register_tool(name="extract_video_frames", desc="提取视频关键帧，用于分析")
def extract_video_frames(video_path: str, output_dir: str = "./video_frames") -> str:
    # 记录任务到网关管理的任务系统
    try:
        print(f"通过APISIX网关注册视频处理任务...")
        headers = {"Content-Type": "application/json"}
        data = {
            "task_type": "frame_extraction",
            "video_path": video_path,
            "status": "started"
        }
        
        # 通过APISIX网关记录任务
        response = requests.post(
            f"{GATEWAY_URL}/api/agno/tasks",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            task_id = response.json().get("task_id")
            print(f"任务已在网关注册，ID: {task_id}")
    except Exception as e:
        print(f"网关任务注册失败，继续本地处理: {str(e)}")
    
    # 执行帧提取
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # FFmpeg命令: 提取I帧(关键帧)
    ffmpeg.input(video_path).output(
        f"{output_dir}/frame_%04d.jpg", 
        vf="select='eq(pict_type\\,I)'", 
        vsync="vfr"
    ).run(overwrite_output=True)
    
    # 更新任务状态
    try:
        if 'task_id' in locals():
            requests.put(
                f"{GATEWAY_URL}/api/agno/tasks/{task_id}",
                headers=headers,
                data=json.dumps({"status": "completed", "frame_count": len(os.listdir(output_dir))})
            )
    except Exception:
        pass
    
    return f"关键帧提取完成:{output_dir},共{len(os.listdir(output_dir))}帧"

# 步骤2: 生成PRD
@register_tool(name="video_to_prd", desc="分析视频内容，生成产品PRD文档")
def video_to_prd(video_path: str, product_name: str) -> str:
    print(f"=== 视频到PRD处理流程 (APISIX网关架构) ===")
    print(f"- 网关路径: 通过APISIX网关访问Agno服务和数据库")
    print(f"- 优化路径: 直接访问LM Studio进行多模态推理")
    print(f"========================================")
    
    # 提取关键帧
    frame_dir = extract_video_frames(video_path).split(":")[1].split(",")[0]
    # 读取第一帧(封面)
    first_frame = cv2.imread(f"{frame_dir}/frame_0001.jpg")
    _, img_encoded = cv2.imencode(".jpg", first_frame)
    img_hex = img_encoded.tobytes().hex()  # 转为十六进制格式

    # 直接调用LM Studio多模态模型（不通过APISIX网关，优化性能）
    print(f"直接连接LM Studio进行多模态推理...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer lm-studio-local"
    }
    
    prompt = f"分析这个产品演示视频，为{product_name}生成一份详细PRD，包含:1.产品概述;2.UI设计;3.功能特性;4.技术要求"
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"hex:{img_hex}"}}
        ]}
    ]
    
    data = {
        "model": "lmstudio-community/Qwen-VL-7B-GGUF",
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.1
    }
    
    # 直接连接到LM Studio，绕过APISIX网关
    response = requests.post(
        f"{LM_STUDIO_URL}/chat/completions",
        headers=headers,
        data=json.dumps(data)
    )
    
    if response.status_code == 200:
        prd_content = response.json()["choices"][0]["message"]["content"]
        
        # 保存PRD文档到本地
        prd_path = f"./{product_name}_prd.md"
        with open(prd_path, "w", encoding="utf-8") as f:
            f.write(prd_content)
        
        # 通过APISIX网关将PRD保存到数据库
        try:
            print(f"通过APISIX网关将PRD保存到数据库...")
            db_headers = {"Content-Type": "application/json"}
            db_data = {
                "product_name": product_name,
                "prd_content": prd_content,
                "video_path": video_path,
                "timestamp": "auto"
            }
            
            # 通过APISIX网关保存到PostgreSQL
            db_response = requests.post(
                f"{GATEWAY_URL}/api/agno/prd/save",
                headers=db_headers,
                data=json.dumps(db_data)
            )
            
            if db_response.status_code == 200:
                db_id = db_response.json().get("id")
                print(f"PRD已通过网关保存到数据库，ID: {db_id}")
        except Exception as e:
            print(f"网关保存PRD到数据库失败: {str(e)}")
        
        return f"PRD生成完成，路径:./{product_name}_prd.md"
    else:
        error_msg = f"LM Studio直接调用失败: {response.status_code}"
        print(error_msg)
        return error_msg
```

### 4.2 经理-员工协作模式示例

经理-员工协作模式在APISIX网关架构下进行了优化，所有业务协作流程通过APISIX网关进行管理和调度，而AI模型推理则直接与LM Studio进行通信以保证低延迟。

```python
from agno.agents import Agent
from agno.team import Team
from agno.task_queue import TaskQueue
from agno.llm_client import get_llm_client
import requests
import json
import time
import uuid

# 全局配置 - 遵循APISIX网关架构
GATEWAY_URL = "http://127.0.0.1:8080"  # APISIX独立通信层
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"  # LM Studio直接访问

# 定义Agent类型 - 集成APISIX网关通信
class ManagerAgent(Agent):
    def __init__(self, name="项目经理"):
        super().__init__(name=name)
        self.llm = get_llm_client()
        self.gateway_url = GATEWAY_URL
    
    def assign_task(self, task: str, team: Team) -> str:
        print(f"[网关路径] 经理通过APISIX网关注册和分发任务...")
        
        # 1. 通过APISIX网关注册任务
        task_id = self._register_task_with_gateway(task)
        if not task_id:
            task_id = f"local_{str(uuid.uuid4())[:8]}"
            print(f"[降级] 网关注册失败，使用本地任务ID: {task_id}")
        
        # 2. 分析任务，选择合适的员工Agent
        print(f"[直接路径] 经理直接连接LM Studio进行任务分析...")
        
        # 直接调用LM Studio进行任务分析
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"分析任务'{task}'，应该分配给哪个类型的员工? (只返回员工类型，如：开发者、设计师、测试工程师等)"
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50
        }
        
        # 直接连接LM Studio，绕过APISIX网关
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            agent_type = response.json()["choices"][0]["message"]["content"].strip()
            
            # 3. 通过APISIX网关更新任务分配状态
            try:
                self._update_task_status_with_gateway(task_id, "assigned", {"assigned_to": agent_type})
                print(f"[网关路径] 任务 {task_id} 已通过网关分配给 {agent_type}")
            except Exception as e:
                print(f"[降级] 网关任务状态更新失败: {str(e)}")
            
            return f"{self.name}将任务'{task}'(ID: {task_id})分配给{agent_type}"
        else:
            return f"任务分析失败，LM Studio调用错误: {response.status_code}"
    
    def _register_task_with_gateway(self, task_description: str) -> str:
        """通过APISIX网关注册任务到任务管理系统"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "task_description": task_description,
                "manager_name": self.name,
                "status": "pending",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/agno/task_queue",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("task_id")
            return None
        except Exception:
            return None
    
    def _update_task_status_with_gateway(self, task_id: str, status: str, metadata: dict = None):
        """通过APISIX网关更新任务状态"""
        headers = {"Content-Type": "application/json"}
        data = {"status": status}
        if metadata:
            data.update(metadata)
        
        requests.put(
            f"{self.gateway_url}/api/agno/task_queue/{task_id}",
            headers=headers,
            data=json.dumps(data)
        )

class DeveloperAgent(Agent):
    def __init__(self, name="开发者"):
        super().__init__(name=name)
        self.llm = get_llm_client()
        self.gateway_url = GATEWAY_URL
    
    def develop(self, task: str, task_id: str = None) -> str:
        # 1. 通过APISIX网关更新任务状态为进行中
        if task_id and task_id.startswith("local_") is False:
            try:
                self._update_task_status(task_id, "in_progress")
                print(f"[网关路径] 开发任务 {task_id} 状态已更新为进行中")
            except Exception as e:
                print(f"[降级] 网关任务状态更新失败: {str(e)}")
        
        # 2. 直接调用LM Studio执行开发任务
        print(f"[直接路径] 开发者直接连接LM Studio进行开发...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"作为开发者，请详细完成以下任务: {task}"
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            
            # 3. 通过APISIX网关更新任务状态为已完成
            if task_id and task_id.startswith("local_") is False:
                try:
                    self._update_task_status(task_id, "completed", {"result": result[:100] + "..." if len(result) > 100 else result})
                    print(f"[网关路径] 开发任务 {task_id} 状态已更新为已完成")
                except Exception:
                    pass
            
            return result
        else:
            return f"开发任务执行失败，LM Studio调用错误: {response.status_code}"
    
    def _update_task_status(self, task_id: str, status: str, metadata: dict = None):
        """通过APISIX网关更新任务状态"""
        headers = {"Content-Type": "application/json"}
        data = {"status": status}
        if metadata:
            data.update(metadata)
        
        requests.put(
            f"{self.gateway_url}/api/agno/task_queue/{task_id}",
            headers=headers,
            data=json.dumps(data)
        )

class DesignerAgent(Agent):
    def __init__(self, name="设计师"):
        super().__init__(name=name)
        self.llm = get_llm_client()
        self.gateway_url = GATEWAY_URL
    
    def design(self, task: str, task_id: str = None) -> str:
        # 1. 通过APISIX网关更新任务状态为进行中
        if task_id and task_id.startswith("local_") is False:
            try:
                headers = {"Content-Type": "application/json"}
                data = {"status": "in_progress"}
                requests.put(
                    f"{self.gateway_url}/api/agno/task_queue/{task_id}",
                    headers=headers,
                    data=json.dumps(data)
                )
                print(f"[网关路径] 设计任务 {task_id} 状态已更新为进行中")
            except Exception as e:
                print(f"[降级] 网关任务状态更新失败: {str(e)}")
        
        # 2. 直接调用LM Studio执行设计任务
        print(f"[直接路径] 设计师直接连接LM Studio进行设计...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"作为设计师，请详细完成以下任务: {task}"
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            
            # 3. 通过APISIX网关更新任务状态为已完成
            if task_id and task_id.startswith("local_") is False:
                try:
                    headers = {"Content-Type": "application/json"}
                    data = {"status": "completed", "result": result[:100] + "..." if len(result) > 100 else result}
                    requests.put(
                        f"{self.gateway_url}/api/agno/task_queue/{task_id}",
                        headers=headers,
                        data=json.dumps(data)
                    )
                    print(f"[网关路径] 设计任务 {task_id} 状态已更新为已完成")
                except Exception:
                    pass
            
            return result
        else:
            return f"设计任务执行失败，LM Studio调用错误: {response.status_code}"

# 组建团队
def create_team() -> Team:
    print("=== 团队创建 (APISIX网关架构) ===")
    print(f"- 网关路径: 通过APISIX网关管理任务分配和状态")
    print(f"- 优化路径: 所有Agent直接连接LM Studio进行AI推理")
    print(f"================================")
    
    # 尝试通过APISIX网关初始化团队配置
    try:
        print("[网关路径] 通过APISIX网关加载团队配置...")
        headers = {"Content-Type": "application/json"}
        response = requests.get(
            f"{GATEWAY_URL}/api/agno/team/config",
            headers=headers
        )
        
        if response.status_code == 200:
            config = response.json()
            print(f"[网关路径] 团队配置已从网关加载: {config['team_name']}")
    except Exception as e:
        print(f"[降级] 网关加载配置失败，使用默认配置: {str(e)}")
    
    # 创建经理
    manager = ManagerAgent()
    # 创建员工
    developers = [DeveloperAgent(name=f"开发者{i}") for i in range(3)]
    designers = [DesignerAgent(name=f"设计师{i}") for i in range(2)]
    # 创建团队
    team = Team(manager=manager)
    team.add_members(developers + designers)
    return team

# 团队协作示例
def team_collaboration_demo():
    print("\n=== 团队协作演示 (APISIX网关架构) ===\n")
    
    # 创建团队
    team = create_team()
    
    # 创建任务队列
    tasks = [
        "设计用户登录界面",
        "开发用户认证API",
        "优化数据库查询性能"
    ]
    
    # 执行任务
    for task in tasks:
        print(f"\n任务: {task}")
        print("-" * 50)
        
        # 1. 经理分配任务
        assignment_result = team.manager.assign_task(task, team)
        print(f"分配结果: {assignment_result}")
        
        # 2. 提取任务ID和分配对象
        try:
            task_id = assignment_result.split("(ID: ")[1].split(")")[0]
            assigned_to = assignment_result.split("分配给")[1]
        except (IndexError, ValueError):
            task_id = None
            assigned_to = "未知"
        
        # 3. 执行任务
        result = "任务执行失败"
        if "开发者" in assigned_to:
            # 找到一个开发者执行任务
            for member in team.members:
                if isinstance(member, DeveloperAgent):
                    result = member.develop(task, task_id)
                    break
        elif "设计师" in assigned_to:
            # 找到一个设计师执行任务
            for member in team.members:
                if isinstance(member, DesignerAgent):
                    result = member.design(task, task_id)
                    break
        
        # 4. 打印结果摘要
        print(f"任务执行结果摘要: {result[:150]}..." if len(result) > 150 else f"任务执行结果: {result}")
        print("="*50)
```

### 4.3 BMAD-METHOD开发流程实现

BMAD-METHOD开发流程作为核心功能之一，在APISIX网关架构下实现了完整的开发方法论集成，通过Agno多智能体框架协调各角色代理完成从需求到交付的全流程。

```python
from agno.agents import Agent
from agno.team import Team
from agno.task_queue import TaskQueue
from agno.llm_client import get_llm_client
import requests
import json
import time
import uuid

# 全局配置 - 遵循APISIX网关架构
GATEWAY_URL = "http://127.0.0.1:8080"  # APISIX独立通信层
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"  # LM Studio直接访问

# BMAD-METHOD核心角色实现 - 通过APISIX网关架构
class AnalystAgent(Agent):
    """分析师代理 - 对应BMAD-METHOD中的analyst-agent
    负责需求分析、竞品调研、用户画像"""
    
    def __init__(self, name="分析师"):
        super().__init__(name=name)
        self.role_type = "analyst-agent"  # BMAD角色类型
        self.gateway_url = GATEWAY_URL
    
    def analyze_requirements(self, requirement: str, project_id: str = None) -> dict:
        """分析用户需求并生成需求文档"""
        print(f"[网关路径] 分析师通过APISIX网关注册分析任务...")
        
        # 1. 通过APISIX网关注册分析任务
        analysis_id = self._register_analysis_task(requirement, project_id)
        
        # 2. 直接调用LM Studio进行需求分析
        print(f"[直接路径] 分析师直接连接LM Studio进行需求分析...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"作为产品分析师，请详细分析以下需求:\n{requirement}\n\n请提供：\n1. 需求概述\n2. 目标用户分析\n3. 核心功能点\n4. 竞品分析\n5. 技术可行性初步评估"
        
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500
        }
        
        # 直接连接LM Studio进行分析
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            analysis_result = response.json()["choices"][0]["message"]["content"]
            
            # 3. 通过APISIX网关保存分析结果
            try:
                self._save_analysis_result(analysis_id, analysis_result)
                print(f"[网关路径] 需求分析结果已通过网关保存，ID: {analysis_id}")
            except Exception as e:
                print(f"[降级] 网关保存分析结果失败: {str(e)}")
            
            return {
                "analysis_id": analysis_id,
                "result": analysis_result,
                "status": "completed"
            }
        else:
            return {
                "analysis_id": analysis_id,
                "error": f"LM Studio调用错误: {response.status_code}",
                "status": "failed"
            }
    
    def _register_analysis_task(self, requirement: str, project_id: str = None) -> str:
        """通过APISIX网关注册分析任务"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "requirement": requirement,
                "project_id": project_id,
                "analyst_name": self.name,
                "status": "started",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/bmad/analyst/task",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("analysis_id")
        except Exception:
            pass
        
        # 降级：返回本地生成的ID
        return f"local_ana_{str(uuid.uuid4())[:8]}"
    
    def _save_analysis_result(self, analysis_id: str, result: str):
        """通过APISIX网关保存分析结果"""
        headers = {"Content-Type": "application/json"}
        data = {
            "analysis_id": analysis_id,
            "result": result,
            "status": "completed",
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        requests.put(
            f"{self.gateway_url}/api/bmad/analyst/task/{analysis_id}",
            headers=headers,
            data=json.dumps(data)
        )

class PMAgent(Agent):
    """产品经理代理 - 对应BMAD-METHOD中的pm-agent
    负责产品规划、原型设计、进度管理"""
    
    def __init__(self, name="产品经理"):
        super().__init__(name=name)
        self.role_type = "pm-agent"  # BMAD角色类型
        self.gateway_url = GATEWAY_URL
    
    def generate_prd(self, analysis_id: str, project_name: str) -> dict:
        """基于分析结果生成PRD文档"""
        print(f"[网关路径] PM通过APISIX网关获取分析结果...")
        
        # 1. 通过APISIX网关获取分析结果
        analysis_result = self._get_analysis_result(analysis_id)
        if not analysis_result:
            return {
                "status": "failed",
                "error": "无法获取分析结果"
            }
        
        # 2. 直接调用LM Studio生成PRD
        print(f"[直接路径] PM直接连接LM Studio生成PRD文档...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"作为产品经理，请根据以下需求分析生成详细的PRD文档：\n{analysis_result}\n\n请按照以下结构生成：\n1. 产品概述\n2. 用户故事\n3. 功能需求（详细列表）\n4. 非功能需求\n5. UI/UX设计原则\n6. 开发里程碑\n7. 验收标准"
        
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            prd_content = response.json()["choices"][0]["message"]["content"]
            
            # 3. 通过APISIX网关保存PRD
            prd_id = self._save_prd(prd_content, project_name, analysis_id)
            
            # 4. 通过APISIX网关创建开发计划
            plan_id = self._create_development_plan(prd_id)
            
            return {
                "prd_id": prd_id,
                "plan_id": plan_id,
                "status": "completed"
            }
        else:
            return {
                "error": f"LM Studio调用错误: {response.status_code}",
                "status": "failed"
            }
    
    def _get_analysis_result(self, analysis_id: str) -> str:
        """通过APISIX网关获取分析结果"""
        try:
            response = requests.get(
                f"{self.gateway_url}/api/bmad/analyst/task/{analysis_id}"
            )
            
            if response.status_code == 200:
                return response.json().get("result", "")
        except Exception:
            pass
        return ""
    
    def _save_prd(self, prd_content: str, project_name: str, analysis_id: str) -> str:
        """通过APISIX网关保存PRD"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "project_name": project_name,
                "prd_content": prd_content,
                "analysis_id": analysis_id,
                "created_by": self.name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/bmad/pm/prd",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("prd_id")
        except Exception:
            pass
        return f"local_prd_{str(uuid.uuid4())[:8]}"
    
    def _create_development_plan(self, prd_id: str) -> str:
        """通过APISIX网关创建开发计划"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "prd_id": prd_id,
                "created_by": self.name,
                "status": "draft"
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/bmad/pm/plan",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("plan_id")
        except Exception:
            pass
        return f"local_plan_{str(uuid.uuid4())[:8]}"

class ArchitectAgent(Agent):
    """架构师代理 - 对应BMAD-METHOD中的architect-agent
    负责技术选型、架构设计、性能优化"""
    
    def __init__(self, name="架构师"):
        super().__init__(name=name)
        self.role_type = "architect-agent"  # BMAD角色类型
        self.gateway_url = GATEWAY_URL
    
    def design_architecture(self, prd_id: str) -> dict:
        """基于PRD设计系统架构"""
        print(f"[网关路径] 架构师通过APISIX网关获取PRD...")
        
        # 1. 通过APISIX网关获取PRD
        prd_content = self._get_prd(prd_id)
        if not prd_content:
            return {
                "status": "failed",
                "error": "无法获取PRD文档"
            }
        
        # 2. 直接调用LM Studio设计架构
        print(f"[直接路径] 架构师直接连接LM Studio设计系统架构...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"作为系统架构师，请根据以下PRD设计系统架构：\n{prd_content}\n\n请提供：\n1. 技术栈选型（前后端、数据库等）\n2. 系统整体架构图描述\n3. 核心模块划分\n4. 数据流设计\n5. 关键技术挑战与解决方案\n6. 性能优化策略"
        
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            architecture_content = response.json()["choices"][0]["message"]["content"]
            
            # 3. 通过APISIX网关保存架构设计
            architecture_id = self._save_architecture(architecture_content, prd_id)
            
            return {
                "architecture_id": architecture_id,
                "status": "completed"
            }
        else:
            return {
                "error": f"LM Studio调用错误: {response.status_code}",
                "status": "failed"
            }
    
    def _get_prd(self, prd_id: str) -> str:
        """通过APISIX网关获取PRD"""
        try:
            response = requests.get(
                f"{self.gateway_url}/api/bmad/pm/prd/{prd_id}"
            )
            
            if response.status_code == 200:
                return response.json().get("prd_content", "")
        except Exception:
            pass
        return ""
    
    def _save_architecture(self, architecture_content: str, prd_id: str) -> str:
        """通过APISIX网关保存架构设计"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "prd_id": prd_id,
                "architecture_content": architecture_content,
                "created_by": self.name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/bmad/architect/design",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("architecture_id")
        except Exception:
            pass
        return f"local_arch_{str(uuid.uuid4())[:8]}"

class DevAgent(Agent):
    """开发工程师代理 - 对应BMAD-METHOD中的dev-agent
    负责代码实现、单元测试、文档编写"""
    
    def __init__(self, name="开发工程师"):
        super().__init__(name=name)
        self.role_type = "dev-agent"  # BMAD角色类型
        self.gateway_url = GATEWAY_URL
    
    def implement_feature(self, architecture_id: str, feature_id: str, feature_desc: str) -> dict:
        """根据架构设计实现具体功能"""
        print(f"[网关路径] 开发工程师通过APISIX网关获取架构设计...")
        
        # 1. 通过APISIX网关获取架构设计
        architecture_content = self._get_architecture(architecture_id)
        if not architecture_content:
            return {
                "status": "failed",
                "error": "无法获取架构设计"
            }
        
        # 2. 直接调用LM Studio生成代码
        print(f"[直接路径] 开发工程师直接连接LM Studio生成代码实现...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"作为开发工程师，请根据以下架构设计实现特定功能：\n\n架构设计：\n{architecture_content}\n\n需要实现的功能：{feature_desc}\n\n请提供：\n1. 详细的代码实现\n2. 关键函数的注释\n3. 单元测试示例\n4. 集成说明"
        
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            code_content = response.json()["choices"][0]["message"]["content"]
            
            # 3. 通过APISIX网关保存代码实现
            implementation_id = self._save_implementation(
                code_content, architecture_id, feature_id, feature_desc
            )
            
            return {
                "implementation_id": implementation_id,
                "status": "completed"
            }
        else:
            return {
                "error": f"LM Studio调用错误: {response.status_code}",
                "status": "failed"
            }
    
    def _get_architecture(self, architecture_id: str) -> str:
        """通过APISIX网关获取架构设计"""
        try:
            response = requests.get(
                f"{self.gateway_url}/api/bmad/architect/design/{architecture_id}"
            )
            
            if response.status_code == 200:
                return response.json().get("architecture_content", "")
        except Exception:
            pass
        return ""
    
    def _save_implementation(self, code_content: str, architecture_id: str, 
                           feature_id: str, feature_desc: str) -> str:
        """通过APISIX网关保存代码实现"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "architecture_id": architecture_id,
                "feature_id": feature_id,
                "feature_description": feature_desc,
                "code_content": code_content,
                "implemented_by": self.name,
                "status": "completed",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/bmad/dev/implementation",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("implementation_id")
        except Exception:
            pass
        return f"local_impl_{str(uuid.uuid4())[:8]}"

class QAAgent(Agent):
    """测试工程师代理 - 对应BMAD-METHOD中的qa-agent
    负责测试用例、自动化测试、质量保障"""
    
    def __init__(self, name="测试工程师"):
        super().__init__(name=name)
        self.role_type = "qa-agent"  # BMAD角色类型
        self.gateway_url = GATEWAY_URL
    
    def test_implementation(self, implementation_id: str) -> dict:
        """测试代码实现并生成测试报告"""
        print(f"[网关路径] 测试工程师通过APISIX网关获取代码实现...")
        
        # 1. 通过APISIX网关获取代码实现
        implementation_data = self._get_implementation(implementation_id)
        if not implementation_data:
            return {
                "status": "failed",
                "error": "无法获取代码实现"
            }
        
        code_content = implementation_data.get("code_content", "")
        feature_desc = implementation_data.get("feature_description", "")
        
        # 2. 直接调用LM Studio生成测试报告
        print(f"[直接路径] 测试工程师直接连接LM Studio生成测试报告...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prompt = f"作为测试工程师，请测试以下代码实现并生成测试报告：\n\n功能描述：{feature_desc}\n\n代码实现：\n{code_content}\n\n请提供：\n1. 测试用例清单\n2. 代码审查结果\n3. 潜在问题分析\n4. 改进建议\n5. 质量评分"
        
        data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            test_report = response.json()["choices"][0]["message"]["content"]
            
            # 3. 通过APISIX网关保存测试报告
            test_id = self._save_test_report(test_report, implementation_id)
            
            # 4. 解析测试结果并更新实现状态
            is_passed = self._parse_test_result(test_report)
            self._update_implementation_status(implementation_id, is_passed)
            
            return {
                "test_id": test_id,
                "passed": is_passed,
                "status": "completed"
            }
        else:
            return {
                "error": f"LM Studio调用错误: {response.status_code}",
                "status": "failed"
            }
    
    def _get_implementation(self, implementation_id: str) -> dict:
        """通过APISIX网关获取代码实现"""
        try:
            response = requests.get(
                f"{self.gateway_url}/api/bmad/dev/implementation/{implementation_id}"
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {}
    
    def _save_test_report(self, test_report: str, implementation_id: str) -> str:
        """通过APISIX网关保存测试报告"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "implementation_id": implementation_id,
                "test_report": test_report,
                "tested_by": self.name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/bmad/qa/test",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("test_id")
        except Exception:
            pass
        return f"local_test_{str(uuid.uuid4())[:8]}"
    
    def _parse_test_result(self, test_report: str) -> bool:
        """解析测试结果"""
        # 简单实现：通过关键词判断测试是否通过
        if "质量评分：" in test_report:
            try:
                score_part = test_report.split("质量评分：")[1].strip()
                score = int(score_part.split("/")[0])
                return score >= 80
            except Exception:
                pass
        return "通过" in test_report or "passed" in test_report.lower()
    
    def _update_implementation_status(self, implementation_id: str, is_passed: bool):
        """通过APISIX网关更新实现状态"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "status": "passed" if is_passed else "failed",
                "qa_status_updated": True
            }
            
            requests.put(
                f"{self.gateway_url}/api/bmad/dev/implementation/{implementation_id}",
                headers=headers,
                data=json.dumps(data)
            )
        except Exception:
            pass

# BMAD-METHOD工作流实现
class BMADWorkflow:
    """BMAD-METHOD完整工作流实现"""
    
    def __init__(self):
        # 初始化所有角色代理
        self.analyst = AnalystAgent()
        self.pm = PMAgent()
        self.architect = ArchitectAgent()
        self.dev = DevAgent()
        self.qa = QAAgent()
        
        # 配置APISIX网关
        self.gateway_url = GATEWAY_URL
    
    def execute_workflow(self, project_name: str, requirement: str) -> dict:
        """执行完整的BMAD-METHOD工作流"""
        print(f"=== 开始BMAD-METHOD工作流 - {project_name} ===")
        print(f"[网关路径] 所有业务流程通过APISIX网关管理")
        print(f"[直接路径] 所有AI推理直接连接LM Studio优化性能")
        print("========================================")
        
        # 1. 需求分析阶段
        print("\n[1/5] 需求分析阶段")
        print("-" * 30)
        analysis_result = self.analyst.analyze_requirements(requirement)
        if analysis_result["status"] != "completed":
            return {
                "status": "failed",
                "stage": "analysis",
                "error": analysis_result.get("error", "需求分析失败")
            }
        analysis_id = analysis_result["analysis_id"]
        print(f"✓ 需求分析完成，ID: {analysis_id}")
        
        # 2. PRD生成阶段
        print("\n[2/5] PRD生成阶段")
        print("-" * 30)
        prd_result = self.pm.generate_prd(analysis_id, project_name)
        if prd_result["status"] != "completed":
            return {
                "status": "failed",
                "stage": "prd",
                "error": prd_result.get("error", "PRD生成失败")
            }
        prd_id = prd_result["prd_id"]
        plan_id = prd_result["plan_id"]
        print(f"✓ PRD生成完成，ID: {prd_id}")
        print(f"✓ 开发计划创建完成，ID: {plan_id}")
        
        # 3. 架构设计阶段
        print("\n[3/5] 架构设计阶段")
        print("-" * 30)
        architecture_result = self.architect.design_architecture(prd_id)
        if architecture_result["status"] != "completed":
            return {
                "status": "failed",
                "stage": "architecture",
                "error": architecture_result.get("error", "架构设计失败")
            }
        architecture_id = architecture_result["architecture_id"]
        print(f"✓ 架构设计完成，ID: {architecture_id}")
        
        # 4. 开发实现阶段（示例：实现一个核心功能）
        print("\n[4/5] 开发实现阶段")
        print("-" * 30)
        feature_id = "core_feature_1"
        feature_desc = "实现系统的核心功能模块"
        implementation_result = self.dev.implement_feature(
            architecture_id, feature_id, feature_desc
        )
        if implementation_result["status"] != "completed":
            return {
                "status": "failed",
                "stage": "development",
                "error": implementation_result.get("error", "开发实现失败")
            }
        implementation_id = implementation_result["implementation_id"]
        print(f"✓ 功能实现完成，ID: {implementation_id}")
        
        # 5. 测试验证阶段
        print("\n[5/5] 测试验证阶段")
        print("-" * 30)
        test_result = self.qa.test_implementation(implementation_id)
        if test_result["status"] != "completed":
            return {
                "status": "failed",
                "stage": "testing",
                "error": test_result.get("error", "测试验证失败")
            }
        test_id = test_result["test_id"]
        test_passed = test_result["passed"]
        print(f"✓ 测试验证完成，ID: {test_id}")
        print(f"✓ 测试结果: {'通过' if test_passed else '未通过'}")
        
        # 6. 工作流总结
        print("\n========================================")
        print(f"BMAD-METHOD工作流完成 - {project_name}")
        print(f"整体状态: {'成功' if test_passed else '部分成功'}")
        print("========================================")
        
        return {
            "status": "completed",
            "project_name": project_name,
            "analysis_id": analysis_id,
            "prd_id": prd_id,
            "architecture_id": architecture_id,
            "implementation_id": implementation_id,
            "test_id": test_id,
            "test_passed": test_passed
        }

# BMAD-METHOD与Agno集成的桥梁类
class BMADAgnoIntegration:
    """BMAD-METHOD与Agno多智能体框架的集成接口"""
    
    def __init__(self):
        self.bmad_workflow = BMADWorkflow()
        self.gateway_url = GATEWAY_URL
    
    def register_bmad_to_agno(self):
        """将BMAD代理注册到Agno框架"""
        print("[网关路径] 通过APISIX网关注册BMAD代理到Agno...")
        
        try:
            headers = {"Content-Type": "application/json"}
            # 注册映射关系：BMAD角色 → Agno角色
            mappings = {
                "domain_expert": [
                    {"type": "analyst-agent", "endpoint": "/api/bmad/analyst"},
                    {"type": "architect-agent", "endpoint": "/api/bmad/architect"}
                ],
                "planner": [
                    {"type": "pm-agent", "endpoint": "/api/bmad/pm"}
                ],
                "executor": [
                    {"type": "dev-agent", "endpoint": "/api/bmad/dev"}
                ],
                "validator": [
                    {"type": "qa-agent", "endpoint": "/api/bmad/qa"}
                ]
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/agno/agents/register/bmad",
                headers=headers,
                data=json.dumps(mappings)
            )
            
            if response.status_code == 200:
                print("✓ BMAD代理成功注册到Agno框架")
                return True
            else:
                print(f"注册失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"注册异常: {str(e)}")
            return False
    
    def execute_agno_task_with_bmad(self, task: str, project_name: str = "Default"):
        """通过Agno任务系统执行BMAD工作流"""
        print("[网关路径] 通过APISIX网关将任务从Agno路由到BMAD...")
        
        try:
            # 1. 通过APISIX网关创建任务
            task_id = self._create_agno_task(task, project_name)
            if not task_id:
                return {"status": "failed", "error": "无法创建Agno任务"}
            
            # 2. 执行BMAD工作流
            result = self.bmad_workflow.execute_workflow(project_name, task)
            
            # 3. 更新Agno任务状态
            if result["status"] == "completed":
                self._update_agno_task_status(task_id, "completed", result)
            else:
                self._update_agno_task_status(task_id, "failed", result)
            
            return result
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def _create_agno_task(self, task: str, project_name: str) -> str:
        """通过APISIX网关创建Agno任务"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "task": task,
                "project_name": project_name,
                "type": "bmad_workflow",
                "status": "started"
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/agno/task",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json().get("task_id")
        except Exception:
            pass
        return None
    
    def _update_agno_task_status(self, task_id: str, status: str, result: dict):
        """通过APISIX网关更新Agno任务状态"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "status": status,
                "result": result
            }
            
            requests.put(
                f"{self.gateway_url}/api/agno/task/{task_id}",
                headers=headers,
                data=json.dumps(data)
            )
        except Exception:
            pass

# 示例：执行BMAD-METHOD工作流
def bmad_workflow_demo():
    # 创建BMAD-Agno集成实例
    integration = BMADAgnoIntegration()
    
    # 注册BMAD代理到Agno
    integration.register_bmad_to_agno()
    
    # 示例项目信息
    project_name = "智能待办事项系统"
    requirement = "开发一个支持语音交互的智能待办事项管理系统，用户可以通过语音添加、删除和查询待办事项，并支持任务分类和提醒功能。"
    
    # 执行完整工作流
    result = integration.execute_agno_task_with_bmad(requirement, project_name)
    
    # 打印最终结果
    if result["status"] == "completed":
        print(f"\n🎉 项目 '{project_name}' 已成功完成所有开发流程！")
        print(f"- 需求分析ID: {result['analysis_id']}")
        print(f"- PRD文档ID: {result['prd_id']}")
        print(f"- 架构设计ID: {result['architecture_id']}")
        print(f"- 代码实现ID: {result['implementation_id']}")
        print(f"- 测试结果: {'通过' if result['test_passed'] else '未通过'}")
    else:
        print(f"\n❌ 项目 '{project_name}' 在 {result['stage']} 阶段失败")
        print(f"错误信息: {result['error']}")

# 运行演示
if __name__ == "__main__":
    bmad_workflow_demo()
```

### 4.4 条件路由模式示例

条件路由模式在APISIX网关架构下进行了优化，所有路由决策和工作流状态管理通过APISIX网关进行，而AI推理操作则直接与LM Studio通信以确保低延迟响应。

```python
import requests
import json
import uuid

# 全局配置 - 遵循APISIX网关架构
GATEWAY_URL = "http://127.0.0.1:8080"  # APISIX独立通信层
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"  # LM Studio直接访问

# 定义路由条件函数 - 集成APISIX网关和LM Studio直接通信
def route_by_feasibility(state):
    """根据可行性评估结果动态路由任务 - 基于APISIX网关架构"""
    print(f"[网关路径] 通过APISIX网关记录路由决策...")
    
    # 1. 通过APISIX网关记录当前工作流状态
    workflow_id = state.get("workflow_id", f"wf_{str(uuid.uuid4())[:8]}")
    step_id = state.get("step_id", f"step_{str(uuid.uuid4())[:8]}")
    
    try:
        headers = {"Content-Type": "application/json"}
        gateway_data = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "state": state,
            "timestamp": "auto"
        }
        
        # 通过APISIX网关记录到数据库
        response = requests.post(
            f"{GATEWAY_URL}/api/agno/workflow/state",
            headers=headers,
            data=json.dumps(gateway_data)
        )
        
        if response.status_code == 200:
            print(f"[网关路径] 工作流状态已通过网关保存: {workflow_id}")
    except Exception as e:
        print(f"[降级] 网关保存工作流状态失败: {str(e)}")
    
    # 2. 如果需要，直接调用LM Studio进行高级评估
    if "evaluation_result" not in state:
        print(f"[直接路径] 直接连接LM Studio进行高级可行性评估...")
        
        lm_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        prd_path = state.get("prd_path", "未知路径")
        prompt = f"分析PRD文档的可行性，返回简洁评估结果，包含'可行'、'部分可行'或'不可行'关键词"
        
        lm_data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100
        }
        
        # 直接连接LM Studio，绕过APISIX网关
        try:
            response = requests.post(
                f"{LM_STUDIO_URL}/chat/completions",
                headers=lm_headers,
                data=json.dumps(lm_data)
            )
            
            if response.status_code == 200:
                state["evaluation_result"] = response.json()["choices"][0]["message"]["content"]
                print(f"[直接路径] LM Studio评估完成: {state['evaluation_result']}")
            else:
                state["evaluation_result"] = "默认评估: 部分可行"
                print(f"[降级] LM Studio评估失败，使用默认值")
        except Exception:
            state["evaluation_result"] = "默认评估: 部分可行"
    
    # 3. 根据评估结果进行路由决策
    print(f"[路由决策] 基于评估结果: {state['evaluation_result']}")
    
    if "可行" in state["evaluation_result"]:
        # 并行Agent处理
        selected_targets = ["quick_prototype_agent", "tech_split_agent"]
        print(f"[路由结果] 任务完全可行，路由到并行处理: {', '.join(selected_targets)}")
    elif "部分可行" in state["evaluation_result"]:
        # 单Agent处理
        selected_targets = "tech_split_agent"
        print(f"[路由结果] 任务部分可行，路由到技术拆分: {selected_targets}")
    else:
        # 需求优化
        selected_targets = "req_optimize_agent"
        print(f"[路由结果] 任务需要优化，路由到需求重设计: {selected_targets}")
    
    # 4. 通过APISIX网关记录路由结果
    try:
        if 'workflow_id' in locals():
            update_data = {
                "workflow_id": workflow_id,
                "step_id": step_id,
                "route_decision": selected_targets,
                "status": "routed"
            }
            
            requests.put(
                f"{GATEWAY_URL}/api/agno/workflow/state/{workflow_id}/{step_id}",
                headers=headers,
                data=json.dumps(update_data)
            )
            print(f"[网关路径] 路由决策已通过网关记录")
    except Exception:
        pass
    
    return selected_targets

# 创建增强的Agent类，支持APISIX网关和LM Studio直接通信
class GatewayAwareAgent:
    """支持APISIX网关通信的增强Agent"""
    def __init__(self, name):
        self.name = name
        self.gateway_url = GATEWAY_URL
        self.lm_studio_url = LM_STUDIO_URL
    
    def execute(self, data):
        print(f"[{self.name}] [网关路径] 通过APISIX网关记录任务执行...")
        
        # 1. 通过APISIX网关记录执行状态
        execution_id = f"exec_{str(uuid.uuid4())[:8]}"
        try:
            headers = {"Content-Type": "application/json"}
            gateway_data = {
                "execution_id": execution_id,
                "agent_name": self.name,
                "input_data": data,
                "status": "started",
                "timestamp": "auto"
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/agno/agent/execution",
                headers=headers,
                data=json.dumps(gateway_data)
            )
            
            if response.status_code == 200:
                print(f"[{self.name}] [网关路径] 执行记录已通过网关创建")
        except Exception as e:
            print(f"[{self.name}] [降级] 网关创建执行记录失败: {str(e)}")
        
        # 2. 直接调用LM Studio进行AI推理
        print(f"[{self.name}] [直接路径] 直接连接LM Studio进行任务处理...")
        
        lm_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio-local"
        }
        
        # 根据Agent类型生成不同的处理指令
        if "optimize" in self.name.lower():
            prompt = f"作为需求优化专家，请分析并改进以下PRD需求: {data}"
        elif "prototype" in self.name.lower():
            prompt = f"作为原型设计专家，请为以下需求创建快速原型: {data}"
        elif "split" in self.name.lower():
            prompt = f"作为技术拆分专家，请将以下需求拆分为具体任务: {data}"
        else:
            prompt = f"请处理以下任务: {data}"
        
        lm_data = {
            "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        
        # 直接连接LM Studio，绕过APISIX网关
        result = f"{self.name}处理结果"
        try:
            response = requests.post(
                f"{self.lm_studio_url}/chat/completions",
                headers=lm_headers,
                data=json.dumps(lm_data)
            )
            
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                print(f"[{self.name}] [直接路径] LM Studio推理完成")
            else:
                print(f"[{self.name}] [降级] LM Studio调用失败，使用默认响应")
        except Exception:
            print(f"[{self.name}] [降级] LM Studio通信异常，使用默认响应")
        
        # 3. 更新执行结果到网关
        try:
            if 'execution_id' in locals():
                update_data = {
                    "execution_id": execution_id,
                    "status": "completed",
                    "result": result[:100] + "..." if len(result) > 100 else result
                }
                
                requests.put(
                    f"{self.gateway_url}/api/agno/agent/execution/{execution_id}",
                    headers=headers,
                    data=json.dumps(update_data)
                )
                print(f"[{self.name}] [网关路径] 执行结果已通过网关更新")
        except Exception:
            pass
        
        return {"result": result, "agent": self.name}

# 创建工作流 - 集成APISIX网关配置
def create_enhanced_workflow():
    print("=== 创建条件路由工作流 (APISIX网关架构) ===")
    print(f"- 网关路径: 通过APISIX网关管理工作流状态和任务记录")
    print(f"- 优化路径: 直接访问LM Studio进行AI推理")
    print(f"========================================")
    
    # 尝试从APISIX网关获取工作流配置
    workflow_config = {}
    try:
        print("[网关路径] 尝试从APISIX网关获取工作流配置...")
        response = requests.get(f"{GATEWAY_URL}/api/agno/workflow/config")
        
        if response.status_code == 200:
            workflow_config = response.json()
            print(f"[网关路径] 工作流配置已从网关加载: {workflow_config.get('workflow_name', '默认工作流')}")
    except Exception as e:
        print(f"[降级] 网关获取配置失败，使用默认配置: {str(e)}")
    
    # 创建网关感知的Agent实例
    evaluation_agent = GatewayAwareAgent(name="evaluation_agent")
    quick_prototype_agent = GatewayAwareAgent(name="quick_prototype_agent")
    tech_split_agent = GatewayAwareAgent(name="tech_split_agent")
    req_optimize_agent = GatewayAwareAgent(name="req_optimize_agent")
    
    # 创建工作流
    workflow = Workflow(name=workflow_config.get('workflow_name', "PRD可行性评估流程"))
    
    # 添加评估步骤
    workflow.add_step(Step(agent=evaluation_agent, name="需求评估"))
    
    # 添加条件路由 - 集成APISIX网关路由逻辑
    workflow.add_conditional_edges(
        source="需求评估",
        condition=route_by_feasibility,
        targets=["quick_prototype_agent", "tech_split_agent", "req_optimize_agent"]
    )
    
    return workflow

# 执行增强的工作流
def run_enhanced_workflow(prd_path):
    print(f"\n=== 执行PRD可行性评估流程 (APISIX网关架构) ===\n")
    
    # 创建工作流
    workflow = create_enhanced_workflow()
    
    # 准备输入数据
    input_data = {
        "prd_path": prd_path,
        "workflow_id": f"wf_{str(uuid.uuid4())[:8]}",
        "timestamp": "auto"
    }
    
    # 通过APISIX网关记录工作流启动
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{GATEWAY_URL}/api/agno/workflow/start",
            headers=headers,
            data=json.dumps(input_data)
        )
        
        if response.status_code == 200:
            workflow_id = response.json().get("workflow_id")
            input_data["workflow_id"] = workflow_id
            print(f"[网关路径] 工作流已通过网关注册并启动: {workflow_id}")
    except Exception as e:
        print(f"[降级] 网关启动工作流失败: {str(e)}")
    
    # 执行工作流
    print("\n[执行] 开始工作流处理...")
    result = workflow.run(input_data=input_data)
    
    # 更新工作流完成状态
    try:
        if 'workflow_id' in input_data:
            update_data = {
                "workflow_id": input_data["workflow_id"],
                "status": "completed",
                "result": "工作流执行成功"
            }
            
            requests.put(
                f"{GATEWAY_URL}/api/agno/workflow/complete",
                headers=headers,
                data=json.dumps(update_data)
            )
            print(f"[网关路径] 工作流完成状态已通过网关更新")
    except Exception:
        pass
    
    print(f"\n=== 工作流执行完成 ===\n")
    return result

# 执行工作流示例
result = run_enhanced_workflow(prd_path="D:/product_prd_v1.pdf")
```

### 4.4 并行执行模式示例

并行执行模式在APISIX网关架构下进行了优化，所有任务管理、状态跟踪和资源调度通过APISIX网关进行，而实际的AI处理和网页爬取操作则根据需求灵活选择通信路径，保证高效执行。

```python
import requests
import json
import uuid
import time

# 全局配置 - 遵循APISIX网关架构
GATEWAY_URL = "http://127.0.0.1:8080"  # APISIX独立通信层
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"  # LM Studio直接访问

# 创建支持网关通信的增强版爬虫Agent工厂函数
def create_crawler_agent(competitor_name):
    """创建支持APISIX网关通信的爬虫Agent"""
    class GatewayCrawlerAgent:
        def __init__(self, name, competitor):
            self.name = name
            self.competitor = competitor
            self.gateway_url = GATEWAY_URL
            self.lm_studio_url = LM_STUDIO_URL
            self.tools = [WebsiteCrawlTool(), ReviewExtractTool()]
        
        def execute(self, data=None):
            # 1. 生成唯一执行ID并通过APISIX网关注册任务
            execution_id = f"crawler_{competitor_name}_{str(uuid.uuid4())[:8]}"
            url = data.get("url", f"https://竞品{competitor_name}.com")
            print(f"[{self.name}] [网关路径] 通过APISIX网关注册爬取任务: {execution_id}")
            
            # 准备网关请求数据
            gateway_data = {
                "execution_id": execution_id,
                "agent_name": self.name,
                "competitor": self.competitor,
                "target_url": url,
                "status": "started",
                "timestamp": time.time()
            }
            
            # 通过APISIX网关注册任务
            try:
                headers = {"Content-Type": "application/json"}
                response = requests.post(
                    f"{self.gateway_url}/api/agno/crawler/task",
                    headers=headers,
                    data=json.dumps(gateway_data)
                )
                
                if response.status_code == 200:
                    print(f"[{self.name}] [网关路径] 任务注册成功: {execution_id}")
                else:
                    print(f"[{self.name}] [网关警告] 任务注册响应状态: {response.status_code}")
            except Exception as e:
                print(f"[{self.name}] [降级] 网关注册失败，继续本地执行: {str(e)}")
            
            # 2. 执行网页爬取 (模拟)
            print(f"[{self.name}] 开始爬取{self.competitor}网站的用户评论")
            
            # 网页爬取操作
            # 注意：实际爬取会使用self.tools中的工具
            
            # 3. 对爬取结果进行AI分析 - 直接调用LM Studio
            print(f"[{self.name}] [直接路径] 需要AI分析，直接调用LM Studio处理评论数据")
            
            try:
                lm_headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer lm-studio-local"
                }
                
                prompt = f"分析{self.competitor}网站的用户评论数据，提取关键洞察：\n"
                prompt += "1. 用户满意度评分分布\n"
                prompt += "2. 主要优点和缺点\n"
                prompt += "3. 产品功能反馈\n"
                prompt += "4. 价格敏感性分析\n"
                prompt += "5. 竞品对比（如有提及）\n"
                
                lm_data = {
                    "model": "lmstudio-community/Qwen-14B-Chat-GGUF",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1500
                }
                
                # 直接连接LM Studio，绕过APISIX网关
                response = requests.post(
                    f"{self.lm_studio_url}/chat/completions",
                    headers=lm_headers,
                    data=json.dumps(lm_data)
                )
                
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"]
                    print(f"[{self.name}] [直接路径] LM Studio评论分析完成")
                else:
                    result = f"[{self.name}] 分析结果: 无法分析的评论数据"
                    print(f"[{self.name}] [降级] LM Studio分析失败，使用默认响应")
            except Exception as e:
                result = f"[{self.name}] 分析结果: 通信失败"
                print(f"[{self.name}] [降级] 无法连接LM Studio: {str(e)}")
            
            # 4. 通过APISIX网关更新任务状态和结果
            try:
                update_data = {
                    "execution_id": execution_id,
                    "status": "completed",
                    "result": result[:100] + "..." if len(result) > 100 else result,
                    "timestamp": time.time()
                }
                
                requests.put(
                    f"{self.gateway_url}/api/agno/crawler/task/{execution_id}",
                    headers=headers,
                    data=json.dumps(update_data)
                )
                print(f"[{self.name}] [网关路径] 执行结果已通过网关更新")
                
                # 5. 存储评论数据到PostgreSQL数据库（通过网关）
                store_data = {
                    "execution_id": execution_id,
                    "competitor": self.competitor,
                    "raw_data": "采集到的原始评论数据...",
                    "analysis_result": result
                }
                
                store_response = requests.post(
                    f"{self.gateway_url}/api/postgres/competitor_reviews",
                    headers=headers,
                    data=json.dumps(store_data)
                )
                
                if store_response.status_code == 200:
                    print(f"[{self.name}] [网关路径] 评论数据已通过网关存储到PostgreSQL")
            except Exception:
                # 降级处理：网关操作失败不影响主要功能
                pass
            
            return {"result": result, "competitor": self.competitor, "agent": self.name}
    
    return GatewayCrawlerAgent(
        name=f"爬虫Agent-{competitor_name}",
        competitor=competitor_name
    )

# 创建支持网关的并行执行步骤
def create_gateway_parallel_step(competitors):
    """创建支持APISIX网关的并行执行步骤"""
    print("[网关路径] 创建竞品分析并行步骤，通过APISIX网关分配资源...")
    
    # 1. 通过APISIX网关获取并行任务配置
    parallel_config = {}
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{GATEWAY_URL}/api/agno/workflow/parallel-resources",
            headers=headers,
            data=json.dumps({
                "task_count": len(competitors), 
                "operation_type": "competitor_analysis"
            })
        )
        
        if response.status_code == 200:
            parallel_config = response.json()
            print(f"[网关路径] 已从网关获取并行配置: 最大并行度={parallel_config.get('max_parallel', 'unknown')}")
    except Exception as e:
        print(f"[降级] 网关获取配置失败，使用默认并行度: {str(e)}")
    
    # 2. 创建爬虫Agent步骤列表
    steps = []
    for competitor in competitors:
        agent = create_crawler_agent(competitor)
        url = f"https://竞品{competitor}.com"
        steps.append(Step(agent=agent, name=f"爬取竞品{competitor}", input={"url": url}))
    
    # 3. 记录并行任务信息到网关
    try:
        task_info = [
            {"task_id": f"task_{str(uuid.uuid4())[:8]}", 
             "agent_name": step.agent.name, 
             "competitor": step.agent.competitor} 
            for step in steps
        ]
        
        requests.post(
            f"{GATEWAY_URL}/api/agno/workflow/parallel-tasks",
            headers=headers,
            data=json.dumps({"tasks": task_info, "workflow_id": f"wf_{str(uuid.uuid4())[:8]}"})
        )
        print(f"[网关路径] 并行任务信息已通过网关记录: {len(steps)}个任务")
    except Exception:
        pass
    
    # 4. 返回并行步骤
    return ParallelStep(
        name="竞品信息采集",
        steps=steps,
        max_parallel=parallel_config.get('max_parallel', 3)  # 从网关获取的最大并行度
    )

# 执行竞品分析并行工作流
def run_competitor_analysis():
    """执行支持APISIX网关的竞品分析并行工作流"""
    print("=== 创建竞品分析工作流 (APISIX网关架构) ===")
    print(f"- 网关路径: 通过APISIX网关管理任务注册、状态跟踪和资源分配")
    print(f"- 优化路径: 直接访问LM Studio进行评论数据分析")
    print(f"- 网关路径: 通过APISIX网关将结果存储到PostgreSQL数据库")
    print(f"=======================================")
    
    # 1. 通过APISIX网关检查系统状态
    try:
        print("[网关路径] 检查系统资源和爬虫可用性...")
        response = requests.get(f"{GATEWAY_URL}/api/agno/system/health")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"[网关路径] 系统状态: {health_data.get('status', 'unknown')}")
            
            # 检查爬虫资源可用性
            if 'crawler_resources' in health_data:
                available_crawlers = health_data['crawler_resources'].get('available', 0)
                print(f"[网关路径] 可用爬虫资源: {available_crawlers}")
    except Exception as e:
        print(f"[降级] 网关健康检查失败: {str(e)}")
    
    # 2. 创建并行工作流
    competitors = ["A", "B", "C"]
    print(f"\n[执行] 开始分析{len(competitors)}个竞品网站")
    
    # 创建并行步骤
    parallel_crawl = create_gateway_parallel_step(competitors)
    
    # 创建工作流并添加并行步骤
    workflow = Workflow(name="竞品分析并行工作流")
    workflow.workflow_id = f"competitor_wf_{str(uuid.uuid4())[:8]}"
    workflow.add_step(parallel_crawl)
    
    # 3. 通过APISIX网关注册工作流
    try:
        headers = {"Content-Type": "application/json"}
        requests.post(
            f"{GATEWAY_URL}/api/agno/workflow/register",
            headers=headers,
            data=json.dumps({
                "workflow_id": workflow.workflow_id,
                "name": "竞品分析并行工作流",
                "type": "parallel",
                "competitor_count": len(competitors)
            })
        )
        print(f"[网关路径] 工作流已通过网关注册: {workflow.workflow_id}")
    except Exception:
        pass
    
    # 4. 执行工作流
    print("\n[执行] 开始并行爬取和分析...")
    result = workflow.run()
    
    # 5. 通过APISIX网关更新工作流状态
    try:
        requests.put(
            f"{GATEWAY_URL}/api/agno/workflow/status/{workflow.workflow_id}",
            headers=headers,
            data=json.dumps({
                "status": "completed",
                "result_count": len(result) if isinstance(result, list) else 1
            })
        )
        print(f"[网关路径] 工作流完成状态已通过网关更新")
    except Exception:
        pass
    
    print(f"\n=== 竞品分析并行工作流执行完成 ===\n")
    return result

# 执行竞品分析
result = run_competitor_analysis()

# 创建完整工作流
workflow = Workflow(name="竞品分析流程")
workflow.add_step(parallel_crawl)
workflow.add_step(Step(agent=analysis_agent, name="数据整合分析"))

# 执行并监控进度
result = workflow.run()
print("爬取进度:", workflow.get_progress("竞品信息采集"))
```

## 五、系统集成与工作流程

### 5.1 完整工作流示例：从视频到应用开发

在新的架构设计中，APISIX网关作为独立的通信层，垂直排列在架构右侧，连接所有业务层组件。上层组件通过APISIX网关访问下层组件（LM Studio除外，保持直接通信以优化性能）。以下是整合APISIX网关后的完整工作流程：

1. **需求收集阶段**
   - 输入：产品演示视频
   - 处理：
     - **网关路径**：通过APISIX网关将视频数据传递给NeuralAgent视觉分析
     - **直接路径**：直接与LM Studio进行多模态理解通信（绕过网关，优化性能）
     - **网关路径**：通过APISIX网关将结果存储到PostgreSQL数据库
   - 输出：结构化PRD文档

2. **可行性评估阶段**
   - 输入：PRD文档
   - 处理：
     - **网关路径**：通过APISIX网关管理BMAD分析师角色的任务注册和状态跟踪
     - **直接路径**：直接调用LM Studio进行深度分析推理
     - **网关路径**：通过APISIX网关执行条件路由决策
   - 输出：可行性报告 + 优化建议

3. **产品规划阶段**
   - 输入：可行性报告
   - 处理：
     - **网关路径**：通过APISIX网关管理经理-员工协作模式的任务分配
     - **直接路径**：各角色Agent直接与LM Studio进行推理通信
     - **网关路径**：通过APISIX网关同步项目状态和资源分配
   - 输出：详细规划 + 原型设计

4. **技术实现阶段**
   - 输入：详细规划
   - 处理：
     - **网关路径**：通过APISIX网关配置和管理并行执行任务
     - **直接路径**：各开发角色直接与LM Studio进行代码生成和技术分析
     - **网关路径**：通过APISIX网关管理任务依赖和资源调度
   - 输出：代码实现

5. **质量保障阶段**
   - 输入：代码实现
   - 处理：
     - **网关路径**：通过APISIX网关分配测试任务和收集测试结果
     - **直接路径**：QA Agent直接与LM Studio进行代码审查和测试用例生成
     - **网关路径**：通过APISIX网关将测试报告存储到数据库
   - 输出：测试报告

6. **部署交付阶段**
   - 输入：测试通过的代码
   - 处理：自动化部署工具
   - 输出：可运行的应用

### 5.2 协作模式选择指南

| 场景 | 推荐协作模式 | 优势 | 配置要求 |
|------|------------|------|----------|
| 创意内容生成 | 经理-员工模式 | 任务分解明确，角色分工清晰 | 5+ Agent |
| 需求分析/PRD评审 | 条件路由模式 | 智能分流，提高效率 | 3+ Agent |
| 竞品分析/数据采集 | 并行执行模式 | 大幅提升处理速度 | 硬件性能要求较高 |

## 六、故障排查与优化

在整合APISIX网关作为独立通信层的架构中，需要特别关注网关通信路径和LM Studio直接通信路径的问题排查与优化。以下是针对新架构的故障排查和优化建议：

### 6.1 常见问题及解决方案

1. **LM Studio连接失败（直接通信路径）**
   - 检查服务是否启动
   - 验证端口1234是否被占用
   - 确认API兼容性设置为OpenAI v1
   - 检查防火墙是否允许直接访问LM Studio端口

2. **APISIX网关通信故障（网关通信路径）**
   - 检查APISIX服务状态：`curl http://localhost:9080/apisix/admin/routes -H "X-API-KEY: your_api_key"`
   - 验证网关路由配置是否正确
   - 检查网关日志以识别具体错误：`tail -f /usr/local/apisix/logs/error.log`
   - 确认网关配置中的下游服务地址正确

3. **网关降级机制不触发**
   - 检查代码中的异常捕获逻辑是否完整
   - 验证超时设置是否合理（建议设置10-15秒）
   - 添加更详细的网关故障日志记录

4. **视觉识别不准确**
   - 调整YOLOv8置信度阈值
   - 更新Tesseract语言包
   - 尝试多种视觉路线协同工作

5. **任务执行超时**
   - 增加max_tokens设置
   - 调整temperature参数
   - 优化并行任务数量
   - 检查网关连接池和超时设置

### 6.2 性能优化建议

1. **模型优化**
   - 选择合适的模型大小（平衡性能与速度）
   - 量化模型（INT8/INT4）减少内存占用

2. **通信路径优化**
   - **网关路径优化**：
     - 配置APISIX连接池参数：增加worker_connections和keepalive连接数
     - 启用网关缓存：对频繁访问的配置和状态数据实施缓存
     - 实现请求合并：对短时间内的相似请求进行合并处理
   - **直接路径优化**：
     - 保持LM Studio直接通信以确保AI推理性能
     - 实现LM Studio请求批处理以提高吞吐量

3. **并行度调整**
   - 根据CPU核心数动态调整并行任务数
   - 实现任务优先级队列
   - 通过APISIX网关动态分配并行资源，避免资源竞争

4. **缓存机制**
   - 缓存常用查询结果
   - 实现模型响应缓存
   - 通过APISIX网关实现分布式缓存一致性

## 七、总结与展望

本方案通过整合NeuralAgent、Agno多智能体框架、BMAD-METHOD开发方法论和LM Studio本地模型服务，构建了一个功能完整、高度灵活的本地化AI智能体系统。特别值得强调的是，我们创新性地引入了APISIX网关作为独立的通信层，垂直排列在架构右侧，连接所有业务层组件，实现了以下架构优势：

1. **分层通信架构**：上层组件通过APISIX网关访问下层组件，实现了通信的集中管理和监控
2. **性能优化路径**：保留了LM Studio的直接通信路径，确保AI推理性能最大化
3. **高可用性保障**：实现了完善的网关降级机制，即使网关通信失败也能保证核心功能可用
4. **资源统一管理**：通过网关实现了任务注册、状态跟踪和资源分配的统一管理

该系统具备多模态视觉理解、人类级操作能力和智能任务执行能力，同时支持多种协作模式以适应不同场景需求，包括经理-员工模式、条件路由模式和并行执行模式。

未来可以进一步探索：
1. 更多视觉模型的集成（如SAM、CLIP等）
2. 更复杂的多智能体协作策略
3. 硬件加速支持（如Intel Arc/AMD GPUs）
4. 跨平台支持（Linux/macOS）
5. 低资源环境优化
6. APISIX网关的高级特性应用（如A/B测试、流量镜像等）
7. LM Studio与网关的自适应通信策略（根据负载动态切换）

通过不断迭代和完善，该系统有望成为企业和个人用户的强大AI助手，在离线环境下提供接近在线服务的智能体验，同时保持通信架构的清晰性、可维护性和高性能。