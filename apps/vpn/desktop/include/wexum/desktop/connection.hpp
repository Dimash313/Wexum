#pragma once

#include <cstdint>

namespace wexum::desktop {

enum class ConnectionState {
  Disconnected,
  Connecting,
  Protected,
  Interrupted,
  Disconnecting,
  Error,
};

enum class EngineEventKind { Connected, Interrupted, Disconnected, Failed };
enum class EngineAction { None, Start, Stop };

struct EngineCommand {
  EngineAction action{EngineAction::None};
  std::uint64_t attempt{0};
};

// Must be supplied only by a future authenticated policy/engine adapter.
// These booleans are NOT an authentication mechanism.
struct TrustedPolicy {
  bool entitlement_valid{false};
  bool device_valid{false};
  bool engine_channel_authenticated{false};
};

// Events must be validated by the privileged service transport BEFORE dispatch.
struct VerifiedEngineEvent {
  EngineEventKind kind;
  std::uint64_t attempt;
  std::uint64_t sequence;
};

class ConnectionMachine final {
 public:
  [[nodiscard]] ConnectionState state() const noexcept { return state_; }
  [[nodiscard]] std::uint64_t attempt() const noexcept { return attempt_; }
  [[nodiscard]] bool can_connect() const noexcept;

  // A revoked grant cannot keep the UI in Protected state.
  [[nodiscard]] EngineCommand update_trusted_policy(TrustedPolicy policy) noexcept;
  [[nodiscard]] EngineCommand request_connect() noexcept;
  [[nodiscard]] EngineCommand request_disconnect() noexcept;
  [[nodiscard]] bool observe_verified_engine_event(const VerifiedEngineEvent& event) noexcept;
  void on_engine_channel_lost() noexcept;

 private:
  ConnectionState state_{ConnectionState::Disconnected};
  TrustedPolicy policy_{};
  std::uint64_t attempt_{0};
  std::uint64_t last_sequence_{0};
  // Stop/revocation/channel loss requires verified tunnel-down confirmation.
  bool stop_confirmation_required_{false};
};

}  // namespace wexum::desktop
