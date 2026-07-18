"""Private Data Infrastructure (PDI) — secure private data platform.

A standalone secure-hosting product (the "Private Data Infrastructure"
proposal): a private, encrypted data vault with a tamper-evident audit log, a
tenant registry, and a deployment record (on-premises or colocation).

PDI is the infrastructure layer that AI systems such as QRME and JIM-mini can
*optionally* run on top of — storing sensitive data in its encrypted vault
instead of their own databases. Those systems reach PDI only over its HTTP API;
PDI shares no code with them.
"""

__version__ = "0.1.0"
