# Arduino Remote Control System Architecture

## Overview

This document describes how phone-based remote control of the Arduino Uno currently works.

## Current end-to-end path

```text
[Phone Browser]
      |
      | HTTPS request
      v
[Cloudflare Tunnel Public URL]
      |
      | forwards traffic
      v
[Local FastAPI Service on Laptop]
      |
      | pyserial / USB serial (COM3)
      v
[Arduino Uno]
      |
      | executes hardware action
      v
[Pin 13 LED]
```

## Response path

```text
[Arduino Uno]
      |
      | serial response: OK / STATUS
      v
[Local FastAPI Service]
      |
      | JSON response
      v
[Cloudflare Tunnel]
      |
      | HTTPS response
      v
[Phone Browser]
```

## Component responsibilities

### 1. Phone Browser
- Opens the public URL
- Displays the control page
- Sends requests such as:
  - `POST /led/on`
  - `POST /led/off`
  - `GET /status`
- Shows returned status/output

### 2. Cloudflare Tunnel
- Gives a temporary public HTTPS URL
- Forwards external traffic to local `127.0.0.1:8000`
- Makes the local FastAPI service reachable from the phone

### 3. Local FastAPI Service
- Exposes HTTP endpoints for the page
- Translates web requests into serial commands
- Talks to the Arduino over USB serial
- Returns structured JSON results to the browser

### 4. Arduino Uno
- Receives line-based serial commands
- Recognizes:
  - `LED_ON`
  - `LED_OFF`
  - `STATUS`
- Controls pin 13 LED
- Returns status lines such as:
  - `OK LED_ON`
  - `OK LED_OFF`
  - `STATUS ON`
  - `STATUS OFF`

## Why phone control works

Phone control works because the phone does not connect to the Arduino directly.
Instead, it talks to a public tunnel URL, which forwards requests to the laptop.
The laptop runs FastAPI, and FastAPI sends serial commands to the Arduino.

## Current properties
- Arduino is physically attached to the laptop
- FastAPI is the local control bridge
- Cloudflare Tunnel is the public access bridge
- The browser is only the control UI

## Current limitations
- The Cloudflare URL is temporary
- The current public MVP is for fast validation, not long-term deployment
- Security still needs tightening for stable public use
- The laptop and local service must stay running

## Recommended next steps
1. Restore and verify token-based protection correctly
2. Keep public control but require authentication
3. Expand from LED-only control to generic whitelisted actions
4. Later wrap the system as an RL/agent environment
