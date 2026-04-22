# MongoDB Atlas Sizing Proposal: E-Commerce Order Management Platform

## 1. Executive Summary

This proposal addresses the sizing requirements for an e-commerce order management platform targeting Azure with a 5TB data retention policy. The **recommended configuration is a 2-shard M50 cluster** deployed across three Azure regions (centralus, eastus, eastus2) in a 2-2-1 node distribution. This balanced approach provides optimal cost-efficiency while maintaining high availability and performance headroom for the projected workload.

The **primary sizing driver is Storage capacity**, requiring horizontal scaling (sharding) to accommodate the 5TB+ total dataset while maintaining the mandatory 20-30% disk headroom for background operations. The configuration ensures compliance with Atlas guardrails including 5-node electable replica sets, MongoDB 8.0, BYOK encryption, and multi-region cloud backups.

## 2. Baseline Assumptions & Context

### Data Volume Analysis:
- **Raw Data:** 5TB (customer-stated retention target)
- **Compression Estimate:** 5TB ÷ 3 (WiredTiger zstd typical ratio) = **1.67TB compressed data**
- **Index Size:** 25% of data size = 1.67TB × 0.25 = **0.42TB indexes**
- **Total Storage Requirement:** 1.67TB + 0.42TB = **2.09TB base storage**

### Cloud Environment:
- **Provider:** Microsoft Azure
- **Regions:** centralus (primary), eastus, eastus2
- **Distribution:** 2-2-1 electable nodes across regions

### Workload Profile:
- **Write Pattern:** Average 50 writes/sec, peak 400k docs in 2 hours (≈56 writes/sec)
- **Read/Write Ratio:** 60% reads, 40% writes
- **Peak Write Requirement:** 400k docs ÷ 2 hours = 56 writes/sec sustained
- **Collections:** 10-12 collections (connection scaling consideration)

### Growth Projections:
- **Data Retention:** Fixed at 5TB with archiving (steady-state assumption)
- **Document Growth:** 450k initial documents with ongoing increases
- **Timeline:** Approximately 5 months to reach 5TB target based on document size estimates

### Mandatory Configuration Applied:
- 5-node electable replica set per shard, 3 regions (2-2-1), MongoDB 8.0, BYOK security, multi-region backups enabled, no Search Nodes

## 3. Data Storage & Performance Analysis

### Working Set Calculation:
- **Hot Data Assumption:** 20% of total data actively accessed = 5TB × 0.20 = **1TB hot data**
- **Total Index Size:** 0.42TB (all indexes assumed hot)
- **Overhead:** 10% buffer = (1TB + 0.42TB) × 0.10 = **0.14TB**
- **Working Set Total:** 1TB + 0.42TB + 0.14TB = **1.56TB working set**

### WiredTiger Cache Requirements:
- **M50 RAM:** 64GB per node
- **Cache Allocation:** 64GB × 50% = **32GB cache per node**
- **Cache vs Working Set:** 32GB cache << 1,560GB working set
- **Analysis:** Working set cannot fit entirely in cache; tier selection must prioritize I/O performance over pure memory containment

### Storage Requirement & Sharding Analysis:
- **Total Storage Needed:** 2.09TB + 30% headroom = **2.72TB minimum**
- **4TB Rule Check:** 2.72TB < 4TB (single shard possible, but headroom analysis required)
- **Single Shard Utilization:** 2.72TB ÷ 4TB = **68% utilization**
- **Recommendation:** Single shard acceptable, but 2-shard approach provides better operational headroom and future scaling

### IOPS Analysis:
- **Write Load:** 56 writes/sec peak
- **Read Load:** 84 reads/sec (assuming 60/40 ratio)
- **Total Operations:** ~140 ops/sec
- **Azure M40+ Standard IOPS:** 3,000+ IOPS baseline (sufficient for workload)

### Connection Analysis:
- **M40 Connection Limit:** 3,000 connections
- **M50 Connection Limit:** 4,500 connections  
- **10-12 Collections:** Low connection requirements, no constraint

## 4. Proposed Configuration Options

### Option A: Cost-Optimized
**Configuration:** 1-Shard M40 Cluster
- **Tier:** M40 (16GB RAM, 4 vCPUs per node)
- **Storage:** 3TB per shard (auto-scaling enabled)
- **Nodes:** 5 electable nodes (2-2-1 across regions)
- **Total Cluster Storage:** 3TB
- **Utilization:** 2.72TB ÷ 3TB = **91% utilization**

**Technical Justification:** Meets minimum storage requirements with single-shard simplicity. However, operates at 91% disk utilization, leaving minimal headroom for background operations, growth, or emergency scenarios.

**Trade-offs:** High disk utilization risk, limited operational headroom, challenging for chunk migrations if sharding becomes necessary later.

### Option B: Balanced (Recommended)  
**Configuration:** 2-Shard M50 Cluster
- **Tier:** M50 (64GB RAM, 16 vCPUs per node)
- **Storage:** 2TB per shard (auto-scaling enabled)
- **Shards:** 2 shards
- **Nodes:** 10 electable nodes total (5 per shard, 2-2-1 per shard across regions)
- **Total Cluster Storage:** 4TB
- **Utilization:** 2.72TB ÷ 4TB = **68% utilization**

**Technical Justification:** Provides optimal balance of cost, performance, and operational headroom. 68% utilization ensures 32% free space for background operations, index additions, and unexpected growth. M50 tier provides sufficient CPU and memory for the workload while maintaining cost efficiency.

**Best-fit Use Case:** Production deployment requiring operational stability, growth accommodation, and cost optimization.

### Option C: High-Performance / Future-Proof
**Configuration:** 2-Shard M60 Cluster  
- **Tier:** M60 (128GB RAM, 32 vCPUs per node)
- **Storage:** 3TB per shard (auto-scaling enabled)
- **Shards:** 2 shards
- **Nodes:** 10 electable nodes total (5 per shard, 2-2-1 per shard across regions)
- **Total Cluster Storage:** 6TB
- **Utilization:** 2.72TB ÷ 6TB = **45% utilization**

**Technical Justification:** Significant performance headroom with 45% storage utilization and doubled RAM/CPU resources. Handles 2-3x data growth without re-architecture. Enhanced WiredTiger cache (64GB per node) improves query performance for larger working sets.

**Best-fit Use Case:** High-growth scenarios, performance-critical applications, or environments requiring maximum operational flexibility.

## 5. Pricing & Investment Summary

| Option | Tier | Shards | Nodes | Monthly Cost (Est.) | Annual Cost (Est.) |
|:-------|:-----|:-------|:------|:-------------------|:-------------------|
| Option A | M40 | 1 | 5 | $2,400 | $28,800 |
| Option B | M50 | 2 | 10 | $4,800 | $57,600 |
| Option C | M60 | 2 | 10 | $7,200 | $86,400 |

*Note: Pricing estimates include base cluster costs with BYOK encryption and multi-region backup. Actual costs may vary based on data transfer, backup storage, and Azure region-specific pricing. Please verify with the MongoDB Atlas pricing calculator or your MongoDB account team for precise quotations.*

## 6. Auto-Scaling Configuration

**Recommended Configuration (Option B - M50):**
- **Compute Auto-Scaling Range:** M40 (minimum) to M80 (maximum)
- **Storage Auto-Scaling:** Enabled with 90% threshold trigger
- **Starting Storage:** 2TB per shard with auto-expansion capability
- **Predictive Auto-Scaling:** Enabled (cluster meets M30+ requirement with 2+ weeks activity)

This configuration allows Atlas to automatically scale up during traffic spikes while preventing costs from scaling beyond M80 tier limits.

## 7. Caveats & Risk Factors

**Factors that could change this recommendation:**

1. **Index Growth Beyond Projections:** Current estimate assumes 25% index-to-data ratio. Complex compound indexes or additional query patterns could increase this significantly.

2. **Working Set Expansion:** If more than 20% of data becomes "hot" (actively accessed), memory requirements will increase, potentially necessitating higher tiers.

3. **Write Pattern Changes:** Sustained write loads exceeding 56 writes/sec could require vertical scaling or additional sharding for I/O distribution.

4. **Data Retention Policy Changes:** Any increase beyond the 5TB retention policy will require immediate re-evaluation of shard count and storage allocation.

5. **Missing Query Pattern Analysis:** Without specific query shapes, index recommendations are conservative. Actual index requirements may differ significantly.

6. **Connection Pool Growth:** While current collection count suggests low connection requirements, application scaling could change this assumption.

## 8. Testing & Validation Plan

**Load Testing Approach:**
1. **Data Loading:** Load representative 2.5TB dataset (50% of target) with realistic document distribution
2. **Write Testing:** Simulate 56 writes/sec sustained load for 2-hour periods
3. **Read Testing:** Generate mixed query patterns at 84 reads/sec with realistic selectivity
4. **Scaling Testing:** Test storage auto-scaling behavior by approaching 90% disk utilization

**Critical Monitoring Thresholds:**
- **CPU Utilization:** Warn >60%, Critical >80%
- **Disk Latency:** Target <10ms average, Alert >20ms
- **WiredTiger Cache Dirty:** Warn >5%, Critical >20%
- **Replication Lag:** Warn >10 seconds, Critical >60 seconds
- **Storage Utilization:** Warn >80%, Critical >90%
- **Query Targeting:** Monitor for ratios >100 (indicating inefficient queries)
- **Connections Used:** Monitor against tier-specific limits

**Validation Criteria:**
- CPU remains below 60% during sustained load
- Query response times under 100ms for 95th percentile
- Replication lag under 5 seconds during peak writes
- Storage auto-scaling triggers properly before 90% utilization

## 9. Recommendations & Next Steps

**Final Recommendation:** **Option B (2-Shard M50)** provides the optimal balance of cost, performance, and operational stability. The 68% storage utilization ensures adequate headroom while the distributed architecture enables linear scaling for future growth.

**Deployment Sequence:**
1. **Development Environment:** Deploy single M40 for application development and testing
2. **Pre-Production:** Deploy recommended 2-shard M50 configuration for performance validation
3. **Production:** Deploy identical configuration with comprehensive monitoring and alerting

**Additional Services to Configure:**
- **Performance Advisor:** Enable for query optimization recommendations
- **Real-Time Performance Panel:** Configure for production monitoring
- **Custom Alert Policies:** Set up monitoring thresholds listed above
- **Backup Policies:** Configure retention periods and cross-region backup distribution
- **Maintenance Windows:** Schedule during low-traffic periods

**Follow-up Actions Required:**
1. **Index Strategy Session:** Review specific query patterns to optimize index recommendations beyond the conservative 25% estimate
2. **Security Review:** Confirm BYOK key management procedures and regional compliance requirements  
3. **Network Configuration:** Plan VPC peering or private endpoints for secure connectivity
4. **Application Driver Updates:** Ensure application uses MongoDB 8.0 compatible drivers
5. **Monitoring Integration:** Configure Atlas metrics integration with existing monitoring systems

This configuration positions your e-commerce platform for reliable operation while providing clear scaling paths as business requirements evolve.