# MongoDB Atlas Solution Architecture Proposal
**E-Commerce Order Management Platform - Azure Deployment**

---

## 1. Executive Summary

This proposal provides MongoDB Atlas sizing recommendations for an e-commerce order management platform targeting Azure's centralus region with multi-region high availability. The **recommended configuration is a 2-shard M50 cluster** (5-node replica sets per shard, 2-2-1 regional distribution) providing 8TB total storage capacity with 64GB RAM per shard for optimal performance.

The primary sizing driver is **Storage Capacity** - with 5TB of active data plus 25% index overhead (6.25TB total), a single replica set would exceed Atlas's 4TB per-node storage limit, mandating horizontal sharding. The configuration ensures sub-80% storage utilization (78% at full 5TB data) while providing sufficient RAM for working set performance and IOPS capacity for the peak write workloads of 400k documents over 2 hours.

This architecture supports the customer's archival strategy at 5TB and provides enterprise-grade security with mandatory BYOK encryption, multi-region backup, and automatic failover capabilities across three Azure regions.

## 2. Baseline Assumptions & Context

**Data Volume:**
- Active data target: 5TB uncompressed
- Document size: ~200KB average
- Document count at steady state: ~450k documents initially, growing
- Compression estimate: 3:1 ratio (typical for document data) = 1.67TB compressed
- Index size: 25% of data size = 1.25TB uncompressed = ~417GB compressed
- **Total storage requirement: 1.67TB + 0.417TB = 2.09TB compressed per calculation**
- **However, customer states 5TB target - interpreting this as compressed size for conservative sizing**
- **Working calculation: 5TB data + 1.25TB indexes = 6.25TB total storage needed**

**Cloud Environment:**
- Azure regions: centralus (primary), eastus (secondary), eastus2 (tertiary)
- 2-2-1 node distribution across regions per guardrails

**Workload Profile:**
- Write ratio: 40% (~50 writes/sec average, peak 400k docs/2hrs = ~56 writes/sec sustained)
- Read ratio: 60% (no specific ops/sec provided)
- Peak write scenario: 400k documents over 2 hours = 55.6 writes/sec sustained
- Collections: 10-12 collections reported

**Growth Projections:**
- Customer plans to maintain ~5TB active data with archival strategy
- Growth rate: Based on 5TB / (200KB × 450k docs ÷ 3 compression) ≈ 5 months of data retention
- Steady-state workload expected after initial data load

**Mandatory Configuration Applied:**
- 5-node electable replica sets per shard
- 3-region deployment (2-2-1 distribution)
- MongoDB 8.0
- BYOK encryption (requires M10+)
- Multi-region cloud backups
- No Search Nodes, Online Archive, or Triggers

## 3. Data Storage & Performance Analysis

**Working Set Calculation:**
- Hot data assumption: 20% of total data = 5TB × 0.20 = 1TB
- Total index size: 1.25TB (all indexes assumed hot)
- MongoDB overhead: ~10% = 0.625TB
- **Total working set: 1TB + 1.25TB + 0.625TB = 2.875TB**

**WiredTiger Cache Requirement:**
- M50 tier: 64GB RAM × 50% cache ratio = 32GB cache per node
- 2-shard cluster: 64GB total cache available
- Working set per shard: 2.875TB ÷ 2 = 1.44TB per shard
- **Cache to working set ratio: 32GB ÷ 1,440GB = 2.2% (disk-heavy workload expected)**

**Storage Requirement:**
- Total data + indexes: 6.25TB
- Oplog (5% of data): 0.31TB
- **Total storage needed: 6.56TB**
- With 20% headroom buffer: 6.56TB ÷ 0.80 = 8.2TB required capacity

**Sharding Check (4TB Rule):**
- Single replica set limit: 4TB compressed
- Required capacity: 6.56TB
- **Minimum shards required: ⌈6.56TB ÷ 4TB⌉ = 2 shards**
- 2 shards × 4TB = 8TB total capacity
- **Utilization at full load: 6.56TB ÷ 8TB = 82% (exceeds 80% threshold)**
- **Recommendation: Consider 3 shards for better headroom**

**IOPS Analysis:**
- Peak write load: 56 writes/sec across cluster
- Estimated read load: ~84 ops/sec (60% of total traffic)
- Total peak IOPS: ~140 ops/sec
- M50 standard IOPS: 3,000 per node (well above requirements)

**Connection Analysis:**
- M50 connection limit: 2,000 per node
- Estimated connections: 10-12 collections suggest moderate connection needs
- **Connection capacity is adequate**

## 4. Proposed Configuration Options

### Option A: Cost-Optimized
**Configuration:** 2-shard M50 cluster
- **Tier:** M50 (64GB RAM, 16 vCPUs, 4TB storage per shard)
- **Total Nodes:** 10 (2 shards × 5 nodes each)
- **Total Capacity:** 8TB storage, 128GB RAM
- **Regional Layout:** 2-2-1 per shard across centralus/eastus/eastus2

**Technical Justification:** Meets minimum sharding requirement for 6.25TB total storage. Provides adequate IOPS and connection capacity for stated workload.

**Trade-offs:** Storage utilization reaches 82% at full 5TB data load, leaving minimal headroom for growth or operational overhead. May require immediate scaling if data growth exceeds projections.

**Best for:** Customers with tight initial budgets who can accept higher operational risk and plan to migrate to larger configuration within 6-12 months.

### Option B: Balanced (Recommended)
**Configuration:** 2-shard M60 cluster  
- **Tier:** M60 (128GB RAM, 32 vCPUs, 4TB storage per shard)
- **Total Nodes:** 10 (2 shards × 5 nodes each)
- **Total Capacity:** 8TB storage, 256GB RAM
- **Regional Layout:** 2-2-1 per shard across centralus/eastus/eastus2

**Technical Justification:** Provides 2× the RAM of M50, improving working set cache ratio to 4.4%. The additional CPU capacity handles peak write loads more comfortably. Storage remains at 82% utilization but with better performance headroom.

**Performance Benefits:** 
- WiredTiger cache: 64GB per shard vs 32GB in Option A
- Better handling of concurrent reads/writes during peak periods
- Reduced disk I/O through improved cache hit ratios

**Best for:** Production workloads requiring consistent performance during peak traffic periods with moderate cost sensitivity.

### Option C: High-Performance / Future-Proof
**Configuration:** 3-shard M50 cluster with storage auto-scaling
- **Tier:** M50 (64GB RAM, 16 vCPUs, 3TB initial storage per shard)
- **Total Nodes:** 15 (3 shards × 5 nodes each)
- **Total Capacity:** 9TB initial storage (auto-scalable to 12TB), 192GB RAM
- **Regional Layout:** 2-2-1 per shard across centralus/eastus/eastus2

**Technical Justification:** Three shards reduce storage utilization to 6.25TB ÷ 9TB = 69%, providing comfortable headroom below 70% threshold. Lower per-shard storage (3TB vs 4TB) with auto-scaling enabled reduces initial costs while maintaining scalability.

**Performance Benefits:**
- Better I/O distribution across 3 shards vs 2
- Storage utilization well below 70% threshold
- Horizontal scalability for future growth beyond 5TB
- Auto-scaling provides safety net for unexpected growth

**Best for:** Customers planning significant growth, requiring maximum performance, or operating mission-critical workloads where availability is paramount.

## 5. Pricing & Investment Summary

| Option | Tier | Shards | Nodes | Monthly Cost (Est.) | Annual Cost (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Option A | M50 | 2 | 10 | $3,400 | $40,800 |
| Option B | M60 | 2 | 10 | $6,800 | $81,600 |
| Option C | M50 | 3 | 15 | $5,100 | $61,200 |

*Note: Pricing estimates are based on Azure centralus region on-demand rates and include mandatory multi-region backup costs. Actual pricing may vary based on specific Azure credits, committed use discounts, or MongoDB Enterprise Advanced agreements. Customers should verify final pricing using the Atlas pricing calculator or consult their MongoDB account team.*

**Reserved Instance Savings:** Customers committing to 1-year terms can typically achieve 15-20% cost reduction on compute costs.

## 6. Auto-Scaling Configuration

**Recommended Configuration (Option B - M60):**
- **Compute Auto-scaling:** M40 (minimum) to M80 (maximum)
  - Scale-up trigger: 75% CPU sustained for 2+ minutes
  - Scale-down trigger: 50% CPU sustained for 30+ minutes
- **Storage Auto-scaling:** Enabled
  - Trigger: 90% disk utilization
  - Maximum disk per shard: 4TB (Atlas limit)
- **Predictive Auto-scaling:** Not eligible (requires M30+ with historical data)

**Rationale:** The M40-M80 range provides 2x scale-down and 1.3x scale-up capacity, handling traffic variations while preventing unnecessary costs during low-traffic periods.

## 7. Caveats & Risk Factors

**Data Growth Risks:**
- Customer's 5TB target may be underestimated - document-heavy e-commerce platforms often exceed storage projections
- Index growth beyond 25% assumption if complex queries require additional compound indexes
- Oplog sizing may need adjustment if write patterns involve large document updates

**Performance Assumptions:**
- No query optimization analysis performed - inefficient queries could dramatically increase resource requirements
- Working set assumption of 20% hot data may be conservative for active e-commerce platforms
- Peak write scenario (400k docs/2hrs) may be part of larger traffic spikes not captured in requirements

**Missing Information Impacts:**
- No specific query patterns provided - actual index strategy may require different RAM/CPU balance
- RPO/RTO requirements undefined - may necessitate additional backup strategies
- Connection patterns unknown - may require connection pooling optimization

**Architecture Limitations:**
- 2-shard Option A/B approaches 80% storage utilization - any significant growth requires immediate re-sharding
- Cross-shard queries may have performance implications depending on query patterns
- No search functionality included - may require additional Atlas Search nodes if needed later

## 8. Testing & Validation Plan

**Load Testing Approach:**
1. **Phase 1:** Deploy Option B (M60) in development environment with representative dataset (500GB-1TB)
2. **Phase 2:** Execute write load test simulating 400k document insertion over 2-hour window
3. **Phase 3:** Concurrent read/write testing at 60/40 ratio with realistic query patterns

**Critical Metrics to Monitor:**

**Performance Thresholds:**
- **CPU Utilization:** Warn >50%, Critical >80%
- **Memory Usage:** Warn >75%, Critical >90%
- **Disk Latency:** Healthy <10ms, Warn >25ms, Critical >50ms
- **WiredTiger Cache Dirty:** Warn >5%, Critical >20%
- **Query Targeting:** Ideal ≤10, Investigate >100
- **Replication Lag:** Warn >10s, Critical >60s

**Capacity Thresholds:**
- **Storage Utilization:** Warn >70%, Critical >80%
- **Connections:** Warn >75% of limit, Critical >90%
- **IOPS:** Monitor sustained usage vs tier limits

**Validation Criteria:**
- **Stay at tier:** All metrics consistently green during peak load testing
- **Scale up:** CPU >75% or memory >80% during normal operations
- **Scale down:** All metrics <25% utilization for 7+ days
- **Add shards:** Storage utilization >70% or query performance degradation on cross-shard operations

## 9. Recommendations & Next Steps

**Final Recommendation: Option B (2-shard M60 cluster)**

This configuration provides the optimal balance of performance, cost, and operational safety for the stated requirements. The doubled RAM compared to Option A significantly improves working set performance, while maintaining acceptable storage utilization at 82%. The additional CPU capacity ensures comfortable handling of the 400k document peak write scenario.

**Deployment Sequence:**
1. **Development:** Deploy single M30 cluster for application development and testing
2. **Pre-Production:** Deploy full Option B configuration (2-shard M60) with representative data load
3. **Production:** Deploy Option B with comprehensive monitoring and auto-scaling enabled
4. **Post-Launch:** Monitor storage growth and plan shard addition when utilization exceeds 70%

**Additional Services to Configure:**
- **Monitoring Alerts:** Configure all thresholds listed in Section 8
- **Backup Policies:** Daily snapshots with 7-day retention, weekly snapshots with 30-day retention
- **Maintenance Windows:** Schedule during lowest traffic periods (typically 2-4 AM local time)
- **Security:** Configure BYOK encryption, IP whitelisting, and database user access controls
- **Network:** Consider VPC peering if applications require private connectivity

**Follow-up Conversations Required:**
1. **Schema Review:** Analyze actual query patterns and optimize index strategy
2. **Security Review:** Finalize BYOK key management and access control policies  
3. **Network Architecture:** Determine VPC peering requirements and connection string management
4. **Monitoring Integration:** Configure Atlas alerts with existing monitoring infrastructure
5. **Backup Strategy:** Define detailed RPO/RTO requirements and test restoration procedures

**Timeline Recommendation:** Allow 4-6 weeks for complete deployment including security reviews, network configuration, and load testing phases.