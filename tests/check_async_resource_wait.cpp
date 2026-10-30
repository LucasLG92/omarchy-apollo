// Regression test against the actual hyprgraphics implementation, not a model.
// Run each mode with an external timeout: the unpatched late case never returns.
#include <hyprgraphics/resource/AsyncResourceGatherer.hpp>
#include <hyprutils/memory/Atomic.hpp>
#include <atomic>
#include <chrono>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using namespace Hyprgraphics;
using namespace Hyprutils::Memory;
using namespace std::chrono_literals;

class Probe final : public IAsyncResource {
  public:
    std::atomic<bool> release = true;
    std::atomic<unsigned> renders = 0;
    unsigned payload = 0;
    void render() override {
        while (!release.load()) std::this_thread::yield();
        payload = 42;
        ++renders;
    }
};

static void require(bool value) {
    if (!value) throw std::runtime_error("Resource completion invariant failed");
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::string mode = argv[1];
    unsigned checked = 0;
    for (unsigned iteration = 0; iteration < 128; ++iteration) {
        CAsyncResourceGatherer gatherer;
        auto probe = makeAtomicShared<Probe>();
        CAtomicSharedPointer<IAsyncResource> resource(probe);
        if (mode == "early" || mode == "multi") probe->release = false;
        gatherer.enqueue(resource);
        if (mode == "late") {
            const auto deadline = std::chrono::steady_clock::now() + 2s;
            while (!resource->m_ready.load()) {
                require(std::chrono::steady_clock::now() < deadline);
                std::this_thread::yield();
            }
            gatherer.await(resource);
        } else if (mode == "early" || mode == "multi") {
            std::vector<std::thread> waiters;
            std::atomic<unsigned> returned = 0;
            const unsigned count = mode == "multi" ? 4 : 1;
            for (unsigned n = 0; n < count; ++n)
                waiters.emplace_back([&] { gatherer.await(resource); ++returned; });
            std::this_thread::sleep_for(1ms);
            probe->release = true;
            for (auto& waiter : waiters) waiter.join();
            require(returned.load() == count);
        } else if (mode == "immediate") {
            gatherer.await(resource);
        } else return 2;
        require(resource->m_ready.load() && probe->payload == 42 && probe->renders.load() == 1);
        // Repeated waits must also observe completed resources immediately.
        gatherer.await(resource);
        ++checked;
    }
    std::cout << mode << ": " << checked << " resources completed\n";
}
