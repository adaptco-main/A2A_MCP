#pragma once

#include "WorldModel.hpp"
#include <memory>

namespace engine {

class Sandbox {
public:
  Sandbox();
  void Initialize();
  void LoadLevel(int levelId);
  void Update(float dt);
  const WorldModel &GetWorld() const;

private:
  std::unique_ptr<WorldModel> world_;
};

} // namespace engine
