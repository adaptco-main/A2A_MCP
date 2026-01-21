#include "qube/QubeRuntime.hpp"
#include <iostream>
#include <sstream>

namespace qube {

QubeRuntime::QubeRuntime() : isInitialized_(false), operationsCount_(0) {
  currentStateHash_ = "GENESIS_HASH";
}

QubeRuntime::~QubeRuntime() {
  if (isInitialized_) {
    Shutdown();
  }
}

void QubeRuntime::Initialize(const std::string &configHash) {
  if (isInitialized_)
    return;
  std::cout << "[QUBE] Initializing Runtime with Config: " << configHash
            << std::endl;
  currentStateHash_ = configHash; // Seal the initial state
  isInitialized_ = true;
}

bool QubeRuntime::Execute(const TokenPixel &pixel) {
  if (!isInitialized_) {
    std::cerr << "[QUBE] Error: Runtime not initialized." << std::endl;
    return false;
  }

  // 1. Verify Hash Anchoring (Mock)
  if (pixel.previous_hash != currentStateHash_) {
    // Enforce hash chain integrity
    // In a real implementation, this would reject the block
    std::cout << "[QUBE] Warning: Hash mismatch! Expected " << currentStateHash_
              << " got " << pixel.previous_hash << std::endl;
    // For 'fix' purposes we might proceed or fail. Let's fail to be strict.
    return false;
  }

  // 2. Process Payload (Decoder)
  // Here we would actually modify the internal state based on payload
  // For now, we just acknowledge size
  std::cout << "[QUBE] Executing Pixel " << pixel.sequence_id
            << " | Size: " << pixel.payload.size() << " bytes" << std::endl;

  // 3. Update State Hash
  UpdateHash(pixel);

  // 4. Audit Log
  operationsCount_++;
  auditLog_.push_back(currentStateHash_);

  return true;
}

std::string QubeRuntime::GetStateHash() const { return currentStateHash_; }

void QubeRuntime::Shutdown() {
  std::cout << "[QUBE] Shutting down. Total Operations: " << operationsCount_
            << std::endl;
  isInitialized_ = false;
}

void QubeRuntime::UpdateHash(const TokenPixel &pixel) {
  // Trivial Hash Function for demo: Hash(Prev + CurrentSig)
  // "Zero dependencies" -> use std::hash
  std::stringstream ss;
  ss << currentStateHash_ << pixel.sequence_id
     << pixel.current_hash; // simple chain
  std::size_t h = std::hash<std::string>{}(ss.str());
  currentStateHash_ = std::to_string(h);
}

} // namespace qube
