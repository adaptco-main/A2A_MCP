#include "engine/WorldModel.hpp"
#include <iostream>

namespace engine {

WorldModel::WorldModel() {}

void WorldModel::LoadLevel(int levelId) {
  currentLevel_ = levelId;
  tiles_.clear();
  std::cout << "Generating Level " << levelId << "..." << std::endl;

  // Procedural Gen / Mocking
  // Floor
  tiles_.push_back({TileType::Platform, {{-100, 10}, {1000, 20}}});

  // Boss Room Wall
  tiles_.push_back({TileType::Platform, {{500, -100}, {520, 10}}});

  // Level Specifics
  if (levelId == 1) {
    // Simple platforms
    tiles_.push_back({TileType::Platform, {{50, 5}, {70, 6}}});
  } else if (levelId == 9) {
    // Wily Castle logic
  }

  spawnPoint_ = {0, 0};
}

bool WorldModel::IsSolid(const Vector2 &pos) const {
  // Simple point check against AABBs
  for (const auto &tile : tiles_) {
    if (tile.type == TileType::Platform) {
      if (pos.x >= tile.bounds.min.x && pos.x <= tile.bounds.max.x &&
          pos.y >= tile.bounds.min.y && pos.y <= tile.bounds.max.y) {
        return true;
      }
    }
  }
  return false;
}

const std::vector<Tile> &WorldModel::GetTiles() const { return tiles_; }

Vector2 WorldModel::GetSpawnPoint() const { return spawnPoint_; }

int WorldModel::GetCurrentLevel() const { return currentLevel_; }

} // namespace engine
