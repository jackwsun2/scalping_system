#include "trading/presentation/desktop_app.hpp"

#include <iostream>
#include <string>
#include <vector>

namespace {

std::vector<std::string> split_symbols(const std::string& input)
{
    std::vector<std::string> result;
    std::string current;
    for (char ch : input) {
        if (ch == ',') {
            if (!current.empty()) {
                result.push_back(current);
            }
            current.clear();
        } else if (ch != ' ') {
            current.push_back(ch);
        }
    }
    if (!current.empty()) {
        result.push_back(current);
    }
    return result;
}

} // namespace

int main(int argc, char** argv)
{
    trading::DesktopAppConfig config;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--csv" && i + 1 < argc) {
            config.csv_path = argv[++i];
        } else if (arg == "--symbols" && i + 1 < argc) {
            config.symbols = split_symbols(argv[++i]);
        } else if (arg == "--db" && i + 1 < argc) {
            config.db_path = argv[++i];
        } else if (arg == "--logs" && i + 1 < argc) {
            config.log_dir = argv[++i];
        } else if (arg == "--log-retention-days" && i + 1 < argc) {
            config.log_retention_days = std::stoi(argv[++i]);
        } else {
            std::cerr << "Unknown or incomplete argument: " << arg << "\n";
            return 2;
        }
    }

    try {
        return trading::run_desktop_app(trading::create_desktop_app_context(config));
    } catch (const std::exception& ex) {
        std::cerr << "Desktop app failed: " << ex.what() << "\n";
        return 1;
    }
}
