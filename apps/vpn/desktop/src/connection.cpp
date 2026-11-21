#include "wexum/desktop/connection.hpp"

#include <limits>

namespace wexum::desktop {

bool ConnectionMachine::can_connect() const noexcept {
  return state_ == ConnectionState::Disconnected && policy_.entitlement_valid &&
         policy_.device_valid && policy_.engine_channel_authenticated &&
         attempt_ < std::numeric_limits<std::uint64_t>::max();
}

EngineCommand ConnectionMachine::update_trusted_policy(TrustedPolicy policy) noexcept {
  policy_ = policy;
  if ((!policy_.entitlement_valid || !policy_.device_valid ||
       !policy_.engine_channel_authenticated) &&
      (state_ == ConnectionState::Connecting || state_ == ConnectionState::Protected)) {
    state_ = ConnectionState::Interrupted;
    return {EngineAction::Stop, attempt_};
  }
  return {};
}

EngineCommand ConnectionMachine::request_connect() noexcept {
  if (!can_connect()) return {};
  ++attempt_;
  last_sequence_ = 0;
  state_ = ConnectionState::Connecting;
  return {EngineAction::Start, attempt_};
}

EngineCommand ConnectionMachine::request_disconnect() noexcept {
  if (state_ == ConnectionState::Disconnected ||
      state_ == ConnectionState::Disconnecting) return {};
  state_ = ConnectionState::Disconnecting;
  return {EngineAction::Stop, attempt_};
}

bool ConnectionMachine::observe_verified_engine_event(
    const VerifiedEngineEvent& event) noexcept {
  if (!policy_.engine_channel_authenticated || !attempt_ ||
      event.attempt != attempt_ || !event.sequence ||
      event.sequence <= last_sequence_) return false;

  ConnectionState next = state_;
  switch (event.kind) {
    case EngineEventKind::Connected:
      if ((state_ != ConnectionState::Connecting &&
           state_ != ConnectionState::Interrupted) ||
          !policy_.entitlement_valid || !policy_.device_valid) return false;
      next = ConnectionState::Protected;
      break;
    case EngineEventKind::Interrupted:
      if (state_ != ConnectionState::Connecting &&
          state_ != ConnectionState::Protected) return false;
      next = ConnectionState::Interrupted;
      break;
    case EngineEventKind::Disconnected:
      if (state_ == ConnectionState::Disconnected) return false;
      next = ConnectionState::Disconnected;
      break;
    case EngineEventKind::Failed:
      if (state_ == ConnectionState::Disconnected) return false;
      next = ConnectionState::Error;
      break;
  }
  last_sequence_ = event.sequence;
  state_ = next;
  return true;
}

void ConnectionMachine::on_engine_channel_lost() noexcept {
  policy_.engine_channel_authenticated = false;
  if (state_ != ConnectionState::Disconnected &&
      state_ != ConnectionState::Error) state_ = ConnectionState::Interrupted;
}

}  // namespace wexum::desktop
