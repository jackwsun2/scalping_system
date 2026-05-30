#include "trading/presentation/nana_elements_adapter.hpp"

namespace trading {

std::string SupplementalUiAdapter::name() const
{
    return "Nana / Elements supplemental adapter";
}

bool SupplementalUiAdapter::nana_available() const
{
#if defined(TRADING_WITH_NANA)
    return true;
#else
    return false;
#endif
}

bool SupplementalUiAdapter::elements_available() const
{
#if defined(TRADING_WITH_ELEMENTS)
    return true;
#else
    return false;
#endif
}

std::string SupplementalUiAdapter::status_text() const
{
    if (nana_available() || elements_available()) {
        return "Supplemental native UI adapter enabled";
    }
    return "Supplemental adapter compiled; Nana/Elements libraries are not linked in this environment";
}

} // namespace trading
