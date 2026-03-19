# Ledo Protocol Specification

## Overview

The **Ledo Protocol** is a binary protocol used for communication between the Smart Lamp API and Ledo gateway devices. It operates over two transport layers:

| Transport | Port | Direction | Purpose |
|-----------|------|-----------|---------|
| UDP | 41328 | Gateway → Server | Device discovery and announcements |
| TCP | 41330 | Client ↔ Gateway | Device control and status queries |

## Protocol Characteristics

| Attribute | Value |
|-----------|-------|
| Magic Bytes | `0xF3 0xD4` |
| Byte Order | **Little-endian** |
| Encoding | Binary |
| Header Size | 10 bytes (TCP), 23+ bytes (UDP) |

---

## UDP Protocol - Gateway Discovery

### Packet Structure

Gateways periodically broadcast UDP packets to announce their presence on the network.

```
+--------+--------+----------------+----------------+--------+--------+
| Magic  | Magic  | Gateway ID     | Reserved       | Removed| Added  |
| 0xF3   | 0xD4   | (int32 LE)     | (15 bytes)     | Devices| Devices|
+--------+--------+----------------+----------------+--------+--------+
  Byte 0   Byte 1   Bytes 2-5       Bytes 6-20       Byte 21  Byte 22
```

| Field | Size | Type | Description |
|-------|------|------|-------------|
| Magic | 2 bytes | `0xF3 0xD4` | Protocol identifier |
| Gateway ID | 4 bytes | uint32 LE | Unique gateway identifier |
| Reserved | 15 bytes | - | Reserved for future use |
| Removed Devices | 1 byte | uint8 | Bitmask of removed devices |
| Added Devices | 1 byte | uint8 | Bitmask of added devices |

### Minimum Packet Size

**23 bytes** - Packets shorter than this should be discarded.

### Python Implementation

```python
import struct
from typing import Optional

class LedoProtocol:
    MAGIC = bytes([0xF3, 0xD4])

    @classmethod
    def parse_gateway_from_udp(cls, data: bytes) -> Optional[dict]:
        """Parse gateway info from UDP broadcast packet."""
        if len(data) < 23:
            return None
        if data[0:2] != cls.MAGIC:
            return None

        gateway_id = struct.unpack("<I", data[2:6])[0]  # little-endian
        removed_devices = data[21]
        added_devices = data[22]

        return {
            "gateway_id": gateway_id,
            "removed_devices": removed_devices,
            "added_devices": added_devices,
        }
```

### Example UDP Packet

```
F3 D4 E3 2B 69 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00
│  │  └──────────┴───────────────────────────────────────┴────────┴─────┘
│  │        │                         │                      │
│  │     Gateway ID              Reserved              Added/Removed
│  │   (0x01692BE3 = 23698115)                      (01/00)
Magic Bytes
```

---

## TCP Protocol - Device Control

### Request Header Structure

All TCP requests start with a 15-byte header:

```
+--------+--------+----------------+--------+--------+--------+----------------+--------+
| Magic  | Magic  | Gateway ID     |  Resv  |  Resv  | Command| Length |  Reserved      | Trailer|
| 0xF3   | 0xD4   | (int32 LE)     |  0x00  |  0x00  | (byte) | (byte)  |  4 bytes       | 0x43   |
+--------+--------+----------------+--------+--------+--------+--------+----------------+--------+
  Byte 0   Byte 1   Bytes 2-5       Byte 6   Byte 7   Byte 8   Byte 9    Bytes 10-13     Byte 14
```

| Field | Size | Type | Description |
|-------|------|------|-------------|
| Magic | 2 bytes | `0xF3 0xD4` | Protocol identifier |
| Gateway ID | 4 bytes | uint32 LE | Target gateway (0xFFFFFFFF for broadcast) |
| Reserved | 2 bytes | `0x00 0x00` | Reserved fields |
| Command | 1 byte | uint8 | Command code (see below) |
| Data Length | 1 byte | uint8 | Length of data payload |
| Reserved | 4 bytes | `0x00...` | Reserved fields |
| Trailer | 1 byte | `0x43` | Checksum/trailer |

### Command Codes

| Code | Name | Direction | Description |
|------|------|-----------|-------------|
| `0x1D` | CMD_GET_LAMPS | Client → Gateway | Request list of all lamps |
| `0x43` | CMD_UPDATE_LAMPS | Client → Gateway | Update lamp states |

---

### Command: Get Lamps (0x1D)

Retrieves the current state of all lamps from the gateway.

#### Request Format

```
F3 D4 [Gateway ID LE] 00 00 1D 00 00 00 00 00 43
```

| Field | Value |
|-------|-------|
| Magic | `F3 D4` |
| Gateway ID | 4 bytes (little-endian) |
| Command | `0x1D` |
| Data Length | `0x00` (no payload) |

#### Python Implementation

```python
@classmethod
def build_get_lamps_request(cls, gateway_id: int) -> bytes:
    """Build request to get all lamps from gateway."""
    gateway_bytes = struct.pack("<I", gateway_id)  # little-endian
    return bytes([
        0xF3, 0xD4,          # Magic
        *gateway_bytes,      # Gateway ID (4 bytes)
        0x00, 0x00,          # Reserved
        0x1D,                # Command: GET_LAMPS
        0x00,                # Data length
        0x00, 0x00, 0x00, 0x00,  # Reserved
        0x43,                # Trailer
    ])
```

#### Response Format

The response contains an array of lamp data, each lamp represented by 8 bytes:

```
+----------------+-----------+-----------+-----------+-----------+
| Device ID      | Intensity | Red       | Green     | Blue      |
| (int32 LE)     | (byte)    | (byte)    | (byte)    | (byte)    |
+----------------+-----------+-----------+-----------+-----------+
   Bytes 0-3        Byte 4      Byte 5      Byte 6      Byte 7
```

| Field | Size | Type | Range | Description |
|-------|------|------|-------|-------------|
| Device ID | 4 bytes | uint32 LE | - | Unique lamp identifier |
| Intensity | 1 byte | uint8 | 0-255 | Brightness (0 = off) |
| Red | 1 byte | uint8 | 0-255 | Red color component |
| Green | 1 byte | uint8 | 0-255 | Green color component |
| Blue | 1 byte | uint8 | 0-255 | Blue color component |

#### Response Parsing

```python
@classmethod
def parse_lamp_list(cls, data: bytes) -> List[Lamp]:
    """Parse lamp list from TCP response."""
    lamps = []
    if len(data) < 8:
        return lamps

    # Each lamp is 8 bytes
    lamp_count = len(data) // 8
    for i in range(lamp_count):
        offset = i * 8
        device_id = struct.unpack("<I", data[offset:offset+4])[0]
        intensity = data[offset + 4]
        red = data[offset + 5]
        green = data[offset + 6]
        blue = data[offset + 7]

        lamps.append(Lamp(
            device_id=device_id,
            intensity=intensity,
            red=red,
            green=green,
            blue=blue,
        ))
    return lamps
```

---

### Command: Update Lamps (0x43)

Updates the state (color and intensity) of one or more lamps.

#### Request Format

```
Header (15 bytes):
F3 D4 FF FF FF FF 00 00 43 [Length] 00 00 00 00 43

Payload (N × 8 bytes):
[Device ID LE] [Intensity] [Red] [Green] [Blue] × N
```

| Field | Value |
|-------|-------|
| Magic | `F3 D4` |
| Gateway ID | `0xFFFFFFFF` (broadcast) |
| Command | `0x43` |
| Data Length | `N × 8` (number of lamps × 8) |
| Trailer | `0x43` |

#### Lamp Payload Structure

Each lamp in the payload is 8 bytes:

```python
def to_bytes(self) -> bytes:
    """Convert lamp state to bytes for TCP protocol."""
    device_id_bytes = self.device_id.to_bytes(4, byteorder="little")
    return device_id_bytes + bytes([
        self.intensity & 0xFF,
        self.red & 0xFF,
        self.green & 0xFF,
        self.blue & 0xFF,
    ])
```

#### Python Implementation

```python
@classmethod
def build_update_lamps_request(cls, lamps: List[Lamp]) -> bytes:
    """Build request to update lamp states."""
    lamp_data = b"".join(lamp.to_bytes() for lamp in lamps)
    data_length = len(lamp_data) + 4  # +4 for additional data

    header = bytes([
        0xF3, 0xD4,                   # Magic
        0xFF, 0xFF, 0xFF, 0xFF,       # Broadcast gateway ID
        0x00, 0x00,                   # Reserved
        cls.CMD_UPDATE_LAMPS,         # Command: 0x43
        data_length & 0xFF,           # Data length
        0x00, 0x00, 0x00, 0x00,       # Reserved
        0x43,                         # Trailer
    ])
    return header + lamp_data
```

#### Example: Update Single Lamp

For a lamp with `device_id=1680764563`, `red=255`, `green=0`, `blue=0`, `intensity=255`:

```
Header:
F3 D4 FF FF FF FF 00 00 43 0C 00 00 00 00 43

Payload:
E3 2B 69 01 FF 00 00 FF
│  └─────┴───┴────┴────┘
│       │    │    │
Device ID   R    G    B
(LE)     I
```

Full packet:
```
F3 D4 FF FF FF FF 00 00 43 0C 00 00 00 00 43 E3 2B 69 01 FF 00 00 FF
│  │  └────────┴──┴──┴──┴────┬─┴──────────────────────────────────────┘
│  │           Header          │
Magic                       Payload (8 bytes)
```

---

## Response Header Parsing

```python
@classmethod
def parse_tcp_response_header(cls, data: bytes) -> Optional[dict]:
    """Parse TCP response header."""
    if len(data) < 10:
        return None
    if data[0:2] != cls.MAGIC:
        return None

    command = data[8]
    data_length = data[9]

    return {
        "command": command,
        "data_length": data_length,
    }
```

---

## Data Models

### Lamp Model

```python
from pydantic import BaseModel, Field
from typing import Optional

class Lamp(BaseModel):
    """Lamp model representing a smart lamp device."""
    device_id: int = Field(..., description="Device unique identifier")
    name: Optional[str] = Field(None, description="Lamp name/alias")
    red: int = Field(255, ge=0, le=255, description="Red color value (0-255)")
    green: int = Field(255, ge=0, le=255, description="Green color value (0-255)")
    blue: int = Field(255, ge=0, le=255, description="Blue color value (0-255)")
    intensity: int = Field(255, ge=0, le=255, description="Brightness intensity (0-255)")

    @property
    def is_on(self) -> bool:
        """Check if lamp is on (intensity > 0)."""
        return self.intensity > 0
```

### Lamp Control Request

```python
class LampControlRequest(BaseModel):
    """Request model for controlling a lamp."""
    red: Optional[int] = Field(255, ge=0, le=255)
    green: Optional[int] = Field(255, ge=0, le=255)
    blue: Optional[int] = Field(255, ge=0, le=255)
    intensity: Optional[int] = Field(255, ge=0, le=255)
```

---

## Complete Packet Examples

### Example 1: Get Lamps Request

**Gateway ID:** `23698115` (0x01692BE3)

```
F3 D4 E3 2B 69 01 00 00 1D 00 00 00 00 00 43
│  │  └─────────┴────────┴──┴──┴────────┴───┘
│  │       │         │   │      │     Trailer
│  │   Gateway ID   Resv CMD    Reserved
Magic  (little-endian) (0x1D)
Bytes
```

### Example 2: Update Two Lamps

**Lamp 1:** device_id=1680764563, RGB=(255,0,0), intensity=255
**Lamp 2:** device_id=1680764564, RGB=(0,255,0), intensity=200

```
F3 D4 FF FF FF FF 00 00 43 10 00 00 00 00 43
E3 2B 69 01 FF 00 00 FF
E4 2B 69 01 C8 00 FF 00
```

---

## Error Handling

| Condition | Action |
|-----------|--------|
| Packet < 23 bytes (UDP) | Discard |
| Magic bytes mismatch | Discard |
| TCP connection timeout | Retry after 5 seconds |
| Gateway not responding | Mark gateway offline |

---

## References

- Source Code: [`app/protocols/ledo_protocol.py`](../app/protocols/ledo_protocol.py)
- Data Models: [`app/models/lamp.py`](../app/models/lamp.py)
- API Endpoints: [`README.md`](../README.md)

---

*Document Version: 1.0*
*Last Updated: 2026-03-19*
