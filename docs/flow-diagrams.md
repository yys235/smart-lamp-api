# Smart Lamp 业务流程图

> **版本**: 1.0
> **日期**: 2026-03-19
> **作者**: Business Analyst

---

## 目录

1. [系统架构](#1-系统架构)
2. [设备发现流程](#2-设备发现流程)
3. [灯泡控制流程](#3-灯泡控制流程)
4. [事件处理流程](#4-事件处理流程)
5. [错误处理流程](#5-错误处理流程)

---

## 1. 系统架构

```mermaid
graph TB
    subgraph "外部系统"
        Client[API 客户端]
        Gateway[智能灯泡网关]
    end

    subgraph "Smart Lamp API"
        API[FastAPI 路由层]
        LampSvc[LampService]
        GatewaySvc[GatewayService]
        UDP[UdpClient]
        TCP[TcpClient]
        EventMgr[EventManager]
        DB[(SQLite 数据库)]
    end

    Client -->|HTTP JSON| API
    API --> LampSvc
    LampSvc --> GatewaySvc

    GatewaySvc <-->|UDP 广播| UDP
    UDP <-->|41328| Gateway

    GatewaySvc <-->|TCP 连接| TCP
    TCP <-->|41330| Gateway

    GatewaySvc --> EventMgr
    LampSvc --> DB

    style Gateway fill:#f9f,stroke:#333,stroke-width:2px
    style Client fill:#bbf,stroke:#333,stroke-width:2px
```

---

## 2. 设备发现流程

### 2.1 启动时自动发现

```mermaid
sequenceDiagram
    participant API as FastAPI 服务
    participant GatewaySvc as GatewayService
    participant UDP as UdpClient
    participant Gateway as 网关设备

    API->>GatewaySvc: start()
    GatewaySvc->>UDP: start()
    UDP->>UDP: 绑定端口 41328
    UDP->>UDP: 启动监听循环

    Note over Gateway: 网关发送 UDP 广播
    Gateway->>UDP: UDP 广播包
    UDP->>UDP: 解析 gateway_id, IP

    alt 首次发现
        UDP->>GatewaySvc: on_gateway_discovered()
        GatewaySvc->>GatewaySvc: 记录网关信息
        GatewaySvc->>TCP: get_lamps()
        TCP->>Gateway: TCP 连接 (41330)
        Gateway->>TCP: 返回灯泡列表
        TCP->>GatewaySvc: 返回 Lamp[]

        GatewaySvc->>GatewaySvc: _lamps = lamps
        GatewaySvc->>EventMgr: publish(gateway_connected)
    end
```

### 2.2 主动发现

```mermaid
sequenceDiagram
    participant Client as API 客户端
    participant API as FastAPI
    participant UDP as UdpClient
    participant Gateway as 网关设备

    Client->>API: GET /api/v1/gateway/discover
    API->>UDP: discover_gateway(timeout=5s)

    UDP->>UDP: 创建 discovery_event
    UDP->>Gateway: 发送发现广播
    Note over UDP: 等待响应...

    alt 在超时前收到响应
        Gateway->>UDP: UDP 广播响应
        UDP->>UDP: 解析 gateway 信息
        UDP->>UDP: discovery_event.set()
        UDP->>API: 返回 {gateway_ip, gateway_id}
        API->>Client: 200 OK + 网关信息
    else 超时
        UDP->>API: TimeoutError
        API->>Client: 500 Gateway discovery timeout
    end
```

---

## 3. 灯泡控制流程

### 3.1 开启单个灯泡

```mermaid
sequenceDiagram
    participant Client as API 客户端
    participant API as /lamps/{id}/on
    participant LampSvc as LampService
    participant GatewaySvc as GatewayService
    participant TCP as TcpClient
    participant Gateway as 网关设备

    Client->>API: POST /lamps/1680764563/on<br/>{red:255, green:100, blue:50, intensity:200}
    API->>API: 验证 API Key
    API->>API: 验证参数范围
    API->>LampSvc: turn_on(device_id, request)

    LampSvc->>GatewaySvc: get_lamps()
    GatewaySvc->>TCP: get_lamps(gateway_ip, gateway_id)
    TCP->>Gateway: TCP 请求 (获取灯泡)
    Gateway->>TCP: 灯泡列表响应
    TCP->>GatewaySvc: Lamp[]
    GatewaySvc->>LampSvc: Lamp[]

    LampSvc->>LampSvc: 找到目标 lamp
    LampSvc->>LampSvc: 更新 lamp RGBI 值
    LampSvc->>GatewaySvc: update_lamps(lamps)

    GatewaySvc->>TCP: update_lamps(gateway_ip, lamps)
    TCP->>Gateway: TCP 请求 (更新灯泡)
    Gateway->>TCP: 确认响应
    TCP->>GatewaySvc: success = true

    GatewaySvc->>GatewaySvc: 等待 0.5 秒
    GatewaySvc->>GatewaySvc: 刷新灯泡状态验证

    alt 状态未更新
        GatewaySvc->>TCP: update_lamps() (重试)
        TCP->>Gateway: 重试请求
    end

    GatewaySvc->>LampSvc: 返回 true
    LampSvc->>LampSvc: get_lamp(device_id)
    LampSvc->>API: Lamp
    API->>Client: 200 OK + lamp 数据
```

### 3.2 批量控制流程

```mermaid
flowchart TD
    Start([开始: /lamps/all/on]) --> Validate{验证参数}
    Validate -->|无效| Error400[400 Bad Request]
    Validate -->|有效| GetLamps[获取当前所有灯泡]

    GetLamps --> CheckConn{网关已连接?}
    CheckConn -->|否| Error503[503 Service Unavailable]
    CheckConn -->|是| UpdateAll[更新所有灯泡 RGBI]

    UpdateAll --> SendTCP[发送 TCP 更新请求]
    SendTCP --> TCPResp{TCP 响应成功?}

    TCPResp -->|否| Error500[500 Internal Error]
    TCPResp -->|是| WaitVerify[等待 0.5 秒]

    WaitVerify --> Refresh[刷新灯泡状态]
    Refresh --> Verify{状态已更新?}

    Verify -->|否| Retry[重试一次]
    Retry --> SendTCP

    Verify -->|是| LogDB[记录操作日志]
    LogDB --> Success[200 OK + 所有灯泡状态]

    style Error400 fill:#f99,stroke:#333
    style Error503 fill:#f99,stroke:#333
    style Error500 fill:#f99,stroke:#333
    style Success fill:#9f9,stroke:#333
```

---

## 4. 事件处理流程

```mermaid
sequenceDiagram
    participant UDP as UdpClient
    participant EventMgr as EventManager
    participant Handler1 as 网关连接处理器
    participant Handler2 as 状态变更处理器
    participant DB as 数据库

    Note over UDP: 接收 UDP 广播

    UDP->>UDP: 解析广播包
    UDP->>UDP: 检测设备变化

    alt 首次发现网关
        UDP->>EventMgr: publish(gateway_connected)
        EventMgr->>EventMgr: 加入事件队列

        EventMgr->>Handler1: dispatch(gateway_connected)
        Handler1->>DB: 记录连接日志
    end

    alt 设备状态变化
        UDP->>EventMgr: publish(lamp_state_changed)
        EventMgr->>Handler2: dispatch(lamp_state_changed)
        Handler2->>DB: 记录状态变更
    end

    alt 设备移除
        UDP->>EventMgr: publish(lamp_removed)
        EventMgr->>Handler2: dispatch(lamp_removed)
        Handler2->>DB: 更新设备状态
    end
```

### 4.1 事件类型与处理

```mermaid
graph LR
    subgraph "事件源"
        UDP[UDP 广播]
        TCP[TCP 响应]
        API[API 操作]
    end

    subgraph "EventManager"
        Queue[事件队列]
        Dispatch[事件分发器]
    end

    subgraph "事件处理器"
        H1[网关连接处理]
        H2[状态变更处理]
        H3[错误处理]
        H4[日志记录]
    end

    UDP -->|gateway_connected| Queue
    UDP -->|lamp_state_changed| Queue
    TCP -->|error| Queue
    API -->|operation| Queue

    Queue --> Dispatch
    Dispatch --> H1
    Dispatch --> H2
    Dispatch --> H3
    Dispatch --> H4

    H1 --> DB[(数据库)]
    H2 --> DB
    H4 --> DB
```

---

## 5. 错误处理流程

### 5.1 完整错误处理树

```mermaid
flowchart TD
    Start([API 请求]) --> Auth{API Key 验证}

    Auth -->|失败| Err401[401 Unauthorized]
    Auth -->|成功| Params{参数验证}

    Params -->|失败| Err400[400 Bad Request]
    Params -->|成功| Gateway{网关连接?}

    Gateway -->|否| Err503[503 Gateway Not Connected]
    Gateway -->|是| Operation[执行操作]

    Operation --> TCP{TCP 通信}
    TCP -->|超时| Retry{重试次数 < 3?}
    TCP -->|失败| LogErr[记录错误日志]
    TCP -->|成功| Verify{状态验证}

    Retry -->|是| WaitTCP[等待 1 秒]
    Retry -->|否| Err500[500 Internal Error]

    WaitTCP --> TCP

    Verify -->|失败| Retry
    Verify -->|成功| LogDB[记录操作日志]
    LogDB --> Success[200 OK]

    LogErr --> Err500

    style Err401 fill:#f99,stroke:#333
    style Err400 fill:#f99,stroke:#333
    style Err503 fill:#f99,stroke:#333
    style Err500 fill:#f99,stroke:#333
    style Success fill:#9f9,stroke:#333
```

### 5.2 TCP 通信错误处理

```mermaid
sequenceDiagram
    participant Service as GatewayService
    participant TCP as TcpClient
    participant Gateway as 网关设备
    participant Logger as 日志系统

    Service->>TCP: update_lamps(lamps)

    TCP->>Gateway: 建立 TCP 连接

    alt 连接超时 (5秒)
        TCP->>Logger: error("连接超时")
        TCP->>Service: 返回 False
        Service->>Logger: warning("控制失败")
    end

    alt 连接成功
        TCP->>Gateway: 发送更新命令

        alt 发送失败
            TCP->>Logger: error("发送失败")
            TCP->>Service: 返回 False
        end

        alt 响应超时 (5秒)
            TCP->>Logger: error("响应超时")
            TCP->>Service: 返回 False
        end

        alt 正常响应
            Gateway->>TCP: 返回数据
            TCP->>TCP: 解析响应
            TCP->>Service: 返回 True

            Service->>Service: 等待 0.5 秒验证
            Service->>TCP: get_lamps() (验证)

            alt 验证失败
                Service->>TCP: update_lamps() (重试)
            end
        end
    end
```

### 5.3 错误码映射

| 错误场景 | HTTP 状态码 | 错误消息 | 日志级别 |
|----------|-------------|----------|----------|
| API Key 缺失/无效 | 401 | Unauthorized | WARNING |
| 参数验证失败 | 400 | Invalid parameter: {field} | INFO |
| 网关未连接 | 503 | Gateway not connected | WARNING |
| TCP 连接超时 | 500 | Failed to connect to gateway | ERROR |
| TCP 响应超时 | 500 | Gateway response timeout | ERROR |
| 控制失败 | 500 | Failed to control lamp {id} | ERROR |
| 设备不存在 | 404 | Lamp {id} not found | INFO |

---

## 附录

### A. 状态转换图

```mermaid
stateDiagram-v2
    [*] --> Disconnected: 服务启动
    Disconnected --> Discovering: 开始 UDP 监听
    Discovering --> Connected: 收到网关广播
    Discovering --> Disconnected: 超时无响应

    Connected --> Refreshing: 定时刷新灯泡
    Refreshing --> Connected: 刷新成功

    Connected --> Controlling: 发送控制命令
    Controlling --> Connected: 控制成功
    Controlling --> Connected: 控制失败(重试)

    Connected --> Disconnected: 网关断开
    Disconnected --> [*]: 服务停止
```

### B. 时序说明

| 操作 | 预计耗时 | 说明 |
|------|----------|------|
| UDP 网关发现 | < 30 秒 | 首次发现可能需要等待 |
| TCP 获取灯泡 | < 1 秒 | 正常网络条件下 |
| TCP 更新灯泡 | < 1 秒 | 单次请求 |
| 状态验证等待 | 0.5 秒 | 固定延迟 |
| 重试间隔 | 1 秒 | 可配置 |

### C. 相关文档

- [需求规格说明书](./requirements.md)
- [API 契约文档](./api-contract.md)
- [数据字典](./data-dictionary.md)
- [协议文档](./protocol.md)

---

*文档变更历史*

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-03-19 | BA | 初始版本 |
