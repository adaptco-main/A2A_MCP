#include "engine/Orchestrator.hpp"
#include "engine/Sandbox.hpp"
#include <cassert>
#include <iostream>

int main() {
  std::cout << "Running Engine Verification..." << std::endl;

  engine::Orchestrator orchestrator;
  // We can't easily inspect orchestrator internals without friend classes or
  // getters, but we can verify it runs without crashing.
  orchestrator.Run();

  std::cout << "Orchestrator run complete." << std::endl;

  // Test Physics / World directly
  engine::WorldModel world;
  world.LoadLevel(1);
  assert(world.GetCurrentLevel() == 1);

  std::cout << "Engine Verification Passed!" << std::endl;
  return 0;
}
