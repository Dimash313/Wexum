package com.ihsansoft.wexumvpn

import org.junit.Assert.*
import org.junit.Test

class ConnectionStateMachineTest {
    @Test fun permissionApprovalNeverMeansProtected() {
        val state = ConnectionStateMachine()
        val id = state.user.beginConsent()!!
        assertTrue(state.user.resolveConsent(id, true))
        assertEquals(ConnectionPhase.PERMISSION_READY, state.current().phase)
    }

    @Test fun deniedPermissionFailsClosed() {
        val state = ConnectionStateMachine()
        state.user.resolveConsent(state.user.beginConsent()!!, false)
        assertEquals(ConnectionFailure.PERMISSION_DENIED, state.current().failure)
        assertNull(state.service.openEngineSession())
    }

    @Test fun staleConsentReplyIgnoredAfterRevoke() {
        val state = ConnectionStateMachine()
        val old = state.user.beginConsent()!!
        state.service.permissionRevoked()
        assertFalse(state.user.resolveConsent(old, true))
        assertEquals(ConnectionPhase.DISCONNECTED, state.current().phase)
    }

    @Test fun staleConsentReplyIgnoredAfterNextAttempt() {
        val state = ConnectionStateMachine()
        val old = state.user.beginConsent()!!
        state.service.permissionRevoked()
        val current = state.user.beginConsent()!!
        assertFalse(state.user.resolveConsent(old, true))
        assertTrue(state.user.resolveConsent(current, true))
        assertEquals(ConnectionPhase.PERMISSION_READY, state.current().phase)
    }

    @Test fun repeatedConsentRequestsCannotOverlap() {
        val state = ConnectionStateMachine()
        assertNotNull(state.user.beginConsent())
        assertNull(state.user.beginConsent())
    }

    @Test fun failedIntentLaunchNeverBecomesReady() {
        val state = ConnectionStateMachine()
        assertTrue(state.user.consentLaunchFailed(state.user.beginConsent()!!))
        assertEquals(ConnectionFailure.CONSENT_FLOW_FAILED, state.current().failure)
    }

    @Test fun permissionReconciliationOnResumeInvalidatesReady() {
        val state = ConnectionStateMachine()
        state.user.resolveConsent(state.user.beginConsent()!!, true)
        state.user.reconcileOsPermission(false)
        assertEquals(ConnectionPhase.DISCONNECTED, state.current().phase)
        assertEquals(ConnectionFailure.PERMISSION_REVOKED, state.current().failure)
    }

    @Test fun engineCannotStartWithoutPermission() {
        assertNull(ConnectionStateMachine().service.openEngineSession())
    }

    @Test fun staleEngineEventsIgnoredAfterRevoke() {
        val state = ConnectionStateMachine()
        state.user.resolveConsent(state.user.beginConsent()!!, true)
        val session = state.service.openEngineSession()!!
        state.service.onEngineSignal(session, EngineSignal.STARTING)
        state.service.permissionRevoked()
        assertFalse(state.service.onEngineSignal(session, EngineSignal.STARTING))
        assertEquals(ConnectionPhase.DISCONNECTED, state.current().phase)
    }

    @Test fun engineFailureAlwaysClearsSession() {
        val state = ConnectionStateMachine()
        state.user.resolveConsent(state.user.beginConsent()!!, true)
        val session = state.service.openEngineSession()!!
        assertTrue(state.service.onEngineSignal(session, EngineSignal.FAILED))
        assertEquals(ConnectionFailure.ENGINE_FAILED, state.current().failure)
        assertFalse(state.service.onEngineSignal(session, EngineSignal.STARTING))
    }

    @Test fun engineSignalsCannotDeclareConnected() {
        val state = ConnectionStateMachine()
        state.user.resolveConsent(state.user.beginConsent()!!, true)
        val session = state.service.openEngineSession()!!
        for (signal in EngineSignal.values()) {
            state.service.onEngineSignal(session, signal)
            assertNotEquals(ConnectionPhase.PROTECTED, state.current().phase)
        }
    }

    @Test fun serviceCrashClearsStateAndInvalidatesCallbacks() {
        val state = ConnectionStateMachine()
        state.user.resolveConsent(state.user.beginConsent()!!, true)
        val session = state.service.openEngineSession()!!
        state.service.onEngineSignal(session, EngineSignal.STARTING)
        state.service.serviceStopped()
        assertEquals(ConnectionPhase.DISCONNECTED, state.current().phase)
        assertFalse(state.service.onEngineSignal(session, EngineSignal.STARTING))
    }

    @Test fun newProcessStartsDisconnected() {
        val old = ConnectionStateMachine()
        old.user.resolveConsent(old.user.beginConsent()!!, true)
        assertEquals(ConnectionPhase.DISCONNECTED, ConnectionStateMachine().current().phase)
    }

    @Test fun observersSeeServiceChangesAndCanUnsubscribe() {
        val state = ConnectionStateMachine()
        var count = 0
        val subscription = state.observe { count++ }
        assertEquals(1, count)
        state.service.engineUnavailable()
        assertEquals(2, count)
        subscription.close()
        state.service.permissionRevoked()
        assertEquals(2, count)
    }

    @Test fun redundantSignalsDoNotNotifyTwice() {
        val state = ConnectionStateMachine()
        var count = 0
        val sub = state.observe { count++ }
        state.service.serviceStopped()
        assertEquals(1, count)
        sub.close()
    }

    @Test fun interruptedStateCannotPretendProtected() {
        val state = ConnectionStateMachine()
        state.user.resolveConsent(state.user.beginConsent()!!, true)
        val session = state.service.openEngineSession()!!
        state.service.onEngineSignal(session, EngineSignal.STARTING)
        state.service.onEngineSignal(session, EngineSignal.INTERRUPTED)
        assertEquals(ConnectionPhase.INTERRUPTED, state.current().phase)
        state.service.onEngineSignal(session, EngineSignal.STOPPED)
        assertEquals(ConnectionPhase.DISCONNECTED, state.current().phase)
    }
}
