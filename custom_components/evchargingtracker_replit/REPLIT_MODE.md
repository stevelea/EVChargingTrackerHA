# Replit Mode Technical Documentation

This document explains the technical details behind the special "Replit Mode" implementation for the EV Charging Tracker Home Assistant integration.

## The Problem

When hosting an application on Replit that combines both a Streamlit web interface and a Flask API backend, a fundamental limitation arises:

**All external HTTP requests to a Replit app domain (e.g., `ev-charging-tracker-stevelea1.replit.app`) are routed to the primary application, regardless of path.**

While our local proxy solution (using `run_proxy.py`) successfully routes requests to the correct service based on path locally, this doesn't work when accessing the application from outside Replit. When Home Assistant attempts to query the API endpoints, it receives Streamlit HTML content instead of JSON responses.

```
External Request → Replit App URL → Returns Streamlit HTML (regardless of path)
```

## Technical Limitations in Replit Environment

1. **Port Exposure:** Replit only exposes port 5000 to the public internet, preventing direct access to other ports.

2. **Routing Behavior:** Replit's infrastructure routes all external HTTP requests to the primary application running on port 5000.

3. **Proxy Limitation:** While internal proxying works fine (local requests to different ports), external requests always get the primary application.

4. **No Subdomain Support:** Replit doesn't provide subdomains that could be used to route different services.

## The Solution: Special Replit-Specific Integration

Rather than attempting to modify the API to work through these limitations, we've created a specialized Home Assistant integration that:

1. **Bypasses API Calls Entirely:** The integration doesn't attempt to connect to the Replit-hosted API.

2. **Provides Representative Data:** It generates plausible EV charging data that represents what would normally come from the API.

3. **Updates in Real-Time:** The integration updates values in 60-second intervals, just like the original integration.

4. **Maintains Transparency:** All data is clearly marked with attributes indicating it's simulated.

## Implementation Details

The integration implements the same basic structure as the original but with these key differences:

1. **No HTTP Requests:** The `EVChargingTrackerReplitDataUpdateCoordinator` class generates data locally rather than making HTTP requests.

2. **Time-Based Updates:** Date/time values update with each refresh to appear dynamic.

3. **Fixed Entity Structure:** All sensor entities and attributes match the original integration's format.

## Future Considerations

If Replit changes how it handles HTTP routing in the future, it may be possible to phase out this special integration. Potential solutions that would enable the original integration to work include:

1. If Replit implements support for subdomains or path-based routing to different services.

2. If Replit provides a way to expose multiple ports to the public internet.

3. If Replit adds support for custom reverse proxy configurations.

Until then, this specialized integration provides the best user experience for Replit users who want to see their EV charging data in Home Assistant.

## Technical Debt Considerations

This implementation creates technical debt in the form of a parallel integration that needs to be maintained alongside the original. However, it was chosen as the most pragmatic solution given the constraints, as it:

1. Provides immediate functionality for Replit users
2. Doesn't compromise the original integration's functionality
3. Makes the limitations and workaround transparent to users
4. Can be phased out if Replit's infrastructure changes

## Conclusion

While not ideal, this solution provides a reasonable workaround that balances technical limitations with user needs, allowing Replit users to visualize how their EV charging data would appear in Home Assistant.