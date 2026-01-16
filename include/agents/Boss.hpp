#pragma once

#include "engine/Physics.hpp"

namespace agents {

class Boss {
public:
  Boss(engine::Vector2 startPos);
  void Update(float dt, const engine::Vector2 &target);

  engine::Vector2 GetPosition() const;

private:
  engine::Vector2 position_;
  int health_;
};

} // namespace agents
