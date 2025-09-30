# Editorial AI Agents

A multi-agent system for automating editorial workflows - from news scouting and research to content production and distribution.

## Overview

This project implements AI agents that work together to automate various stages of editorial workflows, inspired by modern newsroom automation needs. The system is designed to be modular, allowing different agents to handle specific tasks while working together seamlessly.

## Project Vision

This project aims to build smart tools and AI agents to enhance editorial operations, initially within editorial teams and eventually across other departments.

## Available Agents

### [News Scout Agent](/scout_agent/README.md)

- **Purpose**: Monitors RSS feeds and identifies breaking news/important stories
- **Status**: Done
- **Features**: Real-time monitoring, AI-powered importance scoring, automated reporting

### Research Agent (Planned)

- **Purpose**: Research identified important stories
- **Status**: Planned
- **Features**: Multi-source analysis, fact-checking, background research

### Content Synthesis Agent (Planned)

- **Purpose**: Creates new articles based on researched content
- **Status**: Planned
- **Features**: Style-adaptive writing, multi-perspective synthesis

## Architecture

```text
Input Sources → Scout Agent → Research Agent → Synthesis Agent → Output Channels
```
