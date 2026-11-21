import Combine
import Foundation
import Network
import NetworkExtension

/// Read-only OS observer. Starting a tunnel requires audited grants and a real provider.
@MainActor
final class ConnectionStore: ObservableObject {
    @Published private(set) var state = ConnectionState()

    private var manager: NETunnelProviderManager?
    private let networkMonitor = NWPathMonitor()
    private var statusObserver: NSObjectProtocol?
    private var refreshGeneration = 0

    init() {
        networkMonitor.pathUpdateHandler = { [weak self] path in
            Task { @MainActor [weak self] in
                guard let self else { return }
                let available = path.status == .satisfied
                self.state.apply(available ? .networkRestored : .networkLost)
                if available { self.refreshStatus() }
            }
        }
        networkMonitor.start(queue: DispatchQueue(label: "com.ihsansoft.wexumvpn.network-status"))
        statusObserver = NotificationCenter.default.addObserver(
            forName: .NEVPNStatusDidChange, object: nil, queue: .main
        ) { [weak self] notification in
            Task { @MainActor [weak self] in
                guard let self, let manager = self.manager else { return }
                guard let source = notification.object as AnyObject?, source === manager.connection else { return }
                self.refreshStatus()
            }
        }
    }

    func refreshConfiguration() {
        refreshGeneration += 1
        let generation = refreshGeneration
        NETunnelProviderManager.loadAllFromPreferences { [weak self] managers, error in
            Task { @MainActor [weak self] in
                guard let self, generation == self.refreshGeneration else { return }
                guard error == nil, let managers else {
                    self.manager = nil
                    self.state.apply(.observerFailed)
                    return
                }
                guard managers.count <= 1 else {
                    // Ambiguous profiles are not silently chosen.
                    self.manager = nil
                    self.state.apply(.observerFailed)
                    return
                }
                guard let manager = managers.first else {
                    self.manager = nil
                    self.state.apply(.configurationMissing)
                    return
                }
                self.manager = manager
                self.state.apply(.configurationFound)
                self.refreshStatus()
            }
        }
    }

    private func refreshStatus() {
        guard let manager else { return }
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
