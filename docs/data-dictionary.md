# Smart Lamp 数据字典

> **版本**: 1.0
> **日期**: 2026-03-19
> **作者**: Business Analyst

---

## 目录

1. [概述](#1-概述)
2. [API 数据模型](#2-api-数据模型)
3. [数据库模型](#3-数据库模型)
4. [内部数据结构](#4-内部数据结构)

---

## 1. 概述

本文档定义 Smart Lamp API 中使用的所有数据模型和字段。

### 1.1 数据流

```
API 请求/响应 <--> Pydantic 模型 <--> 服务层 <--> 数据库
                          |
                          v
                    Ledo 协议编解码
```

---

## 2. API 数据模型

### 2.1 Lamp (灯泡模型)

表示单个智能灯泡设备的状态。

**文件**: `app/models/lamp.py`

| 字段 | 类型 | 范围 | 默认值 | 必填 | 说明 |
|------|------|------|--------|------|------|
| device_id | int | > 0 | - | 是 | 设备唯一标识符 |
| name | string | - | null | 否 | 灯泡名称/别名 |
| red | int | 0-255 | 255 | 是 | RGB 红色值 |
| green | int | 0-255 | 255 | 是 | RGB 绿色值 |
| blue | int | 0-255 | 255 | 是 | RGB 蓝色值 |
| intensity | int | 0-255 | 255 | 是 | 亮度值，0 表示关闭 |

**属性方法**:
- `is_on`: bool - 检查灯泡是否开启 (intensity > 0)

**方法**:
- `to_bytes()`: bytes - 转换为 Ledo 协议字节数组

**示例**:
```json
{
  "device_id": 1680764563,
  "name": "living_room",
  "red": 255,
  "green": 200,
  "blue": 100,
  "intensity": 200
}
```

### 2.2 LampControlRequest (灯泡控制请求)

控制灯泡时的请求参数模型。

**文件**: `app/models/lamp.py`

| 字段 | 类型 | 范围 | 默认值 | 必填 | 说明 |
|------|------|------|--------|------|------|
| red | int | 0-255 | 255 | 否 | 目标红色值 |
| green | int | 0-255 | 255 | 否 | 目标绿色值 |
| blue | int | 0-255 | 255 | 否 | 目标蓝色值 |
| intensity | int | 0-255 | 255 | 否 | 目标亮度值 |

**示例**:
```json
{
  "red": 255,
  "green": 100,
  "blue": 50,
  "intensity": 200
}
```

### 2.3 ApiResponse (统一响应)

所有 API 的统一响应格式。

**文件**: `app/models/response.py`

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| code | int | 0 | 状态码 (0=成功) |
| message | string | "success" | 响应消息 |
| data | T | null | 响应数据 (泛型) |

**类方法**:
- `success(data, message)`: 创建成功响应
- `error(message, code, data)`: 创建错误响应

### 2.4 HealthResponse (健康检查响应)

健康检查端点的响应模型。

**文件**: `app/models/response.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态 ("healthy" / "unhealthy") |
| gateway_connected | bool | 网关连接状态 |
| lamp_count | int | 灯泡数量 |
| all_off | bool | 是否全部关闭 |
| last_communication | string/null | 最后通信时间 |
| timestamp | string | 响应时间戳 (ISO 8601) |

### 2.5 GatewayStatusResponse (网关状态响应)

网关状态查询的响应模型。

**文件**: `app/models/response.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| connected | bool | 网关是否已连接 |
| gateway_ip | string/null | 网关 IP 地址 |
| gateway_id | int/null | 网关设备 ID |
| lamp_count | int | 灯泡数量 |
| all_off | bool | 是否全部关闭 |
| last_communication | string/null | 最后通信时间 (HH:MM:SS) |

---

## 3. 数据库模型

### 3.1 LampState (灯泡状态历史)

记录灯泡状态变更历史。

**文件**: `app/db/models.py`
**表名**: `lamp_states`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | int | PK, AI | 主键 |
| device_id | int | INDEX, NOT NULL | 设备 ID |
| red | int | DEFAULT 0 | 红色值 |
| green | int | DEFAULT 0 | 绿色值 |
| blue | int | DEFAULT 0 | 蓝色值 |
| intensity | int | DEFAULT 0 | 亮度值 |
| is_on | bool | DEFAULT false | 开关状态 |
| created_at | datetime | INDEX, DEFAULT utcnow | 创建时间 |

**索引**:
- `idx_lamp_states_device_id`: device_id
- `idx_lamp_states_created_at`: created_at

### 3.2 OperationLog (操作日志)

记录所有控制操作。

**文件**: `app/db/models.py`
**表名**: `operation_logs`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | int | PK, AI | 主键 |
| operation | string(50) | INDEX, NOT NULL | 操作类型 |
| device_id | int | NULLABLE | 目标设备 ID |
| details | text | NULLABLE | 操作详情 (JSON) |
| success | bool | DEFAULT true | 操作是否成功 |
| error_message | text | NULLABLE | 错误信息 |
| created_at | datetime | INDEX, DEFAULT utcnow | 创建时间 |

**operation 枚举值**:
- `turn_on`: 开灯操作
- `turn_off`: 关灯操作
- `get_lamps`: 获取灯泡列表
- `discover`: 网关发现

### 3.3 GatewayConnection (网关连接记录)

记录网关连接历史。

**文件**: `app/db/models.py`
**表名**: `gateway_connections`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | int | PK, AI | 主键 |
| gateway_ip | string(50) | NOT NULL | 网关 IP |
| gateway_id | int | NOT NULL | 网关 ID |
| connected | bool | DEFAULT true | 连接状态 |
| created_at | datetime | INDEX, DEFAULT utcnow | 创建时间 |

---

## 4. 内部数据结构

### 4.1 Ledo 协议格式

#### 4.1.1 获取灯泡请求 (TCP)

发送到网关获取所有灯泡列表。

**长度**: 15 字节

| 偏移 | 长度 | 值 | 说明 |
|------|------|-----|------|
| 0-1 | 2 | 0xF3 0xD4 | 魔法头 |
| 2-5 | 4 | gateway_id | 网关 ID (小端序) |
| 6-7 | 2 | 0x00 0x00 | 保留 |
| 8 | 1 | 0x1D | 命令码 |
| 9 | 1 | 0x05 | 数据长度 |
| 10-13 | 4 | 0x00 | 数据 |
| 14 | 1 | 0x43 | 校验/尾部 |

#### 4.1.2 更新灯泡请求 (TCP)

发送到网关更新灯泡状态。

**头部**: 14 字节
**Body**: 每个灯泡 8 字节

| 偏移 | 长度 | 值 | 说明 |
|------|------|-----|------|
| 0-1 | 2 | 0xF3 0xD4 | 魔法头 |
| 2-5 | 4 | 0xFFFFFFFF | 广播网关 ID |
| 6-7 | 2 | 0x00 0x00 | 保留 |
| 8 | 1 | 0x43 | 命令码 |
| 9 | 1 | data_length | 数据长度 |
| 10-13 | 4 | 0x00 | 保留 |
| 14+ | 8*N | lamp_data | 灯泡数据 |

**灯泡数据格式** (每灯泡 8 字节):
| 偏移 | 长度 | 说明 |
|------|------|------|
| 0-3 | 4 | device_id (小端序) |
| 4 | 1 | intensity |
| 5 | 1 | red |
| 6 | 1 | green |
| 7 | 1 | blue |

#### 4.1.3 TCP 响应格式

从网关接收的响应。

**头部**: 10 字节固定
**Body**: header[9] 指定长度

| 偏移 | 长度 | 说明 |
|------|------|------|
| 0-1 | 2 | 魔法头 (0xF3 0xD4) |
| 2-7 | 6 | 保留 |
| 8 | 1 | 命令码 |
| 9 | 1 | 数据长度 |
| 10+ | N | 响应数据 |

#### 4.1.4 UDP 广播包格式

网关发送的广播消息。

**最小长度**: 23 字节

| 偏移 | 长度 | 说明 |
|------|------|------|
| 0-1 | 2 | 魔法头 (0xF3 0xD4) |
| 2-5 | 4 | gateway_id (小端序) |
| 6-20 | 15 | 保留/其他数据 |
| 21 | 1 | removed_devices 状态 |
| 22 | 1 | added_devices 状态 |

### 4.2 事件类型

**文件**: `app/events/manager.py`

| 事件类型 | 说明 | 数据 |
|----------|------|------|
| gateway_connected | 网关已连接 | {ip, gateway_id} |
| gateway_disconnected | 网关断开 | {ip, gateway_id} |
| lamp_state_changed | 灯泡状态变更 | {lamps} |
| lamp_added | 灯泡添加 | {device_id} |
| lamp_removed | 灯泡移除 | {device_id} |
| error | 错误事件 | {error, message} |

---

## 附录

### A. 数据类型映射

| Python | Pydantic | SQLAlchemy | JSON | 说明 |
|--------|----------|------------|------|------|
| int | Integer | Integer | number | 整数 |
| str | String | String | string | 字符串 |
| bool | Boolean | Boolean | boolean | 布尔值 |
| float | Float | Float | number | 浮点数 |
| datetime | datetime | DateTime | string (ISO 8601) | 日期时间 |
| bytes | bytes | LargeBinary | string (base64) | 字节数组 |
| List[T] | array | - | array | 数组 |
| Optional[T] | - | nullable | null | 可空 |

### B. 字节序说明

- **Ledo 协议使用小端序 (little-endian)**
- 与原 Java 版本保持一致

### C. 相关文档

- [API 契约文档](./api-contract.md)
- [协议文档](./protocol.md)
- [需求规格说明书](./requirements.md)

---

*文档变更历史*

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-03-19 | BA | 初始版本 |
