#include "wexum/desktop/locale.hpp"

namespace wexum::desktop {

UiLocale resolve_locale(const std::vector<std::string>& os_preferences,
                        std::optional<UiLocale> manual_override) noexcept {
  if (manual_override) return *manual_override;
  for (const std::string& pref : os_preferences) {
    if (pref.size() < 2) continue;
    const char a = pref[0] >= 'A' && pref[0] <= 'Z' ? pref[0] + ('a' - 'A') : pref[0];
    const char b = pref[1] >= 'A' && pref[1] <= 'Z' ? pref[1] + ('a' - 'A') : pref[1];
    if (pref.size() > 2 && pref[2] != '-' && pref[2] != '_') continue;
    if (a == 'r' && b == 'u') return UiLocale::Russian;
    if (a == 'e' && b == 'n') return UiLocale::English;
  }
  return UiLocale::English;
}

std::string_view locale_code(UiLocale locale) noexcept {
  return locale == UiLocale::Russian ? "ru" : "en";
}

}  // namespace wexum::desktop
