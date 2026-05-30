#include "trading/infrastructure/file_logger.hpp"

#include <spdlog/sinks/basic_file_sink.h>
#include <spdlog/spdlog.h>

#include <chrono>
#include <ctime>
#include <filesystem>
#include <iomanip>
#include <sstream>

namespace trading {

namespace {

std::string today_string()
{
    const auto now = std::chrono::system_clock::now();
    const std::time_t time = std::chrono::system_clock::to_time_t(now);
    std::tm local_time{};
#if defined(_WIN32)
    localtime_s(&local_time, &time);
#else
    localtime_r(&time, &local_time);
#endif
    std::ostringstream out;
    out << std::put_time(&local_time, "%Y-%m-%d");
    return out.str();
}

} // namespace

SpdlogFileLogger::SpdlogFileLogger(std::string log_dir, int retention_days)
    : log_dir_(std::move(log_dir)),
      retention_days_(retention_days)
{
    std::filesystem::create_directories(log_dir_);
    cleanup_old_logs();

    const auto log_file = std::filesystem::path(log_dir_) /
                          ("trading_" + today_string() + ".log");
    logger_ = spdlog::basic_logger_mt("trading_file_logger", log_file.string(), true);
    logger_->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] [%n] %v");
    logger_->flush_on(spdlog::level::info);
    logger_->info("logger initialized file={}", log_file.string());
}

SpdlogFileLogger::~SpdlogFileLogger()
{
    if (logger_) {
        logger_->flush();
        spdlog::drop(logger_->name());
    }
}

void SpdlogFileLogger::info(const std::string& component, const std::string& message)
{
    logger_->info("[{}] {}", component, message);
}

void SpdlogFileLogger::warn(const std::string& component, const std::string& message)
{
    logger_->warn("[{}] {}", component, message);
}

void SpdlogFileLogger::error(const std::string& component, const std::string& message)
{
    logger_->error("[{}] {}", component, message);
}

void SpdlogFileLogger::cleanup_old_logs()
{
    if (retention_days_ <= 0 || !std::filesystem::exists(log_dir_)) {
        return;
    }

    const auto now = std::filesystem::file_time_type::clock::now();
    const auto max_age = std::chrono::hours(24 * retention_days_);
    for (const auto& entry : std::filesystem::directory_iterator(log_dir_)) {
        if (!entry.is_regular_file()) {
            continue;
        }
        const auto path = entry.path();
        if (path.extension() != ".log") {
            continue;
        }
        const auto age = now - entry.last_write_time();
        if (age > max_age) {
            std::filesystem::remove(path);
        }
    }
}

} // namespace trading
