/// OS connection status is not evidence of a verified, traffic-protecting tunnel.
public enum NativeVPNStatus: Equatable, Sendable {
    case invalid, disconnected, connecting, connected, reasserting, disconnecting
}

public enum ConnectionPhase: Equatable, Sendable {
    case noConfiguration
    case disconnected
    case connecting
    case connectedUnverified
    case reconnecting
    case disconnecting
    case interrupted
    case error
}

public enum ConnectionEvent: Equatable, Sendable {
    case configurationFound
    case configurationMissing
    case nativeStatus(NativeVPNStatus)
    case networkLost
    case networkRestored
    case permissionDenied
    case observerFailed
    case processRestarted
}

/// UI-only snapshot; never grants access, enables a VPN, or proves packet protection.
public struct ConnectionState: Equatable, Sendable {
    public private(set) var phase: ConnectionPhase = .noConfiguration
    public private(set) var hasConfiguration = false
    public private(set) var isNetworkAvailable = true

    public init() {}

    public mutating func apply(_ event: ConnectionEvent) {
        switch event {
        case .configurationMissing, .processRestarted:
            hasConfiguration = false
            phase = .noConfiguration
        case .configurationFound:
            hasConfiguration = true
            phase = isNetworkAvailable ? .disconnected : .interrupted
        case .nativeStatus(let status):
            guard hasConfiguration else {
                phase = .noConfiguration
                return
            }
            guard isNetworkAvailable else {
                phase = .interrupted
                return
            }
            switch status {
            case .invalid, .disconnected: phase = .disconnected
            case .connecting: phase = .connecting
            case .connected: phase = .connectedUnverified
            case .reasserting: phase = .reconnecting
            case .disconnecting: phase = .disconnecting
            }
        case .networkLost:
            isNetworkAvailable = false
            phase = hasConfiguration ? .interrupted : .noConfiguration
        case .networkRestored:
            isNetworkAvailable = true
            // Never resurrect a potentially stale connected status after path recovery.
            phase = hasConfiguration ? .disconnected : .noConfiguration
        case .permissionDenied, .observerFailed:
            phase = .error
        }
    }

    /// Protection is intentionally unavailable until an audited engine/verifier exists.
    public var isProtectionVerified: Bool { false }
}
