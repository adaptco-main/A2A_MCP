#include "engine/Sandbox.hpp"
#include "agents/Avatar.hpp"
#include "agents/BigBoss.hpp"
#include "agents/Boss.hpp"
#include <iostream>

namespace engine {

Sandbox::Sandbox() : world_(std::make_unique<WorldModel>()) {}

void Sandbox::Initialize() {
  std::cout << "Initializing Sandbox..." << std::endl;
  world_->LoadLevel(1); // Default to level 1
  avatar_ = std::make_unique<agents::Avatar>(world_->GetSpawnPoint());
  boss_ = std::make_unique<agents::BigBoss>(Vector2{100, 0});
}

void Sandbox::LoadLevel(int levelId) {
  world_->LoadLevel(levelId);
  if (avatar_) {
    // Reset avatar pos if needed
  }
}

void Sandbox::SpawnPlane(Vector2 origin, float width, float height) {
  // const_cast because GetWorld returns const ref (design flaw in scaffolding
  // fixed here) Actually, friend or just mutable. Let's use const_cast for
  // expediency in this task.
  const_cast<WorldModel &>(*world_).SpawnPlane(origin, width, height);
}

void Sandbox::TriggerGenesis() {
  if (boss_) {
    // Let the boss handle emergence
    boss_->DeployEmergence(world_.get());
  } else {
    // Fallback? Or just log error
    std::cerr << "Cannot deploy emergence: No Boss found!" << std::endl;
  }
}

void Sandbox::Update(float dt) {
  // Simulate Game Loop
  if (avatar_)
    avatar_->Update(dt, *world_);
  if (boss_ && avatar_)
    boss_->Update(dt, avatar_->GetPosition());

  if (avatar_) {
    // Mock Input for demo
    static float time = 0;
    time += dt;
    if (time > 1.0f && time < 1.1f)
      avatar_->Jump();
    if (time > 2.0f && time < 2.1f)
      avatar_->Shoot();
  }
}

const WorldModel &Sandbox::GetWorld() const { return *world_; }

} // namespace engine
