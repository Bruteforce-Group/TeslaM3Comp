# Testing Guide for Tesla Model 3 Raspberry Pi 5 Integration

This document outlines the testing procedures to verify the proper functioning of the containerized Tesla Model 3 Raspberry Pi 5 integration system.

## Prerequisites

- Fully deployed system following the DEPLOYMENT.md guide
- Test images for license plate recognition
- Access to the web interface
- OBD-II adapter connected (if testing vehicle data)
- Camera connected (if testing live camera feed)

## Test Plan

### 1. System Startup Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| ST-01 | Start all containers with `docker-compose up -d` | All containers start successfully | ⬜ |
| ST-02 | Check container status with `docker-compose ps` | All containers show "Up" status | ⬜ |
| ST-03 | View logs for each container | No critical errors in logs | ⬜ |
| ST-04 | Restart the system | All containers restart automatically | ⬜ |
| ST-05 | Check system dashboard | All services show as connected | ⬜ |

### 2. Web Interface Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| WI-01 | Access web interface at http://localhost | Dashboard loads correctly | ⬜ |
| WI-02 | Navigate between all pages | All pages load without errors | ⬜ |
| WI-03 | Check responsive design | UI adapts to different screen sizes | ⬜ |
| WI-04 | Test dashboard refresh | Data updates in real-time | ⬜ |
| WI-05 | Check system status indicators | Status indicators reflect actual system state | ⬜ |

### 3. LLM Integration Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| LLM-01 | Check LLM status | LLM service shows as running | ⬜ |
| LLM-02 | Test local Llama 3 inference | Receives appropriate response | ⬜ |
| LLM-03 | Test with complex query | Handles complex queries correctly | ⬜ |
| LLM-04 | Test cloud fallback (if configured) | Falls back to cloud API when needed | ⬜ |
| LLM-05 | Test API key configuration | Can update API keys through UI | ⬜ |
| LLM-06 | Test performance under load | Maintains stability under multiple requests | ⬜ |

### 4. Camera and OpenCV Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| CAM-01 | View live camera feed | Camera feed displays in UI | ⬜ |
| CAM-02 | Test image capture | Can capture and save images | ⬜ |
| CAM-03 | Test license plate recognition with sample images | Correctly identifies license plates | ⬜ |
| CAM-04 | Test license plate recognition with live feed | Identifies plates in real-time | ⬜ |
| CAM-05 | Test recognition accuracy | Achieves >80% accuracy on test set | ⬜ |
| CAM-06 | Test performance under different lighting | Works in various lighting conditions | ⬜ |

### 5. OBD Integration Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| OBD-01 | Check OBD connection status | Shows connected when adapter is plugged in | ⬜ |
| OBD-02 | View vehicle data | Displays vehicle data in UI | ⬜ |
| OBD-03 | Test data logging | Data is logged to database | ⬜ |
| OBD-04 | Test reconnection | Automatically reconnects after disconnection | ⬜ |
| OBD-05 | Test data accuracy | Data matches vehicle instruments | ⬜ |

### 6. Database Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| DB-01 | Check database connection | Database shows as connected | ⬜ |
| DB-02 | Test data storage | Data is properly stored and retrievable | ⬜ |
| DB-03 | Test data persistence | Data persists after system restart | ⬜ |
| DB-04 | Test database performance | Queries complete in reasonable time | ⬜ |
| DB-05 | Test backup functionality | Can backup and restore database | ⬜ |

### 7. Security Analysis Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| SEC-01 | Test security event detection | Detects simulated security events | ⬜ |
| SEC-02 | Test alert system | Generates alerts for security events | ⬜ |
| SEC-03 | Test event logging | Security events are logged to database | ⬜ |
| SEC-04 | Test false positive rate | Low false positive rate on normal images | ⬜ |
| SEC-05 | Test sensitivity configuration | Can adjust detection sensitivity | ⬜ |

### 8. Performance Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| PERF-01 | Monitor CPU usage | CPU usage remains under 80% | ⬜ |
| PERF-02 | Monitor memory usage | Memory usage remains under limits | ⬜ |
| PERF-03 | Test system under load | System remains stable under load | ⬜ |
| PERF-04 | Test long-running stability | System stable after 24 hours | ⬜ |
| PERF-05 | Test thermal management | Temperature remains in safe range | ⬜ |

### 9. Monitoring Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| MON-01 | Access Prometheus interface | Prometheus UI accessible | ⬜ |
| MON-02 | Access Grafana dashboard | Grafana dashboard loads correctly | ⬜ |
| MON-03 | Check metrics collection | Metrics are being collected | ⬜ |
| MON-04 | Test dashboard functionality | Dashboards display real-time data | ⬜ |
| MON-05 | Test alerting (if configured) | Alerts trigger appropriately | ⬜ |

### 10. Integration Tests

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| INT-01 | Test end-to-end plate recognition workflow | Complete workflow functions correctly | ⬜ |
| INT-02 | Test data flow between services | Data flows correctly between services | ⬜ |
| INT-03 | Test system recovery after service failure | System recovers automatically | ⬜ |
| INT-04 | Test external storage integration | Can use external storage | ⬜ |
| INT-05 | Test Tailscale VPN integration | Remote access works via VPN | ⬜ |

## Test Execution

1. For each test, mark the status as:
   - ✅ Pass
   - ❌ Fail
   - ⚠️ Partial Pass
   - ⬜ Not Tested

2. For any failed tests, document:
   - Detailed description of the issue
   - Steps to reproduce
   - Error messages or logs
   - Screenshots if applicable

3. After addressing issues, retest failed items

## Performance Benchmarks

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| LLM inference time | <5s | | ⬜ |
| Plate recognition accuracy | >80% | | ⬜ |
| Plate recognition time | <2s | | ⬜ |
| System boot time | <60s | | ⬜ |
| UI response time | <1s | | ⬜ |
| CPU usage (idle) | <20% | | ⬜ |
| CPU usage (active) | <80% | | ⬜ |
| Memory usage | <6GB | | ⬜ |
| Storage usage | <16GB | | ⬜ |

## Test Data

- Sample license plate images are located in `/home/ubuntu/tesla_model3_rpi_project/docker/test_data/plates/`
- Test scripts are located in `/home/ubuntu/tesla_model3_rpi_project/docker/test_scripts/`
- Performance testing tools are located in `/home/ubuntu/tesla_model3_rpi_project/docker/test_tools/`

## Automated Testing

Run the automated test suite with:

```bash
cd /home/ubuntu/tesla_model3_rpi_project/docker
./run_tests.sh
```

This will execute basic functionality tests and generate a report in the `test_results` directory.

## Reporting Issues

Document any issues found during testing in the GitHub issue tracker or in the `ISSUES.md` file with the following information:

1. Test ID and description
2. Steps to reproduce
3. Expected vs. actual results
4. System configuration
5. Logs or error messages
6. Screenshots if applicable

## Final Verification Checklist

- [ ] All critical tests pass
- [ ] System performs within benchmark targets
- [ ] Documentation is accurate and complete
- [ ] All containers start and run correctly
- [ ] Web interface is fully functional
- [ ] Data persistence works correctly
- [ ] System recovers from failures
- [ ] Monitoring is properly configured
- [ ] Security measures are in place
- [ ] Backup and restore procedures work
