/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include "camera_sensor_helper.h"
#include <cmath>
#include <iostream>

int main()
{
    for (const char *name : { "s5khmx", "s5k3t2", "s5k5e9" }) {
        auto helper = libcamera::ipa::CameraSensorHelperFactoryBase::create(name);
        if (!helper) {
            std::cerr << "Missing sensor helper: " << name << '\n';
            return 1;
        }
        // Golden values from the phone's original Q5 gain conversion.
        for (const auto [code, gain] : {
                 std::pair{32u, 1.0}, {48u, 1.5}, {64u, 2.0},
                 {128u, 4.0}, {256u, 8.0}, {512u, 16.0} }) {
            if (helper->gainCode(gain) != code ||
                std::abs(helper->gain(code) - gain) > 1e-12) {
                std::cerr << "Wrong gain conversion: " << name << '\n';
                return 1;
            }
        }
        std::cout << "PASS " << name << ": 1x/1.5x/2x/4x/8x/16x\n";
    }
}
