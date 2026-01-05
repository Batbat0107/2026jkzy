# 泛光小球聊天机器人（p5.js）

这是一个使用 p5.js 实现的页面式聊天机器人：
- 形式：带有发光效果的球形机器人
- 口型：通过文字驱动（根据字符生成口型时间线）
- 字幕：文字以气泡形式显示在机器人头顶
- 消息来源：可配置为 JSONBin（或任意返回数组 JSON 的 URL）

快速开始

1. 本地运行（开发测试）：
   - 在 `web_chatbot` 目录下运行 `npm install` 然后 `npm start`（会使用 `serve` 提供静态服务器），访问 `http://localhost:5000`。
2. 把整个 `web_chatbot` 文件夹推到一个 Git 仓库（或直接上传到 Vercel）。
3. 在页面上填入 JSONBin 的 URL（示例：`https://api.jsonbin.io/v3/b/<BIN_ID>/latest`），或留空使用示例消息。若需要 API Key，可填 `X-Master-Key`。
4. 点击“取一条消息”或按空格键触发。

部署到 Vercel

1. 把 `web_chatbot` 文件夹推到一个 Git 仓库（GitHub/GitLab）。
2. 在 Vercel 仪表盘 -> New Project -> Import Git Repository，选择你的仓库并部署（默认静态站点即可）。
3. 若需要私有 JSONBin Key，可在 Project Settings -> Environment Variables 添加 `BIN_URL` 和 `BIN_KEY`（或任意键名），然后在页面通过 query 参数或前端读取注入的方式使用。为了安全性，建议在部署后用 query 参数（临时）或 serverless 函数代理私密请求。

示例快速链：
`https://your-site.vercel.app/?binUrl=https://api.jsonbin.io/v3/b/<BIN_ID>/latest&apiKey=<KEY>&auto=1`

已上传的示例数据（私有）

- `memory_chat.json` 已上传到 JSONBin（私有）。
  - **Bin ID**：`695b5bd043b1c97be919ec3d`
  - **API（latest）**：`https://api.jsonbin.io/v3/b/695b5bd043b1c97be919ec3d/latest`
  - 访问此 bin 需要在请求头中加入 `X-Master-Key: <YOUR_API_KEY>`（上传时使用了你提供的 key）。

JSON 格式

支持以下几种结构（从响应中自动寻找数组）：
- Array 直接返回数组： `["hi","hello"]` 
- Object 带 `messages` 字段： `{ "messages": ["a","b"] }`

示例（JSONBin v3）：

- URL: `https://api.jsonbin.io/v3/b/<BIN_ID>/latest`
- 若私有，请在请求头加 `X-Master-Key: <YOUR_API_KEY>` 或在页面输入框填写（部署时强烈建议使用 Vercel 的 Environment Variable / Secret）。

快速部署提示：你可以直接把 `binUrl` 和 `apiKey` 放在部署链接的 Query 参数中，例如 `https://your-site.vercel.app/?binUrl=https://api.jsonbin.io/v3/b/<BIN_ID>/latest&apiKey=<KEY>&auto=1` 以便自动播放。
自定义与扩展

- 口型规则在 `script.js` 的 `buildTimelineFromText` 中，可根据需要调整字符到口型的映射与节奏。

文件说明

- `index.html`：页面骨架，包含控制面板与 p5 canvas 容器。
- `script.js`：核心逻辑（p5 绘制、口型时间线、JSON 获取与 UI 联动）。
- `style.css`：样式与气泡字幕样式。
- `vercel.json`：方便在 Vercel 上作为静态站点部署。

已知限制

- 当前演示基于字符驱动口型，无法完美反映真实语音的音素（phoneme）分布；若需要更精确的唇形同步，可接入 TTS 的音素输出或 WebAudio 分析。

部署信息（由自动化部署）

- 已在 Vercel 使用仓库 `Batbat0107/2026jkzy` 的 `web_chatbot` 目录创建项目并部署。
- **部署 URL**：https://2026jkzy-l47ihu6m8-cbbs-projects-bc686e90.vercel.app
- 已添加环境变量：`BIN_KEY`（已设为 Production，内容为你提供的 JSONBin key）。

欢迎修改和 PR。