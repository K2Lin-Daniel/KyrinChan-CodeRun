# 🌟 仿星极光引擎 魔法使的理科通用计算沙盒 ✨

诶嘿！欢迎来到这个专门为凯琳酱我准备的**理科通用计算沙盒**！(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧
原本这里只是为了做点简单的数学运算诞生的，但是现在它已经进化啦！无论是数学、物理、化学还是天文，只要是理科相关的魔法（Python 代码），这里通通都能帮你安全地运行哦！

内置了超多厉害的魔法书（依赖库），比如 `NumPy`、`SymPy`、`SciPy`、`pymatgen` 等等，绝对能满足各种复杂的计算需求！

## 🛡️ 绝对防御结界 (五重安全防护)

为了防止坏蛋代码把我们的服务器弄坏，凯琳酱我可是设下了**五重防御结界**呢！(๑•̀ㅂ•́)و✧

1. **Docker 结界限制**: 限制了最大进程数 (`pids_limit`)、内存、CPU，还丢弃了所有的特权 (`cap_drop`)，而且根文件系统是只读的哦！坏蛋休想篡改文件！
2. **非特权小精灵 (Non-Root)**: 服务是在一个没有特权的小精灵用户 (`sandboxuser`) 下运行的，非常乖巧安全！
3. **Linux 资源封印**: 使用了 Python 的 `resource` 魔法，限制了每次执行的虚拟内存 (`RLIMIT_AS`)、CPU 时间 (`RLIMIT_CPU`) 和子进程 (`RLIMIT_NPROC`)，绝对不会出现内存耗尽或者 fork 炸弹的！
4. **子进程次元隔离**: 所有的未知代码都会被丢进一个独立的子进程里执行，即使它坏掉了，也不会影响到 API 本体的运行哦！
5. **断网大阵 (Network Isolation)**: 默认情况下，容器是被关在内部网络里的 (`internal: true`)，完全切断了与外部世界的联系。想要连接外网的话，需要亲自解开封印（修改 `docker-compose.yml`）。

## 🚀 召唤仪式 (Quick Start)

### 仪式准备
- Docker
- Docker Compose

### 开始召唤

把这些文件下载到你的魔法阵（目录）里，然后念出以下咒语：

```bash
cd python-sandbox
docker-compose up -d --build
```

铛铛！API 就会在 `http://localhost:8000` 降临啦！🎉

---

## 📖 魔法契约 (API Documentation)

### ⚡ 释放魔法 (Execute Code)

把你要执行的 Python 咒语（代码）交给我吧！

- **魔法阵 (Endpoint)**: `/execute`
- **属性 (Method)**: `POST`
- **格式 (Content-Type)**: `application/json`

#### 咒语内容 (Request Body)

| 字段 | 类型 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `code` | `string` | **必须哦** | 要执行的 Python 咒语。 |
| `timeout` | `integer` | `5` | 最长允许的咏唱时间（CPU 秒数）。 |
| `memory_limit_mb` | `integer`| `256` | 最多可以消耗的魔力（虚拟内存，单位 MB）。 |
| `files` | `object` | `{}` | 输入文件字典。键为文件名，值为 Base64 编码的文件内容。代码可以直接用相对路径读取它们哦！ |

**举个栗子 (Example Request):**

```json
{
  "code": "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df)\nimport matplotlib.pyplot as plt\nplt.plot(df['age'])\n# 即使不写 plt.savefig，画出的图也会被自动捕获并返回哦！",
  "timeout": 5,
  "memory_limit_mb": 256,
  "files": {
    "data.csv": "bmFtZSxhZ2UKQWxpY2UsMjUKQm9iLDMwCg=="
  }
}
```

#### 宇宙的真理 (Response)

| 字段 | 类型 | 描述 |
| :--- | :--- | :--- |
| `stdout` | `string` | 魔法成功释放后的反馈（标准输出）。 |
| `stderr` | `string` | 魔法失败时候的警告（标准错误/异常）。 |
| `exit_code` | `integer`| 退出状态码（0 代表大成功！非 0 就是出错了或者超时啦。`137` 通常意味着超时被我无情抹杀了哦）。 |
| `images` | `object` | 生成的所有图像文件字典。键为文件名，值为 Base64 编码的 Image Data URL（如 `data:image/png;base64,...`）。 |

**大成功！(Success):**

```json
{
  "stdout": "    name  age\n0  Alice   25\n1    Bob   30\n",
  "stderr": "",
  "exit_code": 0,
  "images": {
    "plot.png": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
  }
}
```

**超时失败... (Timeout):**

```json
{
  "stdout": "",
  "stderr": "Warning: Failed to set resource limits...\nExecution timed out (Wall-clock limit reached).",
  "exit_code": 137,
  "images": {}
}
```

### 💓 心跳测试 (Health Check)

看看我还在不在～

- **魔法阵 (Endpoint)**: `/health`
- **属性 (Method)**: `GET`

#### 响应

```json
{
  "status": "ok"
}
```

---

## ⚙️ 进阶设定 (Configuration)

### 🌐 解除断网封印 (Enable Internet Access)
为了防止数据泄露或者下载奇怪的东西，默认是不能联网的。如果真的想要它联网的话，请修改 `docker-compose.yml` 文件：

```yaml
networks:
  sandbox_net:
    internal: false # 把这里改成 false 就可以啦
```

然后重新启动一下服务：
```bash
docker-compose down
docker-compose up -d
```

---

## 🤖 LLM 对接与文件映射最佳实践 (LLM Integration Guide)

为了让 LLM 在生成代码、处理数据和渲染图表时与沙盒实现最安全、直观的配合，推荐采用以下双向映射与渲染模式：

### 📥 1. 输入文件映射 (Input Files Mapping)
- **数据源准备**：将用户上传的文件（如 `data.csv`、`data.xlsx`）在后端转换为 Base64 编码，放入 API 请求的 `files` 字典中。
- **提示词引导 (Prompt Guide)**：
  > “用户上传了一个名为 `[文件名]` 的文件。你可以直接在 Python 代码中通过相对路径 `'[文件名]'` 读取它并进行分析，无需自行生成或模拟数据。”
- **LLM 代码生成示例**：
  ```python
  import pandas as pd
  # 直接以相对路径读取传入的 CSV
  df = pd.read_csv("data.csv")
  ```

### 📤 2. 输出图表映射与前端渲染 (Output Plots Mapping & Frontend Rendering)
- **显式保存命名**：为了让前端能精确地把图表渲染到 LLM 文本中的对应上下文中，推荐在提示词中约束 LLM **显式对图片进行命名保存**。
- **提示词引导 (Prompt Guide)**：
  > “如果你需要绘制图表展示结果，请显式使用 `plt.savefig('自定义英文名称.png')`（或 `.svg`）保存它，并在你的 Markdown 回复中使用标准图片标签引用它，例如：`![销售额趋势](sales_trends.png)`。你可以根据内容自定义图片名称，建议使用 SVG 格式获得无限清晰度。”
- **前端渲染流 (Frontend Rendering Process)**：
  1. 后端调用 `/execute` 拿到 `images` 字典。
  2. 前端解析 LLM 的 Markdown 文本时，若解析到图片标签 `![alt](filename.png)`，则检查 `images` 字典中是否存在键为 `filename.png` 的数据。
  3. 若存在，将图片标签的 `src` 替换为对应的 Base64 Data URL：`<img src="data:image/png;base64,..." alt="alt">` 即可直接展示。
- **自动捕获兜底**：如果 LLM 未指定文件名直接画图，沙盒会默认将其保存为 `plot.png` 并高精度（200 DPI）渲染。前端可自动将 Markdown 未引用的多余图片追加展示在回复底部。
