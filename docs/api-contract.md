# Smart Lamp API 契约文档

> **版本**: 1.0
> **日期**: 2026-03-19
> **Base URL**: `http://localhost:8000/api/v1`

---

## 目录

1. [概述](#1-概述)
2. [通用规范](#2-通用规范)
3. [认证](#3-认证)
4. [API 端点](#4-api-端点)
5. [错误码](#5-错误码)

---

## 1. 概述

本文档定义 Smart Lamp API 的所有 REST 接口规范，包括请求格式、响应格式和错误处理。

### 1.1 基础信息

| 属性 | 值 |
|------|-----|
| 协议 | HTTP/1.1, HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| API 版本 | v1 |

---

## 2. 通用规范

### 2.1 统一响应格式

所有 API 响应遵循统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，0 表示成功 |
| message | string | 响应消息 |
| data | any | 响应数据，可为对象、数组或 null |

### 2.2 认证方式

使用 API Key 进行认证，通过 HTTP Header 传递：

```
X-API-Key: your-api-key
```

### 2.3 请求方法

| 方法 | 用途 |
|------|------|
| GET | 查询资源 |
| POST | 创建资源或执行操作 |

---

## 3. 认证

### 3.1 API Key 配置

在服务端配置环境变量 `API_KEY`，客户端请求时需在 Header 中携带。

**请求示例**:
```http
GET /api/v1/lamps HTTP/1.1
Host: localhost:8000
X-API-Key: your-api-key
```

---

## 4. API 端点

### 4.1 灯泡控制

#### 4.1.1 获取所有灯泡

获取所有已连接灯泡的当前状态。

**请求**:
```http
GET /api/v1/lamps
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "lamps": [
      {
        "device_id": 1680764563,
        "name": "living_room",
        "red": 255,
        "green": 200,
        "blue": 100,
        "intensity": 200
      },
      {
        "device_id": 1680764191,
        "name": "bedroom",
        "red": 255,
        "green": 255,
        "blue": 255,
        "intensity": 255
      }
    ],
    "count": 2
  }
}
```

#### 4.1.2 获取单个灯泡

根据 device_id 获取指定灯泡状态。

**请求**:
```http
GET /api/v1/lamps/{device_id}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| device_id | int | 设备唯一标识，>= 1 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "device_id": 1680764563,
    "name": "living_room",
    "red": 255,
    "green": 200,
    "blue": 100,
    "intensity": 200
  }
}
```

**错误响应** (404):
```json
{
  "detail": "Lamp 1680764563 not found"
}
```

#### 4.1.3 开启单个灯泡

控制指定灯泡开启，并设置 RGB 颜色和亮度。

**请求**:
```http
POST /api/v1/lamps/{device_id}/on
Content-Type: application/json

{
  "red": 255,
  "green": 100,
  "blue": 50,
  "intensity": 200
}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| device_id | int | 设备唯一标识，>= 1 |

**请求体** (所有字段可选):
| 字段 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| red | int | 0-255 | 255 | 红色值 |
| green | int | 0-255 | 255 | 绿色值 |
| blue | int | 0-255 | 255 | 蓝色值 |
| intensity | int | 0-255 | 255 | 亮度 |

**响应示例**:
```json
{
  "code": 0,
  "message": "Lamp turned on",
  "data": {
    "device_id": 1680764563,
    "name": "living_room",
    "red": 255,
    "green": 100,
    "blue": 50,
    "intensity": 200
  }
}
```

#### 4.1.4 关闭单个灯泡

将指定灯泡的亮度设为 0（关闭）。

**请求**:
```http
POST /api/v1/lamps/{device_id}/off
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| device_id | int | 设备唯一标识，>= 1 |

**响应示例**:
```json
{
  "code": 0,
  "message": "Lamp turned off",
  "data": {
    "device_id": 1680764563,
    "name": "living_room",
    "red": 255,
    "green": 100,
    "blue": 50,
    "intensity": 0
  }
}
```

#### 4.1.5 开启全部灯泡

同时开启所有灯泡。

**请求**:
```http
POST /api/v1/lamps/all/on
Content-Type: application/json

{
  "red": 255,
  "green": 255,
  "blue": 255,
  "intensity": 255
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "All lamps turned on",
  "data": {
    "lamps": [
      { "device_id": 1680764563, "red": 255, "green": 255, "blue": 255, "intensity": 255 },
      { "device_id": 1680764191, "red": 255, "green": 255, "blue": 255, "intensity": 255 }
    ],
    "count": 2
  }
}
```

#### 4.1.6 关闭全部灯泡

同时关闭所有灯泡。

**请求**:
```http
POST /api/v1/lamps/all/off
```

**响应示例**:
```json
{
  "code": 0,
  "message": "All lamps turned off",
  "data": {
    "lamps": [
      { "device_id": 1680764563, "intensity": 0 },
      { "device_id": 1680764191, "intensity": 0 }
    ],
    "count": 2
  }
}
```

### 4.2 网关管理

#### 4.2.1 获取网关状态

获取网关连接状态和统计信息。

**请求**:
```http
GET /api/v1/gateway
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "connected": true,
    "gateway_ip": "192.168.1.100",
    "gateway_id": 1234567890,
    "lamp_count": 4,
    "all_off": false,
    "last_communication": "17:30:45"
  }
}
```

**响应字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| connected | bool | 网关是否已连接 |
| gateway_ip | string/null | 网关 IP 地址 |
| gateway_id | int/null | 网关设备 ID |
| lamp_count | int | 已发现的灯泡数量 |
| all_off | bool | 是否所有灯泡都已关闭 |
| last_communication | string/null | 最后一次通信时间 (HH:MM:SS) |

### 4.3 健康检查

#### 4.3.1 服务健康状态

检查服务运行状态和网关连接情况。

**请求**:
```http
GET /api/v1/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "gateway_connected": true,
  "lamp_count": 4,
  "all_off": false,
  "last_communication": "17:30:45",
  "timestamp": "2026-03-19T17:30:50Z"
}
```

### 4.4 日志查询

#### 4.4.1 获取操作日志

获取历史操作记录，支持分页。

**请求**:
```http
GET /api/v1/logs?limit=10&offset=0
```

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 50 | 返回记录数量 |
| offset | int | 0 | 偏移量 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "logs": [
      {
        "id": 1,
        "operation": "turn_on",
        "device_id": 1680764563,
        "details": "{\"red\": 255, \"green\": 100, \"blue\": 50}",
        "success": true,
        "created_at": "2026-03-19T17:30:00Z"
      }
    ],
    "total": 100
  }
}
```

---

## 5. 错误码

### 5.1 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 5.2 业务错误码

| 错误码 | 消息 | 说明 |
|--------|------|------|
| LAMP_NOT_FOUND | Lamp {device_id} not found | 指定灯泡不存在 |
| GATEWAY_DISCONNECTED | Gateway not connected | 网关未连接 |
| INVALID_PARAMETER | Invalid parameter: {field} | 参数验证失败 |
| CONTROL_FAILED | Failed to control lamp {device_id} | 控制灯泡失败 |

### 5.3 错误响应示例

```json
{
  "detail": "Lamp 1680764563 not found"
}
```

或 (业务错误):
```json
{
  "code": 1,
  "message": "Gateway not connected",
  "data": null
}
```

---

## 附录

### A. OpenAPI 文档

服务运行时访问以下地址查看交互式 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### B. Postman Collection

可从 OpenAPI 文档导出 Postman Collection 进行测试。

---

*文档变更历史*

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-03-19 | BA | 初始版本，基于实现代码生成 |
