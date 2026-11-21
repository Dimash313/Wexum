package com.ihsansoft.wexumvpn

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConnectionStateMachineTest {
    @Test fun startsDisconnected() {
        assertEquals(ConnectionPhase.DISCONNECTED, ConnectionStateMachine().current().phase)
    }

    @Test fun consentIsNotConnection() {
        val machine = ConnectionStateMachine()
        machine.requestConsent()
        machine.permissionGranted()
        assertEquals(ConnectionPhase.READY, machine.current().phase)
    }

    @Test fun deniedPermissionFailsClosed() {
        val machine = ConnectionStateMachine()
        machine.requestConsent()
        machine.permissionDenied()
        assertEquals(ConnectionFailure.PERMISSION_DENIED, machine.current().failure)
        assertFalse(machine.beginConnecting())
    }

    @Test fun cannotConnectWithoutPermission() {
        val machine = ConnectionStateMachine()
        assertFalse(machine.beginConnecting())
        assertEquals(ConnectionPhase.DISCONNECTED, machine.current().phase)
    }

    @Test fun proofCannotArriveBeforeConnectionStarts() {
        val machine = ConnectionStateMachine()
        assertFalse(machine.tunnelVerified(TunnelEvidence(true, true, true, true)))
        assertEquals(ConnectionPhase.DISCONNECTED, machine.current().phase)
    }

    @Test fun eachMissingVerificationFailsClosed() {
        val proofs = listOf(
            TunnelEvidence(false, true, true, true),
            TunnelEvidence(true, false, true, true),
            TunnelEvidence(true, true, false, true),
            TunnelEvidence(true, true, true, false),
        )
        for (proof in proofs) {
            val machine = ConnectionStateMachine()
            machine.permissionGranted()
            assertTrue(machine.beginConnecting())
            assertFalse(machine.tunnelVerified(proof))
            assertEquals(ConnectionFailure.UNVERIFIED_TUNNEL, machine.current().failure)
        }
    }

    @Test fun completeEvidenceIsOnlyTheFutureEngineStateGate() {
        val machine = ConnectionStateMachine()
        machine.permissionGranted()
        assertTrue(machine.beginConnecting())
        assertTrue(machine.tunnelVerified(TunnelEvidence(true, true, true, true)))
        assertEquals(ConnectionPhase.PROTECTED, machine.current().phase)
    }

    @Test fun networkLossRemovesProtectedStatus() {
        val machine = ConnectionStateMachine()
        machine.permissionGranted()
        machine.beginConnecting()
        machine.tunnelVerified(TunnelEvidence(true, true, true, true))
        machine.networkLost()
        assertEquals(ConnectionPhase.INTERRUPTED, machine.current().phase)
    }

    @Test fun revokeRemovesProtectedStatus() {
        val machine = ConnectionStateMachine()
        machine.permissionGranted()
        machine.beginConnecting()
        machine.tunnelVerified(TunnelEvidence(true, true, true, true))
        machine.revoked()
        assertEquals(ConnectionPhase.DISCONNECTED, machine.current().phase)
    }

    @Test fun engineUnavailabilityNeverReportsProtection() {
        val machine = ConnectionStateMachine()
        machine.permissionGranted()
        machine.transportUnavailable()
        assertEquals(ConnectionSnapshot(ConnectionPhase.ERROR, ConnectionFailure.ENGINE_UNAVAILABLE), machine.current())
    }

    @Test fun disconnectClearsError() {
        val machine = ConnectionStateMachine()
        machine.transportUnavailable()
        machine.disconnect()
        assertEquals(ConnectionSnapshot(ConnectionPhase.DISCONNECTED), machine.current())
    }
}
