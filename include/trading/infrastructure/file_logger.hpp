#pragma once

#include "trading/application/interfaces.hpp"

#include <memory>
#include <string>

namespace spdlog {
class logger;
}

namespace trading {

class SpdlogFileLogger final : public ILogger {
public:
    SpdlogFileLogger(std::string log_dir, int retention_days);
    ~SpdlogFileLogger() override;

    void info(const std::string& component, const std::string& message) override;
    void warn(const std::string& component, const std::string& message) override;
    void error(const std::string& component, const std::string& message) override;

    void cleanup_old_logs();

private:
    std::string log_dir_;
    int retention_days_ = 7;
    std::shared_ptr<spdlog::logger> logger_;
};

} // namespace trading
