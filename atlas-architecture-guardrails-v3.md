# MongoDB Atlas Solution Guardrails (v8.0) - Version 3.0

## 1. Mandatory Cluster Configuration
*Non-negotiable settings for every proposal.*

- **Node Count:** 5-Node Electable Replica Set (per shard).
- **Regional Distribution:** 3 Regions (Recommended 2-2-1 distribution).
- **MongoDB Version:** Always **8.0**.
- **Search Nodes:** Do **NOT** include Search Nodes currently.
- **Security:** **Bring Your Own Key (BYOK)** is mandatory (Minimum M10 tier required).
- **Backup:** **Multi-Region Cloud Backups** must be enabled.

## 2. Scaling Logic: Vertical vs. Horizontal
Scaling decisions must balance immediate needs with long-term stability[cite: 39, 41].

### Vertical Scaling (Scale-Up)
- **When to use:** For temporary traffic bursts or when CPU/RAM is the primary bottleneck and you are well below the 4TB storage limit[cite: 13, 43].
- **Limitations:** You will eventually hit hardware "ceilings" or price-to-performance cliffs[cite: 15, 17].

### Horizontal Scaling (Sharding/Scale-Out)
- **When to use:** Mandatory for datasets > 4TB or when I/O throughput exceeds a single node's capability[cite: 23, 266, 268].
- **Benefit:** Provides "linear scalability" and avoids the hard ceilings of single-server hardware[cite: 25, 291].

## 3. Storage Thresholds & "Headroom" Rules
*Critical for preventing performance degradation during data movement.*

- **The 4TB Rule:** Atlas has a 4TB (compressed) storage limit for a replica set[cite: 268].
- **The 70-80% Utilization Threshold:** - You must proactively add shards when data consumes **70-80% of total available disk**. 
    - This ensures **20-30% of disk remains free** to provide the resources necessary for "Chunk Migration" (moving data to the new shard) and ongoing background operations[cite: 233, 267].
- **Proactive Growth Calculation:** - **Example:** A customer has 5TB data + 1TB index (6TB total). 
    - A 2-shard M50 cluster provides 8TB total. 
    - **Utilization:** 6TB / 8TB = 75%. 
    - **Decision:** Because this is already in the "Must Scale" range and leaves little room for growth, you **must recommend 3 shards** (12TB capacity) to ensure the customer doesn't need to scale again immediately after go-live[cite: 51, 56, 270].

## 4. Workload-Specific Logic
- **Storage-Heavy / Low-Write:** Use sharding to gain disk capacity (e.g., 4 shards of M50 for 16TB) rather than scaling to a massive M200 node[cite: 267].
- **Read-Heavy / High-Performance:** Ensure the **RAM is >= 15-20% of the active data volume** to maintain the "Working Set" in memory and avoid disk I/O bottlenecks[cite: 265].
- **High Ingestion:** Scale tier vertically for more CPU/IOPS to handle write locks and ingestion pressure[cite: 266].

## 5. Output Instructions for AI Agents
1. **Capacity Audit:** State the total storage (Data + Index) and the utilization % of the proposed shards.
2. **Growth Buffer:** Explicitly state: *"We have sized this with a 3-shard configuration to ensure you remain below the 80% utilization threshold, providing the necessary 20-30% disk headroom for background operations and future data growth."*
3. **Topology Justification:** If sharding is required, explain if it is for **Storage Capacity** (to stay under the 4TB per-node limit) or **Performance** (to distribute I/O)[cite: 265, 266, 267].
4. **BYOK Confirmation:** Remind the customer that the chosen M10+ tier facilitates the mandatory BYOK security requirement.
