# public-projects

My goal is to publish some utilities targeting personal productivity improvements for mundane, personal tasks that take more time than they should :), with a focus on learning as I build. This repo is intended to be a collection of small tools and reference implementations exploring ideas in improving personal productivity (for example: areas such as budgeting, taxes, etc.). Each project in this repository focuses on a specific concept or technique and is intended for experimentation and learning.

## Overview

This repository is intended to evolve to contain multiple independent tools and prototypes. 

Each tool:
- Demonstrates a core idea
- Is intentionally lightweight
- Prioritizes clarity over completeness

Accompanying blog posts and design notes provide additional context for the ideas explored here.

## Tools in this Repository

All tools reside under the tools/ folder.

| Tool | Description | Status |
|----|----|----|
| `TripExpenseCalculator` | a tool to categorize and calculate totals of all expenses undertaken on a trip, including various categories like flights/transport, accommodations, tours, meals, grocery purchases, etc., Inputs include a date range for the trip and bank/credit card statements for relevant duration of trip expenses. Uses Local AI to prevent confidential data leakage. | Prototype |
| `on-demand-geo-exit-node` | a PowerShell tool that spins up a temporary Tailscale exit node on a small Azure VM in the region of your choice, so your PC's traffic egresses from that country. The VM has no inbound ports open, uses a single-use ephemeral auth key, and self-deletes after an idle timeout or maximum lifetime, leaving nothing running or billing between uses. Typical uses include reaching geo-restricted personal accounts while abroad, testing your own site from another region, or securing traffic on untrusted Wi-Fi. | Stable |

New tools may be added over time as ideas evolve.
