import SwiftUI
import UIKit

struct ConnectionView: View {
    @EnvironmentObject private var store: ConnectionStore

    private var statusKey: LocalizedStringKey {
        switch store.state.phase {
        case .noConfiguration: return "status.noConfiguration"
        case .checkingConfiguration: return "status.checkingConfiguration"
        case .disconnected: return "status.disconnected"
        case .connecting: return "status.connecting"
        case .connectedUnverified: return "status.unverified"
        case .reconnecting: return "status.reconnecting"
        case .disconnecting: return "status.disconnecting"
        case .interrupted: return "status.interrupted"
        case .error: return "status.error"
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 28) {
                Text("app.brand")
                    .font(.system(size: 30, weight: .bold, design: .rounded))
                VStack(alignment: .leading, spacing: 16) {
                    Image(systemName: "shield.lefthalf.filled")
                        .font(.system(size: 56, weight: .ultraLight))
                        .accessibilityHidden(true)
                    Text(statusKey)
                        .font(.title2.weight(.semibold))
                        .accessibilityAddTraits(.isHeader)
                    Text("status.disclaimer")
                        .font(.body)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(24)
                .background(Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 24))

                Button { store.refreshConfiguration() } label: {
                    Text("action.refresh")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                }
                .buttonStyle(.borderedProminent)
                .tint(.primary)
                .accessibilityHint(Text("accessibility.refreshHint"))

                Text("action.connectUnavailable")
                    .font(.footnote)
                    .foregroundStyle(.secondary)

                Divider()
                Text("privacy.disclosureTitle")
                    .font(.headline)
                Text("privacy.disclosure")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .padding(24)
        }
        .background(Color(uiColor: .systemBackground))
        .onAppear { store.refreshConfiguration() }
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
            store.refreshConfiguration()
        }
    }
}
