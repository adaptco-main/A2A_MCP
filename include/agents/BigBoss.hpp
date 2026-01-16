#pragma once
#include "agents/Boss.hpp"

namespace agents {

class BigBoss : public Boss {
public:
  BigBoss(engine::Vector2 startPos);
  void Update(float dt, const engine::Vector2 &target) override;

private:
  float rageTimer_;
};

} // namespace agents
