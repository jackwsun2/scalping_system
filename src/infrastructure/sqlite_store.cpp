#include "trading/infrastructure/sqlite_store.hpp"

#include <filesystem>
#include <stdexcept>

namespace trading {

namespace {

void bind_text(sqlite3_stmt* stmt, int index, const std::string& value)
{
    sqlite3_bind_text(stmt, index, value.c_str(), -1, SQLITE_TRANSIENT);
}

void check_sqlite(int rc, sqlite3* db, const std::string& context)
{
    if (rc != SQLITE_OK && rc != SQLITE_DONE && rc != SQLITE_ROW) {
        throw std::runtime_error(context + ": " + sqlite3_errmsg(db));
    }
}

} // namespace

SqliteTradingStore::SqliteTradingStore(std::string db_path)
    : db_path_(std::move(db_path))
{
}

SqliteTradingStore::~SqliteTradingStore()
{
    if (db_) {
        sqlite3_close(db_);
    }
}

void SqliteTradingStore::open()
{
    if (db_) {
        return;
    }
    const std::filesystem::path path(db_path_);
    if (path.has_parent_path()) {
        std::filesystem::create_directories(path.parent_path());
    }
    const int rc = sqlite3_open(db_path_.c_str(), &db_);
    if (rc != SQLITE_OK) {
        const std::string error = db_ ? sqlite3_errmsg(db_) : "unknown sqlite error";
        throw std::runtime_error("Cannot open SQLite database: " + error);
    }
    exec("PRAGMA journal_mode=WAL;");
    exec("PRAGMA synchronous=NORMAL;");
    exec("PRAGMA foreign_keys=ON;");
}

void SqliteTradingStore::exec(const std::string& sql)
{
    open();
    char* error = nullptr;
    const int rc = sqlite3_exec(db_, sql.c_str(), nullptr, nullptr, &error);
    if (rc != SQLITE_OK) {
        const std::string message = error ? error : sqlite3_errmsg(db_);
        sqlite3_free(error);
        throw std::runtime_error("SQLite exec failed: " + message);
    }
}

void SqliteTradingStore::initialize()
{
    open();
    exec("CREATE TABLE IF NOT EXISTS bars ("
         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
         "timestamp TEXT NOT NULL,"
         "symbol TEXT NOT NULL,"
         "open REAL NOT NULL,"
         "high REAL NOT NULL,"
         "low REAL NOT NULL,"
         "close REAL NOT NULL,"
         "volume REAL NOT NULL,"
         "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
         "UNIQUE(timestamp, symbol));");
    exec("CREATE TABLE IF NOT EXISTS backtest_runs ("
         "run_id TEXT PRIMARY KEY,"
         "symbol TEXT NOT NULL,"
         "initial_cash REAL NOT NULL,"
         "final_equity REAL NOT NULL,"
         "total_return_pct REAL NOT NULL,"
         "max_drawdown_pct REAL NOT NULL,"
         "sharpe_ratio REAL NOT NULL,"
         "win_rate_pct REAL NOT NULL,"
         "total_trades INTEGER NOT NULL,"
         "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);");
    exec("CREATE TABLE IF NOT EXISTS trades ("
         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
         "run_id TEXT NOT NULL,"
         "symbol TEXT NOT NULL,"
         "entry_time TEXT NOT NULL,"
         "exit_time TEXT NOT NULL,"
         "quantity INTEGER NOT NULL,"
         "entry_price REAL NOT NULL,"
         "exit_price REAL NOT NULL,"
         "pnl REAL NOT NULL,"
         "exit_reason TEXT NOT NULL,"
         "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
         "FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id));");
    exec("CREATE TABLE IF NOT EXISTS runtime_events ("
         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
         "timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
         "level TEXT NOT NULL,"
         "component TEXT NOT NULL,"
         "message TEXT NOT NULL);");
}

void SqliteTradingStore::save_market_series(const MarketSeries& series)
{
    initialize();
    sqlite3_stmt* stmt = nullptr;
    const char* sql =
        "INSERT OR REPLACE INTO bars(timestamp, symbol, open, high, low, close, volume) "
        "VALUES(?, ?, ?, ?, ?, ?, ?);";
    check_sqlite(sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr), db_, "prepare bars insert");
    exec("BEGIN TRANSACTION;");
    for (const auto& bar : series.bars) {
        sqlite3_reset(stmt);
        sqlite3_clear_bindings(stmt);
        bind_text(stmt, 1, bar.timestamp);
        bind_text(stmt, 2, bar.symbol);
        sqlite3_bind_double(stmt, 3, bar.open);
        sqlite3_bind_double(stmt, 4, bar.high);
        sqlite3_bind_double(stmt, 5, bar.low);
        sqlite3_bind_double(stmt, 6, bar.close);
        sqlite3_bind_double(stmt, 7, bar.volume);
        check_sqlite(sqlite3_step(stmt), db_, "insert bar");
    }
    sqlite3_finalize(stmt);
    exec("COMMIT;");
}

void SqliteTradingStore::save_backtest_result(const std::string& run_id,
                                              const std::string& symbol,
                                              const BacktestResult& result)
{
    initialize();
    sqlite3_stmt* run_stmt = nullptr;
    const char* run_sql =
        "INSERT OR REPLACE INTO backtest_runs(run_id, symbol, initial_cash, final_equity, "
        "total_return_pct, max_drawdown_pct, sharpe_ratio, win_rate_pct, total_trades) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);";
    check_sqlite(sqlite3_prepare_v2(db_, run_sql, -1, &run_stmt, nullptr), db_, "prepare run insert");
    bind_text(run_stmt, 1, run_id);
    bind_text(run_stmt, 2, symbol);
    sqlite3_bind_double(run_stmt, 3, result.initial_cash);
    sqlite3_bind_double(run_stmt, 4, result.final_equity);
    sqlite3_bind_double(run_stmt, 5, result.total_return_pct);
    sqlite3_bind_double(run_stmt, 6, result.max_drawdown_pct);
    sqlite3_bind_double(run_stmt, 7, result.sharpe_ratio);
    sqlite3_bind_double(run_stmt, 8, result.win_rate_pct);
    sqlite3_bind_int64(run_stmt, 9, static_cast<sqlite3_int64>(result.total_trades));
    check_sqlite(sqlite3_step(run_stmt), db_, "insert backtest run");
    sqlite3_finalize(run_stmt);

    sqlite3_stmt* trade_stmt = nullptr;
    const char* trade_sql =
        "INSERT INTO trades(run_id, symbol, entry_time, exit_time, quantity, entry_price, "
        "exit_price, pnl, exit_reason) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);";
    check_sqlite(sqlite3_prepare_v2(db_, trade_sql, -1, &trade_stmt, nullptr), db_, "prepare trade insert");
    exec("BEGIN TRANSACTION;");
    for (const auto& trade : result.trades) {
        sqlite3_reset(trade_stmt);
        sqlite3_clear_bindings(trade_stmt);
        bind_text(trade_stmt, 1, run_id);
        bind_text(trade_stmt, 2, trade.symbol);
        bind_text(trade_stmt, 3, trade.entry_time);
        bind_text(trade_stmt, 4, trade.exit_time);
        sqlite3_bind_int64(trade_stmt, 5, static_cast<sqlite3_int64>(trade.quantity));
        sqlite3_bind_double(trade_stmt, 6, trade.entry_price);
        sqlite3_bind_double(trade_stmt, 7, trade.exit_price);
        sqlite3_bind_double(trade_stmt, 8, trade.pnl);
        bind_text(trade_stmt, 9, trade.exit_reason);
        check_sqlite(sqlite3_step(trade_stmt), db_, "insert trade");
    }
    sqlite3_finalize(trade_stmt);
    exec("COMMIT;");
}

void SqliteTradingStore::save_runtime_event(const RuntimeEvent& event)
{
    initialize();
    sqlite3_stmt* stmt = nullptr;
    const char* sql =
        "INSERT INTO runtime_events(timestamp, level, component, message) "
        "VALUES(COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP), ?, ?, ?);";
    check_sqlite(sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr), db_, "prepare event insert");
    bind_text(stmt, 1, event.timestamp);
    bind_text(stmt, 2, event.level);
    bind_text(stmt, 3, event.component);
    bind_text(stmt, 4, event.message);
    check_sqlite(sqlite3_step(stmt), db_, "insert runtime event");
    sqlite3_finalize(stmt);
}

std::vector<RuntimeEvent> SqliteTradingStore::recent_events(int limit)
{
    initialize();
    std::vector<RuntimeEvent> events;
    sqlite3_stmt* stmt = nullptr;
    const char* sql =
        "SELECT timestamp, level, component, message "
        "FROM runtime_events ORDER BY id DESC LIMIT ?;";
    check_sqlite(sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr), db_, "prepare event query");
    sqlite3_bind_int(stmt, 1, limit);
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        RuntimeEvent event;
        event.timestamp = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        event.level = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1));
        event.component = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 2));
        event.message = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 3));
        events.push_back(event);
    }
    sqlite3_finalize(stmt);
    return events;
}

} // namespace trading
