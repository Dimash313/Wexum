#include "wexum/desktop/connection.hpp"
#include "wexum/desktop/locale.hpp"

#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using namespace wexum::desktop;

int checks = 0;
#define CHECK(expr) do { ++checks; if (!(expr)) { \
  std::cerr << __FILE__ << ':' << __LINE__ << " failed: " << #expr << '\n'; \
  std::exit(1); } } while (false)

void test_fail_closed_and_full_cycle() {
  ConnectionMachine m;
  CHECK(m.state() == ConnectionState::Disconnected);
  CHECK(!m.can_connect());
  CHECK(m.request_connect().action == EngineAction::None);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 1}));

  CHECK(m.update_trusted_policy({true, true, false}).action == EngineAction::None);
  CHECK(!m.can_connect());
  CHECK(m.update_trusted_policy({true, true, true}).action == EngineAction::None);
  CHECK(m.can_connect());
  const EngineCommand start = m.request_connect();
  CHECK(start.action == EngineAction::Start && start.attempt == 1);
  CHECK(m.state() == ConnectionState::Connecting);
  CHECK(m.request_connect().action == EngineAction::None);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 2, 1}));
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 0}));
  CHECK(m.observe_verified_engine_event({EngineEventKind::Connected, 1, 1}));
  CHECK(m.state() == ConnectionState::Protected);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Interrupted, 1, 1}));
  CHECK(m.request_disconnect().action == EngineAction::Stop);
  CHECK(m.state() == ConnectionState::Disconnecting);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 2}));
  CHECK(m.request_disconnect().action == EngineAction::None);
  CHECK(m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 3}));
  CHECK(m.state() == ConnectionState::Disconnected);
  CHECK(m.request_connect().attempt == 2);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 100}));
}

void test_revocation_and_recovery() {
  ConnectionMachine m;
  (void)m.update_trusted_policy({true, true, true});
  (void)m.request_connect();
  CHECK(m.observe_verified_engine_event({EngineEventKind::Connected, 1, 1}));
  const EngineCommand stop = m.update_trusted_policy({false, true, true});
  CHECK(stop.action == EngineAction::Stop && stop.attempt == 1);
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 2}));
  CHECK(!m.can_connect());
  CHECK(m.update_trusted_policy({false, true, true}).action == EngineAction::None);
  (void)m.update_trusted_policy({true, true, true});
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 3}));
  CHECK(m.state() == ConnectionState::Interrupted);
  m.on_engine_channel_lost();
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 4}));
  CHECK(m.request_disconnect().action == EngineAction::Stop);
  CHECK(m.state() == ConnectionState::Disconnecting);
  CHECK(!m.can_connect());
  (void)m.update_trusted_policy({true, true, true});
  CHECK(m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 5}));
  CHECK(m.state() == ConnectionState::Disconnected);
  CHECK(m.can_connect());
}

void test_errors_cannot_fake_disconnect() {
  ConnectionMachine m;
  (void)m.update_trusted_policy({true, true, true});
  (void)m.request_connect();
  CHECK(m.observe_verified_engine_event({EngineEventKind::Failed, 1, 1}));
  CHECK(m.state() == ConnectionState::Error);
  CHECK(!m.can_connect());
  CHECK(m.request_connect().action == EngineAction::None);
  CHECK(m.request_disconnect().action == EngineAction::Stop);
  CHECK(m.state() == ConnectionState::Disconnecting);
  CHECK(m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 2}));
  CHECK(m.can_connect());
  CHECK(m.request_connect().attempt == 2);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 3}));
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Disconnected, 2, 0}));
  CHECK(m.state() == ConnectionState::Connecting);
}

void test_interrupted_then_stale_and_downgrade() {
  ConnectionMachine m;
  (void)m.update_trusted_policy({true, true, true});
  (void)m.request_connect();
  CHECK(m.observe_verified_engine_event({EngineEventKind::Interrupted, 1, 4}));
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 3}));
  CHECK(m.observe_verified_engine_event({EngineEventKind::Connected, 1, 5}));
  CHECK(m.state() == ConnectionState::Protected);
  CHECK(m.update_trusted_policy({true, false, true}).action == EngineAction::Stop);
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 6}));
  CHECK(m.request_disconnect().action == EngineAction::Stop);
}

void test_reauthenticated_channel_must_confirm_old_tunnel_stopped() {
  ConnectionMachine m;
  (void)m.update_trusted_policy({true, true, true});
  (void)m.request_connect();
  CHECK(m.observe_verified_engine_event({EngineEventKind::Connected, 1, 1}));
  m.on_engine_channel_lost();
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(m.update_trusted_policy({true, true, true}).action == EngineAction::None);
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 2}));
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(!m.can_connect());
  CHECK(m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 3}));
  CHECK(m.can_connect());
  CHECK(m.request_connect().attempt == 2);
  CHECK(m.observe_verified_engine_event({EngineEventKind::Connected, 2, 1}));
  CHECK(m.state() == ConnectionState::Protected);
}

void test_revocation_during_interruption_must_stop() {
  ConnectionMachine m;
  (void)m.update_trusted_policy({true, true, true});
  (void)m.request_connect();
  CHECK(m.observe_verified_engine_event({EngineEventKind::Interrupted, 1, 1}));
  CHECK(m.update_trusted_policy({true, false, true}).action == EngineAction::Stop);
  CHECK(m.update_trusted_policy({true, false, true}).action == EngineAction::None);
  (void)m.update_trusted_policy({true, true, true});
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 2}));
  CHECK(m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 3}));
  CHECK(m.can_connect());
}

void test_invalid_policy_in_error_requires_stop() {
  ConnectionMachine m;
  (void)m.update_trusted_policy({true, true, true});
  (void)m.request_connect();
  CHECK(m.observe_verified_engine_event({EngineEventKind::Failed, 1, 1}));
  CHECK(m.update_trusted_policy({false, true, true}).action == EngineAction::Stop);
  (void)m.update_trusted_policy({true, true, true});
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 2}));
  CHECK(m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 3}));
  CHECK(m.can_connect());
}

void test_rejected_newer_event_blocks_stale_disconnect() {
  ConnectionMachine m;
  (void)m.update_trusted_policy({true, true, true});
  (void)m.request_connect();
  CHECK(m.observe_verified_engine_event({EngineEventKind::Connected, 1, 1}));
  CHECK(m.update_trusted_policy({false, true, true}).action == EngineAction::Stop);
  (void)m.update_trusted_policy({true, true, true});
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Connected, 1, 5}));
  CHECK(!m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 4}));
  CHECK(m.state() == ConnectionState::Interrupted);
  CHECK(m.observe_verified_engine_event({EngineEventKind::Disconnected, 1, 6}));
  CHECK(m.state() == ConnectionState::Disconnected);
  CHECK(m.can_connect());
}

void test_locales_only_published() {
  CHECK(resolve_locale({"ru-KZ", "en-US"}) == UiLocale::Russian);
  CHECK(resolve_locale({"kk-KZ", "ru-RU"}) == UiLocale::Russian);
  CHECK(resolve_locale({"ar-SA", "kk-KZ"}) == UiLocale::English);
  CHECK(resolve_locale({"EN-us", "ru"}) == UiLocale::English);
  CHECK(resolve_locale({"russian", "ru"}) == UiLocale::Russian);
  CHECK(resolve_locale({}, UiLocale::Russian) == UiLocale::Russian);
  CHECK(resolve_locale({"ru"}, UiLocale::English) == UiLocale::English);
  CHECK(locale_code(UiLocale::Russian) == "ru");
  CHECK(locale_code(UiLocale::English) == "en");
}

int main() {
  test_fail_closed_and_full_cycle();
  test_revocation_and_recovery();
  test_errors_cannot_fake_disconnect();
  test_interrupted_then_stale_and_downgrade();
  test_reauthenticated_channel_must_confirm_old_tunnel_stopped();
  test_revocation_during_interruption_must_stop();
  test_invalid_policy_in_error_requires_stop();
  test_rejected_newer_event_blocks_stale_disconnect();
  test_locales_only_published();
  std::cout << "WexumVPN Desktop core: " << checks << " checks passed\n";
}
