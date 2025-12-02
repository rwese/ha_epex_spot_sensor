# Backlog Specifications

This directory contains detailed specifications for planned features and enhancements to the EPEX Spot Sensor integration.

---

## Active Specifications

### ✅ Flexible Duration with Price Tolerance
**Status:** Ready for Implementation  
**Files:**
- `flexible-duration-with-price-tolerance.md` - Complete feature specification
- `DECISIONS-flexible-duration-with-price-tolerance.md` - Finalized design decisions

**Summary:**
Add two complementary features to provide flexible scheduling:
1. **Flexible Duration:** Find optimal intervals "up to X hours" (between min and max duration)
2. **Price Tolerance:** Accept time slots within ±X% of the cheapest price

**Implementation Phases:**
- **Phase 1:** Price Tolerance (2-3 weeks) - Simpler, lower risk
- **Phase 2:** Flexible Duration (3-4 weeks) - More complex
- **Phase 3:** Polish & Optimization (1 week)

**Key Decisions:**
- Price tolerance relative to cheapest slot (not average)
- Stop adding intervals when price exceeds threshold
- Prefer earlier start times when multiple options exist
- Individual slot filtering (not cumulative average)
- Duration entity overrides flexible mode
- Two independent features (can enable either or both)
- Graceful fallback for edge cases
- Performance not a concern due to small data sets

**Next Steps:**
1. Review specifications
2. Begin Phase 1 implementation (Price Tolerance)
3. Create implementation branch
4. Write unit tests alongside code
5. Update documentation

---

## How to Use These Specifications

### For Developers

1. **Read the main specification** (`flexible-duration-with-price-tolerance.md`)
   - Understand current behavior
   - Review proposed features
   - Study algorithm pseudocode
   - Check testing requirements

2. **Review design decisions** (`DECISIONS-flexible-duration-with-price-tolerance.md`)
   - Understand rationale for each choice
   - See configuration examples
   - Review testing strategy
   - Check documentation requirements

3. **Follow implementation phases**
   - Start with Phase 1 (Price Tolerance)
   - Complete testing before moving to Phase 2
   - Maintain backward compatibility

### For Reviewers

1. **Verify completeness**
   - All open questions answered
   - Edge cases considered
   - Testing strategy defined
   - Documentation planned

2. **Check feasibility**
   - Technical approach sound
   - Performance acceptable
   - Backward compatibility maintained
   - User experience clear

3. **Validate decisions**
   - Rationale makes sense
   - Alternatives considered
   - Risks identified and mitigated

---

## Specification Template

When creating new backlog items, include:

1. **Header**
   - Status, Priority, Type, Component, Dates

2. **Summary**
   - Brief overview of the feature

3. **Current Behavior**
   - What exists today
   - Code locations
   - Limitations

4. **Proposed Behavior**
   - Detailed feature description
   - Use cases
   - Examples

5. **Technical Implementation**
   - Configuration changes
   - Algorithm changes
   - Backward compatibility
   - Testing requirements

6. **Design Decisions**
   - Open questions
   - Options considered
   - Final decisions with rationale

7. **Dependencies**
   - Internal and external

8. **Success Criteria**
   - Definition of done

9. **Risks & Mitigations**
   - Identified risks
   - Mitigation strategies

10. **Implementation Phases**
    - Breakdown of work
    - Deliverables per phase

---

## Status Definitions

- **Proposed:** Initial idea, needs research and clarification
- **In Analysis:** Gathering requirements, exploring options
- **Ready for Implementation:** All decisions made, specification complete
- **In Progress:** Implementation underway
- **In Review:** Code complete, under review
- **Done:** Merged and released

---

## Contributing

When adding or updating specifications:

1. Create detailed specification in this directory
2. Use clear, descriptive filenames
3. Include code examples and pseudocode
4. Document all design decisions
5. Consider backward compatibility
6. Define testing requirements
7. Update this README with links

---

**Last Updated:** 2025-12-02
