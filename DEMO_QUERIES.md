# Complex Demo Queries for Omni-Retail Multi-Agent Orchestrator

These queries are designed to test the system's ability to handle complex, multi-agent scenarios with clear, unambiguous answers based on the seeded database.

## Query 1: Order Tracking with Support Ticket Status
**Query:** "I ordered a Gaming Monitor last week (OrderID 1). Where is my package and do I have any open support tickets?"

**Expected Flow:**
1. **ShopCore Agent**: Find order details for OrderID 1 (Gaming Monitor)
   - Order Status: "Delivered"
   - Order Date: 7 days ago
2. **ShipStream Agent**: Find shipment for OrderID 1
   - Tracking Number: TRK001
   - Status: "Delivered" (consistent with order)
   - Estimated Arrival: Past date (already delivered)
3. **CareDesk Agent**: Find tickets for UserID 1 (from order)
   - Check for open tickets related to OrderID 1

**Expected Answer:** 
- Order 1 (Gaming Monitor) was delivered
- Tracking: TRK001, Status: Delivered
- Support ticket status (if any)

**Why it's complex:** Requires 3 agents, cross-database joins via OrderID and UserID, and status consistency validation.

---

## Query 2: Premium User Order History with Payment and Satisfaction
**Query:** "I'm a premium user with email alice@example.com. Show me my last order, how I paid for it, and if I left a satisfaction rating."

**Expected Flow:**
1. **ShopCore Agent**: Find user by email "alice@example.com"
   - UserID: 1, PremiumStatus: 1 (premium)
   - Find last order for UserID 1
   - Get OrderID, ProductID, OrderDate, Status
2. **PayGuard Agent**: Find payment information
   - Find wallet for UserID 1
   - Find transaction for the OrderID
   - Get payment method details
3. **CareDesk Agent**: Find satisfaction survey
   - Find tickets for UserID 1
   - Find surveys linked to tickets
   - Check if survey exists for the order

**Expected Answer:**
- User: Alice Johnson (Premium)
- Last Order: OrderID, Product, Date, Status
- Payment: Transaction details, Payment method
- Satisfaction: Survey rating (if exists)

**Why it's complex:** Requires all 4 agents, email-based user lookup, premium status validation, and cross-referencing multiple relationships.

---

## Query 3: Returned Order Refund Status and Tracking
**Query:** "I returned my Wireless Headphones (OrderID 4). Has my refund been processed and what's the status of the return shipment?"

**Expected Flow:**
1. **ShopCore Agent**: Find order details for OrderID 4
   - Product: Wireless Headphones (ProductID 2)
   - Status: "Returned"
   - UserID: 4
2. **ShipStream Agent**: Find return shipment
   - Shipment for OrderID 4
   - Status: "Returned"
   - Tracking information
3. **PayGuard Agent**: Find refund transaction
   - Find wallet for UserID 4
   - Find refund transaction for OrderID 4
   - Transaction Type: "Refund"
   - Amount and status

**Expected Answer:**
- Order 4 (Wireless Headphones) - Status: Returned
- Return Shipment: Tracking number, Status
- Refund: Transaction details, Amount, Status

**Why it's complex:** Requires 3 agents, handles return/refund workflow, validates refund transaction exists, and checks return shipment status.

---

## Additional Test Queries (Simpler but Valid)

### Query 4: Product Availability Check
**Query:** "Do you have any Gaming Monitors in stock? Show me the price and recent orders."

**Expected Flow:**
1. **ShopCore Agent**: 
   - Find product "Gaming Monitor" (ProductID 1)
   - Get price: $299.99
   - Find recent orders for this product

**Expected Answer:**
- Product: Gaming Monitor, Price: $299.99
- Recent orders list

---

### Query 5: Multi-Order Tracking
**Query:** "I'm user ID 1. Show me all my orders that are currently in transit."

**Expected Flow:**
1. **ShopCore Agent**: Find all orders for UserID 1 with Status "In Transit"
2. **ShipStream Agent**: For each OrderID, get tracking information

**Expected Answer:**
- List of in-transit orders with tracking numbers

---

## Notes for Testing

1. **OrderID 1**: Gaming Monitor, Delivered, UserID 1 (Alice - Premium)
2. **OrderID 3**: Gaming Monitor, In Transit, UserID 3 (Charlie - Premium)
3. **OrderID 4**: Wireless Headphones, Returned, UserID 4 (Diana)
4. **Premium Users**: UserID 1, 3, 5, 7, 10, 12, 15, 17, 20
5. **Email for Alice**: alice@example.com (UserID 1)

All queries are designed to have clear, unambiguous answers based on the seeded data structure.
