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

    func testOfflineWithoutConfigurationDoesNotClaimInterruption() {
        var state = ConnectionState()
        state.apply(.networkLost)
        XCTAssertEqual(state.phase, .noConfiguration)
    }
}
