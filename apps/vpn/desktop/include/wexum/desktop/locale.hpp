#pragma once

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace wexum::desktop {

enum class UiLocale { English, Russian };

// Only independently published desktop catalogs may be selected.
// Unpublished languages fall back to the next OS preference, then English.
[[nodiscard]] UiLocale resolve_locale(
    const std::vector<std::string>& os_preferences,
    std::optional<UiLocale> manual_override = std::nullopt) noexcept;
[[nodiscard]] std::string_view locale_code(UiLocale locale) noexcept;

}  // namespace wexum::desktop
