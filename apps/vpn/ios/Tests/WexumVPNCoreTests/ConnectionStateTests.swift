import XCTest
@testable import WexumVPNCore

final class ConnectionStateTests: XCTestCase {
    func testStartsWithoutConfigurationOrProtection() {
        let state = ConnectionState()
        XCTAssertEqual(state.phase, .noConfiguration)
        XCTAssertFalse(state.hasConfiguration)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testNativeConnectedCannotClaimProtection() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.nativeStatus(.connected))
        XCTAssertEqual(state.phase, .connectedUnverified)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testNativeStatusBeforeConfigurationIsIgnored() {
        var state = ConnectionState()
        state.apply(.nativeStatus(.connected))
        XCTAssertEqual(state.phase, .noConfiguration)
    }

    func testNativeStatusesMapWithoutInventingSuccess() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        let cases: [(NativeVPNStatus, ConnectionPhase)] = [
            (.invalid, .disconnected),
            (.disconnected, .disconnected),
            (.connecting, .connecting),
            (.connected, .connectedUnverified),
            (.reasserting, .reconnecting),
            (.disconnecting, .disconnecting)
        ]
        for (status, expected) in cases {
            state.apply(.nativeStatus(status))
            XCTAssertEqual(state.phase, expected)
            XCTAssertFalse(state.isProtectionVerified)
        }
    }

    func testNetworkLossInterruptsAndIgnoresConnectedCallbacks() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.nativeStatus(.connected))
        state.apply(.networkLost)
        state.apply(.nativeStatus(.connected))
        XCTAssertEqual(state.phase, .interrupted)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testNetworkRestorationNeedsFreshNativeState() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.networkLost)
        state.apply(.networkRestored)
        XCTAssertEqual(state.phase, .disconnected)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testConfigurationRemovalRevokesDisplayStatus() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.nativeStatus(.connected))
        state.apply(.configurationMissing)
        XCTAssertEqual(state.phase, .noConfiguration)
        XCTAssertFalse(state.hasConfiguration)
    }

    func testPermissionDeniedFailsClosed() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.permissionDenied)
        XCTAssertEqual(state.phase, .error)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testObserverFailureFailsClosed() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.observerFailed)
        XCTAssertEqual(state.phase, .error)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testProcessRestartDoesNotRestorePriorConnection() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.nativeStatus(.connected))
        state.apply(.processRestarted)
        XCTAssertEqual(state.phase, .noConfiguration)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testRefreshImmediatelyDropsStaleNativeConnectedStatus() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.nativeStatus(.connected))
        state.apply(.configurationRefreshStarted)
        XCTAssertEqual(state.phase, .checkingConfiguration)
        XCTAssertFalse(state.hasConfiguration)
        XCTAssertFalse(state.isProtectionVerified)
        // Preferences callback never arrives; a late native status cannot revive it.
        state.apply(.nativeStatus(.connected))
        XCTAssertEqual(state.phase, .checkingConfiguration)
        state.apply(.configurationMissing)
        XCTAssertEqual(state.phase, .noConfiguration)
    }

    func testRefreshAfterResumeRequiresNewConfigurationAndNativeStatus() {
        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.nativeStatus(.connected))
        state.apply(.configurationRefreshStarted)
        state.apply(.configurationFound)
        XCTAssertEqual(state.phase, .disconnected)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testPendingPreferencesTimeoutInvalidatesLateCallback() {
        var epoch = ObservationEpoch()
        let pending = epoch.beginRefresh()
        XCTAssertTrue(epoch.expirePending(pending))
        XCTAssertFalse(epoch.isCurrent(pending))
        XCTAssertFalse(epoch.activate(pending))
        XCTAssertFalse(epoch.permitsStatus(for: pending))

        var state = ConnectionState()
        state.apply(.configurationFound)
        state.apply(.nativeStatus(.connected))
        state.apply(.configurationRefreshStarted)
        state.apply(.observerFailed)
        XCTAssertEqual(state.phase, .error)
        XCTAssertFalse(state.isProtectionVerified)
    }

    func testTimeoutCannotInvalidateCompletedOrSupersededRefresh() {
        var epoch = ObservationEpoch()
        let old = epoch.beginRefresh()
        let current = epoch.beginRefresh()
        XCTAssertFalse(epoch.expirePending(old))
        XCTAssertTrue(epoch.isCurrent(current))
        XCTAssertTrue(epoch.activate(current))
        XCTAssertFalse(epoch.expirePending(current))
        XCTAssertTrue(epoch.permitsStatus(for: current))
    }

    func testObservationRejectsStatusBeforeActivation() {
        var epoch = ObservationEpoch()
        let ticket = epoch.beginRefresh()
        XCTAssertFalse(epoch.permitsStatus(for: ticket))
        XCTAssertFalse(epoch.permitsStatus(for: nil))
        XCTAssertTrue(epoch.activate(ticket))
        XCTAssertTrue(epoch.permitsStatus(for: ticket))
    }

    func testSupersededConfigurationResponseCannotActivate() {
        var epoch = ObservationEpoch()
        let oldTicket = epoch.beginRefresh()
        let latestTicket = epoch.beginRefresh()
        XCTAssertFalse(epoch.isCurrent(oldTicket))
        XCTAssertFalse(epoch.activate(oldTicket))
        XCTAssertFalse(epoch.permitsStatus(for: oldTicket))
        XCTAssertTrue(epoch.activate(latestTicket))
        XCTAssertTrue(epoch.permitsStatus(for: latestTicket))
    }

    func testNetworkSwitchInvalidatesStatusAndPendingResponse() {
        var epoch = ObservationEpoch()
        let previous = epoch.beginRefresh()
        XCTAssertTrue(epoch.activate(previous))
        epoch.invalidate()
        XCTAssertFalse(epoch.permitsStatus(for: previous))
        XCTAssertFalse(epoch.activate(previous))
        let onNewPath = epoch.beginRefresh()
        XCTAssertTrue(epoch.activate(onNewPath))
        XCTAssertFalse(epoch.permitsStatus(for: previous))
        XCTAssertTrue(epoch.permitsStatus(for: onNewPath))
    }

    func testFailedReloadDoesNotReuseOldStatusTicket() {
        var epoch = ObservationEpoch()
        let oldTicket = epoch.beginRefresh()
        XCTAssertTrue(epoch.activate(oldTicket))
        _ = epoch.beginRefresh()
        XCTAssertFalse(epoch.permitsStatus(for: oldTicket))
        epoch.invalidate() // loader failure or missing configuration
        XCTAssertFalse(epoch.permitsStatus(for: oldTicket))
    }

    func testRepeatedInvalidateNeverRestoresStatus() {
        var epoch = ObservationEpoch()
        let ticket = epoch.beginRefresh()
        XCTAssertTrue(epoch.activate(ticket))
        for _ in 0..<100 {
            epoch.invalidate()
            XCTAssertFalse(epoch.permitsStatus(for: ticket))
        }
    }

    func testOfflineWithoutConfigurationDoesNotClaimInterruption() {
        var state = ConnectionState()
        state.apply(.networkLost)
        XCTAssertEqual(state.phase, .noConfiguration)
    }
}
