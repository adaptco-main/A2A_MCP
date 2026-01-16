#include "agents/BigBoss.hpp"
#include "agents/Boss.hpp"
#include <cassert>
#include <iostream>
#include <memory>


int main() {
  std::cout << "Testing Boss and BigBoss..." << std::endl;

  // Test Boss
  {
    std::cout << "Test 1: Normal Boss" << std::endl;
    agents::Boss b({0, 0});
    engine::Vector2 target{10, 0};
    b.Update(1.0f, target);
    // Boss moves 1.0f towards target
    assert(b.GetPosition().x == 1.0f);
  }

  // Test BigBoss Inheritance
  {
    std::cout << "Test 2: BigBoss Instantiation" << std::endl;
    agents::BigBoss bb({0, 0});
  }

  // Test Polymorphism
  {
    std::cout << "Test 3: Polymorphism" << std::endl;
    std::unique_ptr<agents::Boss> polyBoss =
        std::make_unique<agents::BigBoss>(engine::Vector2{0, 0});
    engine::Vector2 target{10, 0};

    // BigBoss moves at 0.5 speed initially
    polyBoss->Update(1.0f, target);
    std::cout << "BigBoss pos: " << polyBoss->GetPosition().x << std::endl;
    assert(polyBoss->GetPosition().x == 0.5f);
  }

  // Test Rage Mode
  {
    std::cout << "Test 4: Rage Mode" << std::endl;
    agents::BigBoss bb({0, 0});
    engine::Vector2 target{100, 0};

    // Simulate > 5 seconds
    // We do 55 steps of 0.1s = 5.5s
    for (int i = 0; i < 55; ++i) {
      bb.Update(0.1f, target);
    }
    // Now > 5.0, should be in rage mode (speed 2.0).
    // Measure step
    float posBefore = bb.GetPosition().x;
    bb.Update(1.0f, target);
    float posAfter = bb.GetPosition().x;
    float delta = posAfter - posBefore;

    std::cout << "Rage Speed: " << delta << std::endl;
    assert(delta == 2.0f);
  }

  std::cout << "All Boss tests passed!" << std::endl;
  return 0;
}
