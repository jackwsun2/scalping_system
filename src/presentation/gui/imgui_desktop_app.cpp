#include "trading/presentation/desktop_app.hpp"

#include "trading/presentation/nana_elements_adapter.hpp"

#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl2.h>

#include <GLFW/glfw3.h>

#include <algorithm>
#include <array>
#include <cstdio>
#include <cstring>
#include <numeric>
#include <iomanip>
#include <sstream>

namespace trading {

namespace {

void glfw_error_callback(int error, const char* description)
{
    std::fprintf(stderr, "GLFW Error %d: %s\n", error, description);
}

std::string join_symbols(const std::vector<std::string>& symbols)
{
    std::ostringstream out;
    for (std::size_t i = 0; i < symbols.size(); ++i) {
        if (i > 0) {
            out << ",";
        }
        out << symbols[i];
    }
    return out.str();
}

std::vector<std::string> split_symbols(const char* input)
{
    std::vector<std::string> symbols;
    std::string current;
    for (const char* p = input; *p != '\0'; ++p) {
        if (*p == ',') {
            if (!current.empty()) {
                symbols.push_back(current);
            }
            current.clear();
        } else if (*p != ' ') {
            current.push_back(*p);
        }
    }
    if (!current.empty()) {
        symbols.push_back(current);
    }
    return symbols.empty() ? std::vector<std::string>{"GLD", "SLV"} : symbols;
}

void draw_equity_curve(const BacktestResult& result)
{
    if (result.equity_curve.empty()) {
        ImGui::TextUnformatted("No equity data");
        return;
    }
    std::vector<float> values;
    values.reserve(result.equity_curve.size());
    for (double value : result.equity_curve) {
        values.push_back(static_cast<float>(value));
    }
    const auto [min_it, max_it] = std::minmax_element(values.begin(), values.end());
    ImGui::PlotLines("Equity", values.data(), static_cast<int>(values.size()),
                     0, nullptr, *min_it, *max_it, ImVec2(-1.0f, 150.0f));
}

std::vector<float> aggregate_equity_curve(const std::vector<BacktestResult>& results)
{
    std::size_t max_size = 0;
    for (const auto& result : results) {
        max_size = std::max(max_size, result.equity_curve.size());
    }

    std::vector<float> values(max_size, 0.0f);
    for (std::size_t i = 0; i < max_size; ++i) {
        double equity = 0.0;
        for (const auto& result : results) {
            if (result.equity_curve.empty()) {
                continue;
            }
            const std::size_t index = std::min(i, result.equity_curve.size() - 1);
            equity += result.equity_curve[index];
        }
        values[i] = static_cast<float>(equity);
    }
    return values;
}

void draw_aggregate_equity_curve(const std::vector<BacktestResult>& results)
{
    auto values = aggregate_equity_curve(results);
    if (values.empty()) {
        ImGui::TextUnformatted("No equity data");
        return;
    }
    const auto [min_it, max_it] = std::minmax_element(values.begin(), values.end());
    ImGui::PlotLines("Account Balance (USD)", values.data(), static_cast<int>(values.size()),
                     0, nullptr, *min_it, *max_it, ImVec2(-1.0f, 220.0f));
}

BacktestResult aggregate_results(const std::vector<BacktestResult>& results)
{
    BacktestResult aggregate;
    if (results.empty()) {
        return aggregate;
    }

    aggregate.initial_cash = std::accumulate(
        results.begin(), results.end(), 0.0,
        [](double sum, const BacktestResult& result) { return sum + result.initial_cash; });
    aggregate.final_equity = std::accumulate(
        results.begin(), results.end(), 0.0,
        [](double sum, const BacktestResult& result) { return sum + result.final_equity; });
    aggregate.net_profit = aggregate.final_equity - aggregate.initial_cash;
    aggregate.total_return_pct = aggregate.initial_cash > 0.0
        ? aggregate.net_profit / aggregate.initial_cash * 100.0
        : 0.0;

    double weighted_drawdown = 0.0;
    double weighted_sharpe = 0.0;
    double gross_profit = 0.0;
    double gross_loss = 0.0;
    std::size_t drawdown_weight = 0;
    for (const auto& result : results) {
        aggregate.total_trades += result.total_trades;
        aggregate.winning_trades += result.winning_trades;
        aggregate.losing_trades += result.losing_trades;
        aggregate.total_fees += result.total_fees;
        aggregate.largest_win = std::max(aggregate.largest_win, result.largest_win);
        aggregate.largest_loss = std::min(aggregate.largest_loss, result.largest_loss);
        weighted_drawdown += result.max_drawdown_pct * static_cast<double>(result.equity_curve.size());
        weighted_sharpe += result.sharpe_ratio;
        drawdown_weight += result.equity_curve.size();
        for (const auto& trade : result.trades) {
            aggregate.trades.push_back(trade);
            if (trade.pnl > 0.0) {
                gross_profit += trade.pnl;
            } else {
                gross_loss += -trade.pnl;
            }
        }
    }

    aggregate.win_rate_pct = aggregate.total_trades > 0
        ? static_cast<double>(aggregate.winning_trades) / static_cast<double>(aggregate.total_trades) * 100.0
        : 0.0;
    aggregate.max_drawdown_pct = drawdown_weight > 0
        ? weighted_drawdown / static_cast<double>(drawdown_weight)
        : 0.0;
    aggregate.sharpe_ratio = weighted_sharpe / static_cast<double>(results.size());
    aggregate.profit_factor = gross_loss > 1e-12 ? gross_profit / gross_loss : (gross_profit > 0.0 ? gross_profit : 0.0);
    aggregate.average_trade_pnl = aggregate.total_trades > 0
        ? aggregate.net_profit / static_cast<double>(aggregate.total_trades)
        : 0.0;
    aggregate.average_win = aggregate.winning_trades > 0
        ? gross_profit / static_cast<double>(aggregate.winning_trades)
        : 0.0;
    aggregate.average_loss = aggregate.losing_trades > 0
        ? -gross_loss / static_cast<double>(aggregate.losing_trades)
        : 0.0;

    return aggregate;
}

void draw_metric(const char* label, double value, const char* format = "%.2f")
{
    ImGui::BeginGroup();
    ImGui::TextDisabled("%s", label);
    ImGui::Text(format, value);
    ImGui::EndGroup();
}

void draw_price_view(const MarketSeries& market)
{
    if (market.bars.empty()) {
        ImGui::TextUnformatted("No price data");
        return;
    }
    std::vector<float> closes;
    closes.reserve(market.bars.size());
    for (const auto& bar : market.bars) {
        closes.push_back(static_cast<float>(bar.close));
    }
    const auto [min_it, max_it] = std::minmax_element(closes.begin(), closes.end());
    ImGui::PlotLines(("Close##" + market.symbol).c_str(), closes.data(),
                     static_cast<int>(closes.size()), 0, nullptr,
                     *min_it, *max_it, ImVec2(-1.0f, 140.0f));
}

} // namespace

int run_desktop_app(DesktopAppContext context)
{
    glfwSetErrorCallback(glfw_error_callback);
    if (!glfwInit()) {
        throw std::runtime_error("failed to initialize GLFW");
    }

    GLFWwindow* window = glfwCreateWindow(1280, 820, "ScalpingSystem Trader Workstation", nullptr, nullptr);
    if (window == nullptr) {
        glfwTerminate();
        throw std::runtime_error("failed to create GLFW window");
    }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    ImGui::StyleColorsDark();

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL2_Init();

    std::array<char, 256> symbols_buffer{};
    std::array<char, 512> csv_buffer{};
    std::array<char, 512> db_buffer{};
    std::array<char, 512> log_buffer{};
    std::snprintf(symbols_buffer.data(), symbols_buffer.size(), "%s", join_symbols(context.config.symbols).c_str());
    std::snprintf(csv_buffer.data(), csv_buffer.size(), "%s", context.config.csv_path.c_str());
    std::snprintf(db_buffer.data(), db_buffer.size(), "%s", context.config.db_path.c_str());
    std::snprintf(log_buffer.data(), log_buffer.size(), "%s", context.config.log_dir.c_str());

    ServiceRunResult last_run;
    std::string status = "Ready";
    SupplementalUiAdapter supplemental_ui;
    StrategyConfig strategy_config = context.config.strategy;
    RiskConfig risk_config = context.config.risk;
    int strategy_index = strategy_config.name == "RSI_ONLY" ? 1 : 0;

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        ImGui_ImplOpenGL2_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiCond_Always);
        ImGui::SetNextWindowSize(io.DisplaySize, ImGuiCond_Always);
        ImGui::Begin("ScalpingSystem", nullptr,
                     ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoResize |
                     ImGuiWindowFlags_NoCollapse);

        if (ImGui::BeginTabBar("MainTabs")) {
            if (ImGui::BeginTabItem("Backtest Simulator")) {
                const BacktestResult summary = aggregate_results(last_run.results);

                ImGui::TextUnformatted("Quant Strategy Backtest Simulator");
                ImGui::Separator();
                if (!last_run.results.empty()) {
                    draw_aggregate_equity_curve(last_run.results);
                } else {
                    ImGui::Dummy(ImVec2(0.0f, 220.0f));
                }

                ImGui::Columns(4, "SummaryMetrics", false);
                draw_metric("Total Return", summary.total_return_pct, "%.2f%%");
                ImGui::NextColumn();
                draw_metric("Win Rate", summary.win_rate_pct, "%.1f%%");
                ImGui::NextColumn();
                draw_metric("Max Drawdown", summary.max_drawdown_pct, "%.2f%%");
                ImGui::NextColumn();
                draw_metric("Profit Factor", summary.profit_factor, "%.2f");
                ImGui::Columns(1);

                ImGui::Separator();
                ImGui::InputText("Symbols", symbols_buffer.data(), symbols_buffer.size());
                ImGui::InputText("CSV", csv_buffer.data(), csv_buffer.size());
                ImGui::InputText("SQLite DB", db_buffer.data(), db_buffer.size());
                ImGui::InputText("Log Dir", log_buffer.data(), log_buffer.size());

                const char* strategy_names[] = {"RSI Multi-Factor", "RSI Oversold/Overbought"};
                if (ImGui::Combo("Strategy", &strategy_index, strategy_names, 2)) {
                    strategy_config.name = strategy_index == 1 ? "RSI_ONLY" : "RSI_MULTI_FACTOR";
                    strategy_config.minimum_confidence = strategy_index == 1 ? 0.65 : 0.58;
                }
                const double zero = 0.0;
                const double commission_max = 0.05;
                const double take_profit_max = 5.0;
                const double stop_loss_max = 3.0;
                const double risk_min = 0.1;
                const double risk_max = 3.0;
                const double daily_loss_min = 0.5;
                const double daily_loss_max = 10.0;
                const double drawdown_min = 1.0;
                const double drawdown_max = 40.0;
                const double volume_ratio_min = 0.10;
                const double volume_ratio_max = 2.00;
                const double atr_pct_min = 0.0;
                const double atr_pct_max = 8.0;
                const double slippage_max = 0.20;
                double slippage_pct = risk_config.slippage_bps / 100.0;
                if (ImGui::SliderScalar("Slippage (%)", ImGuiDataType_Double, &slippage_pct, &zero, &slippage_max, "%.3f")) {
                    risk_config.slippage_bps = slippage_pct * 100.0;
                }
                ImGui::SliderScalar("Commission Per Share", ImGuiDataType_Double, &risk_config.commission_per_share, &zero, &commission_max, "%.4f");
                ImGui::SliderScalar("Take Profit (%)", ImGuiDataType_Double, &strategy_config.fixed_take_profit_pct, &zero, &take_profit_max, "%.2f");
                ImGui::SliderScalar("Stop Loss (%)", ImGuiDataType_Double, &strategy_config.fixed_stop_loss_pct, &zero, &stop_loss_max, "%.2f");
                double risk_per_trade_pct = risk_config.risk_per_trade_pct * 100.0;
                if (ImGui::SliderScalar("Risk Per Trade (%)", ImGuiDataType_Double, &risk_per_trade_pct, &risk_min, &risk_max, "%.2f")) {
                    risk_config.risk_per_trade_pct = risk_per_trade_pct / 100.0;
                }
                double max_daily_loss_pct = risk_config.max_daily_loss_pct * 100.0;
                if (ImGui::SliderScalar("Max Daily Loss (%)", ImGuiDataType_Double, &max_daily_loss_pct, &daily_loss_min, &daily_loss_max, "%.2f")) {
                    risk_config.max_daily_loss_pct = max_daily_loss_pct / 100.0;
                }
                double max_total_drawdown_pct = risk_config.max_total_drawdown_pct * 100.0;
                if (ImGui::SliderScalar("Max Total Drawdown (%)", ImGuiDataType_Double, &max_total_drawdown_pct, &drawdown_min, &drawdown_max, "%.2f")) {
                    risk_config.max_total_drawdown_pct = max_total_drawdown_pct / 100.0;
                }
                ImGui::SliderScalar("Volume Ratio", ImGuiDataType_Double, &strategy_config.minimum_volume_ratio, &volume_ratio_min, &volume_ratio_max, "%.2f");
                double min_atr_pct = strategy_config.min_atr_pct * 100.0;
                if (ImGui::SliderScalar("Min ATR (%)", ImGuiDataType_Double, &min_atr_pct, &atr_pct_min, &atr_pct_max, "%.2f")) {
                    strategy_config.min_atr_pct = min_atr_pct / 100.0;
                }
                double max_atr_pct = strategy_config.max_atr_pct * 100.0;
                if (ImGui::SliderScalar("Max ATR (%)", ImGuiDataType_Double, &max_atr_pct, &atr_pct_min, &atr_pct_max, "%.2f")) {
                    strategy_config.max_atr_pct = max_atr_pct / 100.0;
                }
                ImGui::Checkbox("Trend Filter", &strategy_config.require_trend_confirmation);

                if (ImGui::Button("Run Backtest", ImVec2(150.0f, 0.0f))) {
                    try {
                        context.config.symbols = split_symbols(symbols_buffer.data());
                        context.config.csv_path = csv_buffer.data();
                        context.config.db_path = db_buffer.data();
                        context.config.log_dir = log_buffer.data();
                        context.config.strategy = strategy_config;
                        context.config.risk = risk_config;
                        context = create_desktop_app_context(context.config);
                        last_run = context.service->run_backtest(context.config.symbols, strategy_config, risk_config);
                        status = "Backtest completed and persisted";
                    } catch (const std::exception& ex) {
                        status = std::string("Error: ") + ex.what();
                        context.logger->error("DesktopApp", status);
                    }
                }
                ImGui::SameLine();
                ImGui::Text("Status: %s", status.c_str());

                ImGui::Separator();
                if (ImGui::BeginTable("Results", 9, ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg)) {
                    ImGui::TableSetupColumn("Symbol");
                    ImGui::TableSetupColumn("Return %");
                    ImGui::TableSetupColumn("Final Equity");
                    ImGui::TableSetupColumn("Net PnL");
                    ImGui::TableSetupColumn("Max DD %");
                    ImGui::TableSetupColumn("Sharpe");
                    ImGui::TableSetupColumn("Profit Factor");
                    ImGui::TableSetupColumn("Trades");
                    ImGui::TableSetupColumn("Win %");
                    ImGui::TableHeadersRow();
                    for (std::size_t i = 0; i < last_run.results.size(); ++i) {
                        const auto& result = last_run.results[i];
                        const std::string symbol = i < last_run.markets.size() ? last_run.markets[i].symbol : "";
                        ImGui::TableNextRow();
                        ImGui::TableSetColumnIndex(0);
                        ImGui::TextUnformatted(symbol.c_str());
                        ImGui::TableSetColumnIndex(1);
                        ImGui::Text("%.2f", result.total_return_pct);
                        ImGui::TableSetColumnIndex(2);
                        ImGui::Text("%.2f", result.final_equity);
                        ImGui::TableSetColumnIndex(3);
                        ImGui::Text("%.2f", result.net_profit);
                        ImGui::TableSetColumnIndex(4);
                        ImGui::Text("%.2f", result.max_drawdown_pct);
                        ImGui::TableSetColumnIndex(5);
                        ImGui::Text("%.2f", result.sharpe_ratio);
                        ImGui::TableSetColumnIndex(6);
                        ImGui::Text("%.2f", result.profit_factor);
                        ImGui::TableSetColumnIndex(7);
                        ImGui::Text("%zu", result.total_trades);
                        ImGui::TableSetColumnIndex(8);
                        ImGui::Text("%.2f", result.win_rate_pct);
                    }
                    ImGui::EndTable();
                }
                ImGui::EndTabItem();
            }

            if (ImGui::BeginTabItem("Charts")) {
                for (std::size_t i = 0; i < last_run.markets.size(); ++i) {
                    const auto& market = last_run.markets[i];
                    ImGui::Text("%s", market.symbol.c_str());
                    draw_price_view(market);
                    if (i < last_run.results.size()) {
                        draw_equity_curve(last_run.results[i]);
                    }
                    ImGui::Separator();
                }
                ImGui::EndTabItem();
            }

            if (ImGui::BeginTabItem("Trades")) {
                if (ImGui::BeginTable("TradesTable", 8, ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg)) {
                    ImGui::TableSetupColumn("Symbol");
                    ImGui::TableSetupColumn("Entry");
                    ImGui::TableSetupColumn("Exit");
                    ImGui::TableSetupColumn("Qty");
                    ImGui::TableSetupColumn("Entry Px");
                    ImGui::TableSetupColumn("Exit Px");
                    ImGui::TableSetupColumn("PnL");
                    ImGui::TableSetupColumn("Reason");
                    ImGui::TableHeadersRow();
                    for (const auto& result : last_run.results) {
                        for (const auto& trade : result.trades) {
                            ImGui::TableNextRow();
                            ImGui::TableSetColumnIndex(0);
                            ImGui::TextUnformatted(trade.symbol.c_str());
                            ImGui::TableSetColumnIndex(1);
                            ImGui::TextUnformatted(trade.entry_time.c_str());
                            ImGui::TableSetColumnIndex(2);
                            ImGui::TextUnformatted(trade.exit_time.c_str());
                            ImGui::TableSetColumnIndex(3);
                            ImGui::Text("%zu", trade.quantity);
                            ImGui::TableSetColumnIndex(4);
                            ImGui::Text("%.2f", trade.entry_price);
                            ImGui::TableSetColumnIndex(5);
                            ImGui::Text("%.2f", trade.exit_price);
                            ImGui::TableSetColumnIndex(6);
                            ImGui::Text("%.2f", trade.pnl);
                            ImGui::TableSetColumnIndex(7);
                            ImGui::TextUnformatted(trade.exit_reason.c_str());
                        }
                    }
                    ImGui::EndTable();
                }
                ImGui::EndTabItem();
            }

            if (ImGui::BeginTabItem("Runtime")) {
                ImGui::Text("Logger: spdlog file sink, retention %d days", context.config.log_retention_days);
                ImGui::Text("SQLite: %s", context.config.db_path.c_str());
                ImGui::Text("%s: %s", supplemental_ui.name().c_str(), supplemental_ui.status_text().c_str());
                ImGui::Separator();
                const auto events = context.service->recent_events(80);
                for (const auto& event : events) {
                    ImGui::Text("[%s] [%s] [%s] %s",
                                event.timestamp.c_str(),
                                event.level.c_str(),
                                event.component.c_str(),
                                event.message.c_str());
                }
                ImGui::EndTabItem();
            }
            ImGui::EndTabBar();
        }

        ImGui::End();

        ImGui::Render();
        int display_w = 0;
        int display_h = 0;
        glfwGetFramebufferSize(window, &display_w, &display_h);
        glViewport(0, 0, display_w, display_h);
        glClearColor(0.08f, 0.09f, 0.10f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL2_RenderDrawData(ImGui::GetDrawData());
        glfwSwapBuffers(window);
    }

    ImGui_ImplOpenGL2_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}

} // namespace trading
