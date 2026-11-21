#include "wexum/desktop/locale.hpp"

#include <QApplication>
#include <QComboBox>
#include <QFont>
#include <QLabel>
#include <QLocale>
#include <QMainWindow>
#include <QPushButton>
#include <QSettings>
#include <QStringList>
#include <QVBoxLayout>
#include <QWidget>

#include <optional>
#include <string>
#include <vector>

using wexum::desktop::UiLocale;

int main(int argc, char** argv) {
  QApplication app(argc, argv);
  QCoreApplication::setOrganizationName("IhsanSoft");
  QCoreApplication::setApplicationName("WexumVPNDesktop");
  QSettings preferences;

  std::vector<std::string> os_languages;
  for (const QString& language : QLocale::system().uiLanguages()) {
    os_languages.push_back(language.toStdString());
  }
  const QString manual_code = preferences.value("ui/locale", "system").toString();
  std::optional<UiLocale> manual;
  if (manual_code == "ru") manual = UiLocale::Russian;
  if (manual_code == "en") manual = UiLocale::English;

  QMainWindow window;
  window.setWindowTitle("WexumVPN");
  window.setMinimumSize(440, 450);
  auto* content = new QWidget(&window);
  auto* layout = new QVBoxLayout(content);
  layout->setContentsMargins(42, 42, 42, 42);
  layout->setSpacing(18);

  auto* heading = new QLabel("WEXUMVPN", content);
  QFont heading_font = heading->font();
  heading_font.setPointSize(25);
  heading_font.setBold(true);
  heading->setFont(heading_font);
  layout->addWidget(heading);

  auto* subheading = new QLabel(content);
  layout->addWidget(subheading);
  layout->addSpacing(34);

  auto* status = new QLabel(content);
  QFont status_font = status->font();
  status_font.setPointSize(19);
  status_font.setBold(true);
  status->setFont(status_font);
  layout->addWidget(status);

  auto* explanation = new QLabel(content);
  explanation->setWordWrap(true);
  layout->addWidget(explanation);
  layout->addSpacing(24);

  auto* connect = new QPushButton(content);
  connect->setEnabled(false);  // No authenticated OS VPN service adapter exists yet.
  connect->setMinimumHeight(48);
  layout->addWidget(connect);

  auto* disconnect = new QPushButton(content);
  disconnect->setEnabled(false);
  disconnect->setMinimumHeight(40);
  layout->addWidget(disconnect);
  layout->addStretch();

  auto* language_label = new QLabel(content);
  layout->addWidget(language_label);
  auto* language = new QComboBox(content);
  language->addItem("System default", "system");
  language->addItem("English", "en");
  language->addItem("Русский", "ru");
  const int index = language->findData(manual_code);
  language->setCurrentIndex(index < 0 ? 0 : index);
  layout->addWidget(language);

  auto render = [&] {
    const UiLocale locale = wexum::desktop::resolve_locale(os_languages, manual);
    const bool ru = locale == UiLocale::Russian;
    subheading->setText(ru ? "Приватное подключение" : "Private connection");
    status->setText(ru ? "Отключено" : "Disconnected");
    explanation->setText(ru
      ? "VPN-движок пока не подключён. Соединение недоступно: приложение не показывает ложную защиту."
      : "VPN engine not integrated. Connection is unavailable; this app does not claim protection.");
    connect->setText(ru ? "Подключиться" : "Connect");
    disconnect->setText(ru ? "Отключиться" : "Disconnect");
    language_label->setText(ru ? "Язык интерфейса" : "Interface language");
  };

  QObject::connect(language, QOverload<int>::of(&QComboBox::currentIndexChanged),
                   &window, [&](int selected) {
    const QString code = language->itemData(selected).toString();
    manual = code == "ru" ? std::optional{UiLocale::Russian} :
             code == "en" ? std::optional{UiLocale::English} : std::nullopt;
    preferences.setValue("ui/locale", code);
    render();
  });
  render();

  content->setStyleSheet(R"(
    QWidget { background: #080808; color: #ffffff; font-size: 14px; }
    QLabel { background: transparent; }
    QPushButton { background: #ffffff; color: #000000; border: 0; border-radius: 8px; font-weight: 600; }
    QPushButton:disabled { background: #333333; color: #aaaaaa; }
    QComboBox { background: #1a1a1a; color: #ffffff; border: 1px solid #444444;
                border-radius: 8px; padding: 8px; }
  )");
  window.setCentralWidget(content);
  window.show();
  return app.exec();
}
