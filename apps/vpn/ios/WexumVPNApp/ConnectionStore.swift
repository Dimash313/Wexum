import Combine
import Foundation
import Network
import NetworkExtension

/// Read-only OS observer. Starting a tunnel requires audited grants and a real provider.
@MainActor
final class ConnectionStore: ObservableObject {
    @Published private(set) var state = ConnectionState()

    private var manager: NETunnelProviderManager?
    private var managerTicket: ObservationEpoch.Ticket?
    private var observationEpoch = ObservationEpoch()
    private let networkMonitor = NWPathMonitor()
    private var statusObserver: NSObjectProtocol?

    init() {
        networkMonitor.pathUpdateHandler = { [weak self] path in
            let available = path.status == .satisfied
            Task { @MainActor [weak self] in
                self?.handleNetworkAvailability(available)
            }
        }
        networkMonitor.start(queue: DispatchQueue(label: "com.ihsansoft.wexumvpn.network-status"))
        statusObserver = NotificationCenter.default.addObserver(
            forName: .NEVPNStatusDidChange, object: nil, queue: .main
        ) { [weak self] notification in
            guard let source = notification.object as? NEVPNConnection else { return }
            let sourceIdentity = ObjectIdentifier(source)
            Task { @MainActor [weak self] in
                guard let self, let manager = self.manager else { return }
                guard ObjectIdentifier(manager.connection) == sourceIdentity,
                      self.observationEpoch.permitsStatus(for: self.managerTicket) else { return }
                self.refreshStatus()
            }
        }
    }

    private func handleNetworkAvailability(_ available: Bool) {
        guard available != state.isNetworkAvailable else { return }
        // A completed status read from the previous network must not be reused.
        observationEpoch.invalidate()
        managerTicket = nil
        state.apply(available ? .networkRestored : .networkLost)
        if available { refreshConfiguration() }
    }

    func refreshConfiguration() {
        let ticket = observationEpoch.beginRefresh()
        managerTicket = nil
        manager = nil
        state.apply(.configurationRefreshStarted)
        // A preferences API callback is not guaranteed to arrive. Fail closed after
        // a bounded wait; the epoch rejects any later completion.
        Task { [weak self] in
            try? await Task.sleep(nanoseconds: 10_000_000_000)
            guard let self, self.observationEpoch.expirePending(ticket) else { return }
            self.manager = nil
            self.managerTicket = nil
            self.state.apply(.observerFailed)
        }
        NETunnelProviderManager.loadAllFromPreferences { [weak self] managers, error in
            Task { @MainActor [weak self] in
                guard let self, self.observationEpoch.isCurrent(ticket) else { return }
                guard error == nil, let managers, managers.count <= 1 else {
                    self.manager = nil
                    self.observationEpoch.invalidate()
                    self.state.apply(.observerFailed)
                    return
                }
                guard let manager = managers.first else {
                    self.manager = nil
                    self.observationEpoch.invalidate()
                    self.state.apply(.configurationMissing)
                    return
                }
                guard self.observationEpoch.activate(ticket) else { return }
                self.manager = manager
                self.managerTicket = ticket
                self.state.apply(.configurationFound)
                self.refreshStatus()
            }
        }
    }

    private func refreshStatus() {
        guard observationEpoch.permitsStatus(for: managerTicket), let manager else { return }
        let nativeStatus: NativeVPNStatus
        switch manager.connection.status {
        case .invalid: nativeStatus = .invalid
        case .disconnected: nativeStatus = .disconnected
        case .connecting: nativeStatus = .connecting
        case .connected: nativeStatus = .connected
        case .reasserting: nativeStatus = .reasserting
        case .disconnecting: nativeStatus = .disconnecting
        @unknown default:
            state.apply(.observerFailed)
            return
        }
        state.apply(.nativeStatus(nativeStatus))
    }

    deinit {
        networkMonitor.cancel()
        if let statusObserver { NotificationCenter.default.removeObserver(statusObserver) }
    }
}
