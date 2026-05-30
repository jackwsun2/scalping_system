#pragma once

#include <string>

namespace trading {

class SupplementalUiAdapter {
public:
    std::string name() const;
    bool nana_available() const;
    bool elements_available() const;
    std::string status_text() const;
};

} // namespace trading
