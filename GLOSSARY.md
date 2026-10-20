# Procurement Decision Support

Shared vocabulary for supplier evaluation, procurement planning and human finalization.
These definitions preserve the accepted V2 baseline; they do not decide which cases are approvable.

## Language

**Planning case**:
A recorded procurement-planning run containing its inputs, supplier evaluations, plans, explanations and sources.
_Avoid_: Purchase Order, approval

**Base case**:
An original planning case against which stress scenarios are compared.
_Avoid_: Stress scenario, approved plan

**Procurement plan**:
A complete allocation of one approved product demand across suppliers, with its cost, exposure and business constraints.
_Avoid_: Supplier ranking, selected offer

**Balanced plan**:
An alternative procurement plan that minimises the largest quantity depending on one supplier, within a cost allowance and without more exposure than the minimum-cost plan.
_Avoid_: Diversification guarantee, risk-free plan

**Order allocation**:
The quantity assigned to each supplier within a procurement plan.
_Avoid_: Supplier score

**Supplier evaluation**:
The assessment of a supplier from documented historical performance characteristics, accompanied by its interpretation and limitations.
_Avoid_: Procurement plan, final decision

**Stress scenario**:
A what-if change to an original planning case's assumptions, producing a separate planning result.
_Avoid_: Refreshed Odoo facts, confirmed business terms

**Final decision**:
The human decision to approve a particular valid saved procurement plan or to make no award.
_Avoid_: Machine recommendation, solver result

**No-award**:
A final decision to place no order from the plans under consideration.
_Avoid_: Approved plan, solver failure

**Approved snapshot**:
The fixed recorded content identifying the approved plan, its planning context and the human decision.
_Avoid_: Latest live state, recalculated plan

**Approved procurement document**:
The PDF representation of an approved snapshot.
_Avoid_: Automatically created Odoo Purchase Order

**Planning reference time**:
The point in time to which the planning inputs and supplier evaluation relate; in a controlled historical demo this is the simulation reference time.
_Avoid_: Approval record time

**Approval record time**:
The time the human final decision was recorded, distinct from the planning reference time.
_Avoid_: Simulation date, proof of current business validity
