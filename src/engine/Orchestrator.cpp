#include "engine/Orchestrator.hpp"
#include <iostream>
#include <string>

namespace engine {

Orchestrator::Orchestrator()
    : sandbox_(std::make_unique<Sandbox>()), isRunning_(false) {}

void Orchestrator::Run() {
  // Initialize Sandbox
  sandbox_->Initialize();
  isRunning_ = true;

  // Command Loop
  // Expected to run as a subprocess where stdin provides commands
  std::string line;
  while (isRunning_ && std::getline(std::cin, line)) {
    // Simple 'Tick' protocol:
    // Any input results in one simulation step.
    // In reality, this would parse JSON from 'line'.

    float dt = 0.016f; // Fixed time step 60fps
    sandbox_->Update(dt);

    // Output State
    // For now, we output a simple confirmation/state JSON
    // A real implementation would serialize the World/Avatar state
    std::cout << "{\"type\": \"state_update\", \"frame_processed\": true}"
              << std::endl;
  }
}

} // namespace engine
