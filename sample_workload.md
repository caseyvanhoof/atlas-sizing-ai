# Application: E-Commerce Order Management Platform

## Cloud Provider
- **Provider:** Azure
- **Region:** centralus (primary), eastus (secondary region), eastus2 (third region for high availabilty)

## MongoDB Version
- Target: MongoDB 8.0

## Collections & Schema
- No schema provided, collection information is below.

## Indexes (Planned)
No indexes are created by the customer yet.  I (MongoDB Consultant) have yet to review their specific query shapes to recommmend indexes.  Because of this, lets go with the conservative number of 20% of data size is the index size.


## Estimated Index Sizes
- Lets go with the conservative number of 25% of data size is the index size
- Which would be 20% of 5TB

## Query Patterns
- Not provided at this time. 

### Read Operations (~60% of traffic)
- **No detailed information provided by customer** Customer could only provide read:write ratio but not query shapes provided.

### Write Operations (~40% of traffic)
- **Average write volume** ~50 writes/sec 
- **Peak Write Volume Use Case:** need to write ~400k docs in 2 hours

### Aggregation / Reporting
- Not provided at this time

## Connection Requirements
- Around 10-12 collections was reported by the customer but no other information

## Availability Requirements
- With 3 regions there should be no need for failover / DR as Atlas can handle regional outages
- We just need to consider data corruption at a potential roll back scenario
- This customer has mutli-region backups enabled by default
- Recovery Point Objective (RPO): Unsure
- Recovery Time Objective (RTO): Unsure

## Growth Projections
- Expect to write 450K documents to start, but will increase (no period of time given)
- They would like to keep ~5TB worth of data in MongoDB and then would start archving
- Based on my estimates of 5TB / ((200KB doc size * 450k docs) / 3 for compression ) = ~5 months of active data in MDB
