package com.ihsansoft.wexumvpn

import org.junit.Assert.*
import org.junit.Test

class ConnectionStateMachineTest {
    private fun granted(state: ConnectionStateMachine) {
        assertTrue(state.user.resolveConsent(state.user.beginConsent()!!, true))
    }

    @Test fun permissionApprovalNeverMeansProtected() {
        val s = ConnectionStateMachine()
        granted(s)
        assertEquals(ConnectionPhase.PERMISSION_READY, s.current().phase)
    }

    @Test fun deniedPermissionFailsClosed() {
        val s = ConnectionStateMachine()
        s.user.resolveConsent(s.user.beginConsent()!!, false)
        assertEquals(ConnectionFailure.PERMISSION_DENIED, s.current().failure)
        assertNull(s.service.openEngineSession(s.service.attach()))
    }

    @Test fun staleConsentReplyIgnoredAfterRevoke() {
        val s = ConnectionStateMachine()
        val old = s.user.beginConsent()!!
        s.service.permissionRevoked()
        assertFalse(s.user.resolveConsent(old, true))
        assertEquals(ConnectionFailure.PERMISSION_REVOKED, s.current().failure)
    }

    @Test fun staleConsentReplyIgnoredAfterNextAttempt() {
        val s = ConnectionStateMachine()
        val old = s.user.beginConsent()!!
        s.service.permissionRevoked()
        val current = s.user.beginConsent()!!
        assertFalse(s.user.resolveConsent(old, true))
        assertTrue(s.user.resolveConsent(current, true))
    }

    @Test fun repeatedConsentRequestsCannotOverlap() {
        val s = ConnectionStateMachine()
        assertNotNull(s.user.beginConsent())
        assertNull(s.user.beginConsent())
    }

    @Test fun failedConsentIntentNeverBecomesReady() {
        val s = ConnectionStateMachine()
        assertTrue(s.user.consentLaunchFailed(s.user.beginConsent()!!))
        assertEquals(ConnectionFailure.CONSENT_FLOW_FAILED, s.current().failure)
    }

    @Test fun resumeInvalidatesRevokedOsGrant() {
        val s = ConnectionStateMachine()
        granted(s)
        s.user.reconcileOsPermission(false)
        assertEquals(ConnectionPhase.DISCONNECTED, s.current().phase)
        assertEquals(ConnectionFailure.PERMISSION_REVOKED, s.current().failure)
    }

    @Test fun noEngineSessionBeforePermissionOrWithoutService() {
        val s = ConnectionStateMachine()
        assertNull(s.service.openEngineSession(5))
        val lease = s.service.attach()
        assertNull(s.service.openEngineSession(lease))
        granted(s)
        assertNull(s.service.openEngineSession(lease + 9))
        assertNotNull(s.service.openEngineSession(lease))
        assertNull(s.service.openEngineSession(lease))
    }

    @Test fun staleEngineSignalsAfterRevokeRejected() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        granted(s)
        val session = s.service.openEngineSession(lease)!!
        assertTrue(s.service.onEngineSignal(session, EngineSignal.STARTING))
        s.service.permissionRevoked()
        assertFalse(s.service.onEngineSignal(session, EngineSignal.FAILED))
        assertFalse(s.service.engineUnavailable(lease))
        assertEquals(ConnectionPhase.DISCONNECTED, s.current().phase)
    }

    @Test fun engineFailureClearsSessionAndPersistsThroughStop() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        granted(s)
        val session = s.service.openEngineSession(lease)!!
        assertTrue(s.service.onEngineSignal(session, EngineSignal.FAILED))
        assertEquals(ConnectionFailure.ENGINE_FAILED, s.current().failure)
        assertFalse(s.service.onEngineSignal(session, EngineSignal.STARTING))
        assertTrue(s.service.serviceStopped(lease))
        assertEquals(ConnectionFailure.ENGINE_FAILED, s.current().failure)
    }

    @Test fun noEngineSignalCanDeclareProtected() {
        for (signal in EngineSignal.values()) {
            val s = ConnectionStateMachine()
            val lease = s.service.attach()
            granted(s)
            val session = s.service.openEngineSession(lease)!!
            s.service.onEngineSignal(session, signal)
            assertNotEquals(ConnectionPhase.PROTECTED, s.current().phase)
        }
    }

    @Test fun serviceStopRejectsOldEngineCallbacks() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        granted(s)
        val session = s.service.openEngineSession(lease)!!
        s.service.onEngineSignal(session, EngineSignal.STARTING)
        assertTrue(s.service.serviceStopped(lease))
        assertEquals(ConnectionPhase.DISCONNECTED, s.current().phase)
        assertFalse(s.service.onEngineSignal(session, EngineSignal.FAILED))
    }

    @Test fun newProcessStartsDisconnected() {
        val old = ConnectionStateMachine()
        granted(old)
        assertEquals(ConnectionPhase.DISCONNECTED, ConnectionStateMachine().current().phase)
    }

    @Test fun observersReceiveServiceEventsAndUnsubscribe() {
        val s = ConnectionStateMachine()
        var notifications = 0
        val subscription = s.observe { notifications++ }
        assertEquals(1, notifications)
        s.service.permissionRevoked()
        assertEquals(2, notifications)
        subscription.close()
        s.service.permissionRevoked()
        assertEquals(2, notifications)
    }

    @Test fun duplicateEventsDoNotNotify() {
        val s = ConnectionStateMachine()
        var count = 0
        val subscription = s.observe { count++ }
        s.service.permissionRevoked()
        s.service.permissionRevoked()
        assertEquals(2, count)
        subscription.close()
    }

    @Test fun interruptedTunnelCannotBeRestartedByStaleStartingEvent() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        granted(s)
        val session = s.service.openEngineSession(lease)!!
        assertFalse(s.service.onEngineSignal(session, EngineSignal.INTERRUPTED))
        assertTrue(s.service.onEngineSignal(session, EngineSignal.STARTING))
        assertFalse(s.service.onEngineSignal(session, EngineSignal.STARTING))
        assertTrue(s.service.onEngineSignal(session, EngineSignal.INTERRUPTED))
        assertFalse(s.service.onEngineSignal(session, EngineSignal.STARTING))
        assertEquals(ConnectionPhase.INTERRUPTED, s.current().phase)
        assertTrue(s.service.onEngineSignal(session, EngineSignal.STOPPED))
        assertEquals(ConnectionPhase.DISCONNECTED, s.current().phase)
    }

    @Test fun lateOnDestroyDoesNotEraseRevocation() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        granted(s)
        s.service.permissionRevoked()
        assertFalse(s.service.serviceStopped(lease))
        assertEquals(ConnectionFailure.PERMISSION_REVOKED, s.current().failure)
    }

    @Test fun staleServiceStopCannotWipeNewServiceOrSession() {
        val s = ConnectionStateMachine()
        val first = s.service.attach()
        granted(s)
        val second = s.service.attach()
        assertFalse(s.service.serviceStopped(first))
        assertNotNull(s.service.openEngineSession(second))
    }

    @Test fun oldConsentAfterServiceShutdownCannotGrantPermission() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        val consent = s.user.beginConsent()!!
        assertTrue(s.service.serviceStopped(lease))
        assertFalse(s.user.resolveConsent(consent, true))
        assertEquals(ConnectionPhase.DISCONNECTED, s.current().phase)
    }

    @Test fun engineUnavailableOnlyForValidLeaseAndState() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        assertFalse(s.service.engineUnavailable(lease))
        granted(s)
        assertFalse(s.service.engineUnavailable(lease + 2))
        assertTrue(s.service.engineUnavailable(lease))
        assertEquals(ConnectionFailure.ENGINE_UNAVAILABLE, s.current().failure)
        assertTrue(s.service.serviceStopped(lease))
        assertEquals(ConnectionFailure.ENGINE_UNAVAILABLE, s.current().failure)
    }

    @Test fun failingObserverCannotBlockRevocationOrHealthyObservers() {
        val failures = mutableListOf<String>()
        val s = ConnectionStateMachine { error -> failures += error.javaClass.simpleName }
        val bad = s.observe { if (s.current().revision > 0) error("UI failure") }
        var healthyCalls = 0
        val healthy = s.observe { healthyCalls++ }
        s.service.permissionRevoked()
        assertEquals(ConnectionFailure.PERMISSION_REVOKED, s.current().failure)
        assertEquals(listOf("IllegalStateException"), failures)
        assertEquals(2, healthyCalls)
        bad.close()
        healthy.close()
    }

    @Test fun initialObserverFailureDoesNotKeepSubscription() {
        val s = ConnectionStateMachine()
        var calls = 0
        try {
            s.observe { calls++; throw IllegalArgumentException("bad subscriber") }
            fail("observer must fail immediately")
        } catch (_: IllegalArgumentException) {
            // Initial callback error is propagated and subscription is removed.
        }
        s.service.permissionRevoked()
        assertEquals(1, calls)
    }

    @Test fun revocationClearsInFlightEngineEvenAfterPermissionRetry() {
        val s = ConnectionStateMachine()
        val lease = s.service.attach()
        granted(s)
        val session = s.service.openEngineSession(lease)!!
        s.service.onEngineSignal(session, EngineSignal.STARTING)
        s.user.reconcileOsPermission(false)
        assertFalse(s.service.onEngineSignal(session, EngineSignal.STOPPED))
        assertEquals(ConnectionFailure.PERMISSION_REVOKED, s.current().failure)
        val newConsent = s.user.beginConsent()!!
        assertTrue(s.user.resolveConsent(newConsent, true))
        assertFalse(s.service.onEngineSignal(session, EngineSignal.STARTING))
    }
}
