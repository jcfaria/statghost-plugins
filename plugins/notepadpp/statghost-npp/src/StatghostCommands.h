#pragma once

#include <cstddef>

namespace StatghostCommands
{
    void invoke(const char *key);
    void invokeByShowIndex(std::size_t index);

    bool isArmed();
    void setArmed(bool armed);
}
